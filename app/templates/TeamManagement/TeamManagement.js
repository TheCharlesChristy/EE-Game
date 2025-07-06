const domain = window.location.hostname;
const port = window.location.port || '5000';

// Initialize SocketIO connection
const socket = io(domain + ":" + port, {
    transports: ['websocket', 'polling'],
    timeout: 20000
});

// Connection event handlers
socket.on('connect', function() {
    console.log('Connected to server');

    // Emit a event to notify the web page that the connection is established
    document.dispatchEvent(new CustomEvent('socketio_connected', {
        detail: { status: 'connected' }
    }));
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