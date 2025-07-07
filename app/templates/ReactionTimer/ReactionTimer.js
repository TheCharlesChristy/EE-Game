const domain = window.location.hostname;
const port = window.location.port || '5000';

// Initialize SocketIO connection
const socket = io(domain + ":" + port, {
    transports: ['websocket', 'polling'],
    timeout: 20000
});

// Make socket globally available for components
window.socket = socket;

// Initialize components
let teamStatusDisplay;
let reactionScreen;
let gameControls;

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing ReactionTimer components...');
    
    // Components will auto-initialize themselves
    // We just store references for easy access
    setTimeout(() => {
        teamStatusDisplay = window.teamStatusDisplay;
        reactionScreen = window.reactionScreen;
        gameControls = window.gameControls;
        
        console.log('Components initialized:', {
            teamStatusDisplay: !!teamStatusDisplay,
            reactionScreen: !!reactionScreen,
            gameControls: !!gameControls
        });
    }, 100);
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
    
    // Update UI to show disconnected state
    document.dispatchEvent(new CustomEvent('socketio_disconnected', {
        detail: { status: 'disconnected' }
    }));
});

socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
    
    // Update UI to show connection error
    document.dispatchEvent(new CustomEvent('socketio_error', {
        detail: { error: error.toString() }
    }));
});

socket.on('connection_status', function(data) {
    console.log('Connection status:', data);
});