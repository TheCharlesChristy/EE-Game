"""
Routes - All API endpoints and page routes for Multi-Team Gaming System
Keeps all routes in one file for simplicity
"""

import time
import os
from pathlib import Path
from flask import Blueprint, jsonify, request, render_template, send_from_directory
from flask_socketio import emit


def init_app(app, socketio):
    """Initialize routes with Flask app and SocketIO."""
    
    # Import services
    from .data_service import data_service
    from .gpio_service import gpio_service
    from .game_service import GameService
    from .websocket_service import websocket_service
    from .TemplateBuilder import TemplateBuilder
    
    # Initialize game service
    game_service = GameService(gpio_service, websocket_service)
    
    # Initialize template builder with correct path
    template_builder = TemplateBuilder("components")
    
    # Static file route for debugging
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files from assets directory."""
        try:
            assets_path = Path(__file__).parent.parent / 'assets'
            file_path = assets_path / filename
            
            app.logger.info(f"=== STATIC FILE REQUEST ===")
            app.logger.info(f"Requested file: {filename}")
            app.logger.info(f"Assets path: {assets_path}")
            app.logger.info(f"Assets path exists: {assets_path.exists()}")
            app.logger.info(f"Full file path: {file_path}")
            app.logger.info(f"File exists: {file_path.exists()}")
            app.logger.info(f"Assets directory contents: {list(assets_path.iterdir()) if assets_path.exists() else 'Directory does not exist'}")
            
            if not assets_path.exists():
                app.logger.error(f"Assets directory does not exist: {assets_path}")
                return f"Assets directory not found: {assets_path}", 404
                
            if not file_path.exists():
                app.logger.error(f"File does not exist: {file_path}")
                return f"File not found: {filename}", 404
            
            app.logger.info(f"Serving file: {file_path}")
            return send_from_directory(str(assets_path), filename)
            
        except Exception as e:
            app.logger.error(f"Error serving static file {filename}: {str(e)}")
            app.logger.exception("Full traceback:")
            return f"Error serving static file: {str(e)}", 500
    
    # Main routes
    @app.route('/')
    def home():
        """Serve the home page."""
        try:
            app.logger.info("=== HOME PAGE REQUEST ===")
            html = template_builder.build_template('HomePage')
            app.logger.info("Home page template built successfully")
            return html
        except Exception as e:
            app.logger.error(f"Error loading home page: {str(e)}")
            app.logger.exception("Full traceback:")
            return f"Error loading home page: {str(e)}", 500
    
    @app.route('/team-management')
    def team_management():
        """Serve the team management page."""
        try:
            html = template_builder.build_template('TeamManagement')
            return html
        except Exception as e:
            return f"Error loading team management page: {str(e)}", 500
    
    # System Status API
    @app.route('/api/system/status')
    def get_system_status():
        """Get current system status."""
        try:
            team_count = data_service.get_team_count()
            config = data_service.get_config()
            
            return jsonify({
                "status": "operational" if gpio_service.is_healthy() else "error",
                "uptime_seconds": int(time.time()),  # Simple uptime
                "teams": {
                    "count": team_count,
                    "max": config.get('max_teams', 8)
                },
                "hardware": {
                    "gpio_status": "connected" if gpio_service.get_status() == "operational" else "error"
                },
                "games": {
                    game['id']: game['status'] 
                    for game in game_service.get_available_games()
                }
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/system/detailed-status')
    def get_detailed_status():
        """Get detailed system status for components."""
        try:
            return jsonify({
                'system': {'status': 'operational' if gpio_service.is_healthy() else 'error'},
                'hardware': {
                    'status': gpio_service.get_status(),
                    'gpio': gpio_service.get_pin_status(),
                    'gpio_connections': len(gpio_service.pin_config)
                },
                'teams': {'count': data_service.get_team_count()},
                'games': {
                    game['id']: game['status'] 
                    for game in game_service.get_available_games()
                },
                'connection': 'connected'
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Team Management API
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        """Get all teams."""
        try:
            teams = data_service.get_teams()
            
            # Add hardware status to each team
            gpio_status = gpio_service.get_pin_status()
            for team in teams:
                team_key = f"team_{team['id']}"
                team['status'] = gpio_status.get(team_key, {}).get('latch', 'unknown')
                
                # Add pin information
                if team['pin_set'] in gpio_service.pin_config:
                    team['pins'] = gpio_service.pin_config[team['pin_set']]
            
            return jsonify({"teams": teams})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/teams', methods=['POST'])
    def add_team():
        """Add a new team."""
        try:
            data = request.get_json()
            if not data or 'name' not in data or 'pin_set' not in data:
                return jsonify({"error": "Missing name or pin_set"}), 400
            
            team = data_service.add_team(data['name'], data['pin_set'])
            if not team:
                return jsonify({"error": "Could not add team (pin set in use or max teams reached)"}), 400
            
            # Broadcast team registration
            websocket_service.broadcast_team_registered(team)
            
            return jsonify(team), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/teams/<int:team_id>', methods=['DELETE'])
    def remove_team(team_id):
        """Remove a team."""
        try:
            if data_service.remove_team(team_id):
                # Broadcast updated team count
                websocket_service.emit_system_status()
                return '', 204
            else:
                return jsonify({"error": "Team not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Game Management API
    @app.route('/api/games/available')
    def get_available_games():
        """Get available games."""
        try:
            games = game_service.get_available_games()
            return jsonify({"games": games})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/games/<game_id>/validate', methods=['POST'])
    def validate_game(game_id):
        """Validate if a game can be started."""
        try:
            data = request.get_json()
            team_count = data.get('team_count', 0)
            
            result = game_service.validate_game_start(game_id, team_count)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/games/<game_id>/start', methods=['POST'])
    def start_game(game_id):
        """Start a game."""
        try:
            data = request.get_json() or {}
            team_ids = data.get('team_ids', [])
            
            if not team_ids:
                # Use all registered teams
                teams = data_service.get_teams()
                team_ids = [team['id'] for team in teams]
            
            if game_id == 'reaction_timer':
                result = game_service.start_reaction_timer(team_ids)
            elif game_id == 'wheel_game':
                result = game_service.start_wheel_game(team_ids)
            elif game_id == 'quiz_game':
                result = game_service.start_quiz_game(team_ids)
            else:
                return jsonify({"error": "Invalid game ID"}), 400
            
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/games/stop', methods=['POST'])
    def stop_game():
        """Stop the current game."""
        try:
            game_service.stop_current_game()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Hardware Testing API
    @app.route('/api/hardware/test/<int:team_id>', methods=['POST'])
    def test_hardware(team_id):
        """Test hardware for a specific team."""
        try:
            result = gpio_service.test_hardware(team_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/hardware/status')
    def get_hardware_status():
        """Get hardware status."""
        try:
            return jsonify({
                "status": gpio_service.get_status(),
                "gpio": gpio_service.get_pin_status(),
                "hardware_available": gpio_service.is_healthy()
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Health Check API
    @app.route('/api/health')
    def health_check():
        """Basic health check."""
        return jsonify({'status': 'healthy'}), 200
    
    @app.route('/api/health/detailed')
    def detailed_health():
        """Detailed health check."""
        try:
            checks = {
                'gpio': gpio_service.is_healthy(),
                'websocket': websocket_service.is_healthy(),
                'data': True  # Data service is always healthy if we get here
            }
            status = 'healthy' if all(checks.values()) else 'unhealthy'
            return jsonify({'status': status, 'checks': checks})
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    # WebSocket Event Handlers
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        websocket_service.connected_clients.add(request.sid)
        print(f"Client connected: {request.sid}")
        
        # Send initial system status
        websocket_service.emit_system_status()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        websocket_service.connected_clients.discard(request.sid)
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping from client."""
        emit('pong', {
            'timestamp': data.get('timestamp') if data else time.time(),
            'server_time': time.time()
        })
    
    @socketio.on('led_test_request')
    def handle_led_test(data):
        """Handle LED test request."""
        try:
            team_id = data.get('team_id')
            duration_ms = data.get('duration_ms', 1000)
            
            if team_id:
                # Test LED
                gpio_service.control_led(team_id, True)
                
                # Schedule LED off
                def turn_off_led():
                    gpio_service.control_led(team_id, False)
                
                import threading
                timer = threading.Timer(duration_ms / 1000.0, turn_off_led)
                timer.start()
                
                emit('led_test_response', {
                    'team_id': team_id,
                    'status': 'success',
                    'duration_ms': duration_ms
                })
            else:
                emit('led_test_response', {
                    'status': 'error',
                    'message': 'Team ID required'
                })
        except Exception as e:
            emit('led_test_response', {
                'status': 'error',
                'message': str(e)
            })
    
    @socketio.on('hardware_test_request')
    def handle_hardware_test(data):
        """Handle hardware test request."""
        try:
            team_id = data.get('team_id')
            if team_id:
                result = gpio_service.test_hardware(team_id)
                emit('hardware_test_response', result)
            else:
                emit('hardware_test_response', {
                    'status': 'error',
                    'message': 'Team ID required'
                })
        except Exception as e:
            emit('hardware_test_response', {
                'status': 'error',
                'message': str(e)
            })
    
    # Background task to process GPIO events
    def process_gpio_events():
        """Background task to process GPIO button press events."""
        while True:
            try:
                events = gpio_service.get_button_events()
                for event in events:
                    # Broadcast button press
                    websocket_service.broadcast_button_press(
                        event['team_id'],
                        event['timestamp']
                    )
                
                time.sleep(0.01)  # 10ms delay
            except Exception as e:
                print(f"Error processing GPIO events: {e}")
                time.sleep(1)
    
    # Start background task for GPIO event processing
    import threading
    gpio_thread = threading.Thread(target=process_gpio_events, daemon=True)
    gpio_thread.start()
    
    print("Routes initialized successfully")
