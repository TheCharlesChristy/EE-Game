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
        
        @self.socketio.on('led_test_request')
        def handle_led_test(data):
            """Handle LED test request."""
            from .gpio_service import gpio_service
            team_id = data.get('team_id')
            duration_ms = data.get('duration_ms', 1000)
            
            if team_id:
                # Test LED
                gpio_service.control_led(team_id, True)
                threading.Timer(duration_ms / 1000, 
                               lambda: gpio_service.control_led(team_id, False)).start()
                
                emit('led_test_response', {
                    'team_id': team_id,
                    'status': 'success',
                    'duration_ms': duration_ms
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
