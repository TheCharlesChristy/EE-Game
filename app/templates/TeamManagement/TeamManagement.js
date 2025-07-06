// Initialize SocketIO connection
const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    timeout: 20000
});

// Connection event handlers
socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});

socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
});

socket.on('connection_status', function(data) {
    console.log('Connection status:', data);
});