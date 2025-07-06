"""
WebSocket Service - Real-time Communication for Multi-Team Gaming System
Handles all WebSocket events and broadcasting
"""

import time
import threading
from flask_socketio import emit
from flask import request


class WebSocketService:
    """Simple WebSocket service for real-time communication."""
    
    def __init__(self):
        self.socketio = None
        self.connected_clients = set()
        self.broadcast_thread = None
        self.running = False
    
    def init_socketio(self, socketio):
        """Initialize with SocketIO instance."""
        self.socketio = socketio
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            client_id = request.sid if request else 'test_client'
            self.connected_clients.add(client_id)
            print(f"Client connected. Total clients: {len(self.connected_clients)}")
            
            # Send initial system status
            self.emit_system_status()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid if request else 'test_client'
            self.connected_clients.discard(client_id)
            print(f"Client disconnected. Total clients: {len(self.connected_clients)}")
        
        @self.socketio.on('ping')
        def handle_ping(data):
            """Handle ping from client."""
            emit('pong', {'timestamp': data.get('timestamp'), 'server_time': time.time()})
        
        # Reaction Timer Game Events
        @self.socketio.on('start_game')
        def handle_start_game(data):
            """Handle start game request."""
            from .game_service import game_service
            from .data_service import data_service
            
            # Get active teams
            teams = data_service.get_teams()
            if not teams:
                emit('error_occurred', {
                    'message': 'No teams registered. Please register teams before starting the game.'
                })
                return
            
            team_ids = [team['id'] for team in teams]
            result = game_service.start_reaction_timer(team_ids)
            
            if result['status'] == 'success':
                emit('game_started', {
                    'game_type': 'reaction_timer',
                    'teams': team_ids,
                    'start_time': time.time()
                })
            else:
                emit('error_occurred', result)
        
        @self.socketio.on('stop_game')
        def handle_stop_game(data):
            """Handle stop game request."""
            from .game_service import game_service
            
            result = game_service.stop_current_game()
            emit('game_state_change', {'state': 'stopped'})
        
        @self.socketio.on('reset_game')
        def handle_reset_game(data):
            """Handle reset game request."""
            from .game_service import game_service
            
            result = game_service.reset_game()
            emit('game_state_change', {'state': 'waiting'})
        
        @self.socketio.on('abort_game')
        def handle_abort_game(data):
            """Handle emergency abort request."""
            from .game_service import game_service
            
            result = game_service.abort_game()
            emit('game_state_change', {'state': 'aborted'})
        
        @self.socketio.on('navigate_to_menu')
        def handle_navigate_to_menu(data):
            """Handle navigation to main menu."""
            emit('navigate_to_menu')
        
        @self.socketio.on('request_status')
        def handle_request_status(data):
            """Handle status request."""
            self.emit_system_status()
        
        @self.socketio.on('request_team_status')
        def handle_request_team_status(data):
            """Handle team status request."""
            from .data_service import data_service
            
            teams = data_service.get_teams()
            emit('team_status_update', {'teams': teams})
        
        @self.socketio.on('request_hardware_status')
        def handle_request_hardware_status(data):
            """Handle hardware status request."""
            self.broadcast_hardware_status()
        
        @self.socketio.on('request_led_status')
        def handle_request_led_status(data):
            """Handle LED status request."""
            from .gpio_service import gpio_service
            
            led_statuses = []
            for team_id in range(1, 9):  # Support up to 8 teams
                status = gpio_service.get_led_status(team_id)
                if status:
                    led_statuses.append({
                        'team_id': team_id,
                        'led_status': status['state'],
                        'gpio_pin': status.get('pin'),
                        'connection_status': status.get('connection', 'unknown')
                    })
            
            emit('led_status_update', {'teams': led_statuses})
        
        @self.socketio.on('test_all_leds')
        def handle_test_all_leds(data):
            """Handle test all LEDs request."""
            from .gpio_service import gpio_service
            
            duration_ms = data.get('duration_ms', 1000)
            result = gpio_service.test_all_leds(duration_ms)
            
            emit('led_test_response', {
                'status': 'success' if result else 'error',
                'duration_ms': duration_ms,
                'message': 'All LEDs tested' if result else 'LED test failed'
            })
        
        @self.socketio.on('reset_all_leds')
        def handle_reset_all_leds(data):
            """Handle reset all LEDs request."""
            from .gpio_service import gpio_service
            
            result = gpio_service.reset_all_leds()
            emit('led_status_update', {
                'status': 'all_reset',
                'success': result
            })
    
    def emit_system_status(self):
        """Emit current system status to all clients."""
        from .data_service import data_service
        from .gpio_service import gpio_service
        
        status_data = {
            'system': {'status': 'operational'},
            'hardware': {
                'status': gpio_service.get_status(),
                'gpio_connections': len(gpio_service.pin_config)
            },
            'teams': {'count': data_service.get_team_count()},
            'connection': 'connected',
            'timestamp': time.time()
        }
        
        self.socketio.emit('system_status_update', status_data)
    
    def broadcast_team_registered(self, team_data):
        """Broadcast when a new team is registered."""
        from .data_service import data_service
        
        self.socketio.emit('team_registered', {
            'team': team_data,
            'team_count': data_service.get_team_count()
        })
    
    def broadcast_hardware_status(self):
        """Broadcast hardware status update."""
        from .gpio_service import gpio_service
        
        self.socketio.emit('hardware_status_update', {
            'status': gpio_service.get_status(),
            'gpio': gpio_service.get_pin_status()
        })
    
    def broadcast_button_press(self, team_id, timestamp, reaction_time_ms=None, valid=True):
        """Broadcast button press event."""
        self.socketio.emit('button_press', {
            'team_id': team_id,
            'timestamp': timestamp,
            'reaction_time_ms': reaction_time_ms,
            'valid': valid
        })
    
    def broadcast_game_started(self, game_id, team_ids):
        """Broadcast game start event."""
        self.socketio.emit('game_started', {
            'game_id': game_id,
            'teams': team_ids,
            'start_time': time.time()
        })
    
    def broadcast_round_started(self, round_num, time_limit_ms, active_teams):
        """Broadcast round start event."""
        self.socketio.emit('round_started', {
            'round': round_num,
            'time_limit_ms': time_limit_ms,
            'active_teams': active_teams
        })
    
    def broadcast_game_ended(self, winner_data, final_standings):
        """Broadcast game end event."""
        self.socketio.emit('game_ended', {
            'winner': winner_data,
            'final_standings': final_standings
        })
    
    def is_healthy(self):
        """Health check for WebSocket service."""
        return self.socketio is not None


# Global service instance
websocket_service = WebSocketService()
