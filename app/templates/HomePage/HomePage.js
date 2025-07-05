/**
 * HomePage JavaScript - Multi-Team Gaming System
 * Handles home page interactions, component communication, and WebSocket events
 */

class HomePage {
    constructor() {
        this.socket = null;
        this.systemStatus = {
            hardware: 'unknown',
            teams: 0,
            connection: 'disconnected'
        };
        this.components = {};
        
        this.init();
    }
    
    /**
     * Initialize the home page
     */
    init() {
        this.setupWebSocket();
        this.bindEvents();
        this.initializeComponents();
        this.setupKeyboardNavigation();
        this.checkSystemHealth();
        
        console.log('HomePage initialized');
    }
    
    /**
     * Setup WebSocket connection for real-time updates
     */
    setupWebSocket() {
        try {
            // Initialize WebSocket connection (adjust URL as needed)
            this.socket = io('/home', {
                transports: ['websocket', 'polling'],
                timeout: 5000
            });
            
            // Connection event handlers
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.systemStatus.connection = 'connected';
                this.updateConnectionStatus();
                this.requestSystemStatus();
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.systemStatus.connection = 'disconnected';
                this.updateConnectionStatus();
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.systemStatus.connection = 'error';
                this.updateConnectionStatus();
            });
            
            // System status events
            this.socket.on('system_status_update', (data) => {
                this.handleSystemStatusUpdate(data);
            });
            
            this.socket.on('hardware_status', (data) => {
                this.handleHardwareStatus(data);
            });
            
            this.socket.on('team_registered', (data) => {
                this.handleTeamRegistered(data);
            });
            
            this.socket.on('team_removed', (data) => {
                this.handleTeamRemoved(data);
            });
            
            this.socket.on('system_alert', (data) => {
                this.handleSystemAlert(data);
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.systemStatus.connection = 'error';
            this.updateConnectionStatus();
        }
    }
    
    /**
     * Bind global event handlers
     */
    bindEvents() {
        // Handle navigation events from components
        document.addEventListener('game_selected', (event) => {
            this.handleGameSelection(event.detail);
        });
        
        document.addEventListener('team_management_requested', (event) => {
            this.handleTeamManagementRequest();
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.socket) {
                this.requestSystemStatus();
            }
        });
        
        // Handle window focus
        window.addEventListener('focus', () => {
            if (this.socket) {
                this.requestSystemStatus();
            }
        });
        
        // Error handling for unhandled errors
        window.addEventListener('error', (event) => {
            console.error('HomePage error:', event.error);
            this.showErrorMessage('An unexpected error occurred. Please refresh the page.');
        });
    }
    
    /**
     * Initialize component references and communication
     */
    initializeComponents() {
        // Store references to component elements
        this.components.navigationGrid = document.querySelector('.main-navigation-grid');
        this.components.statusIndicator = document.querySelector('.system-status-indicator');
        this.components.teamButton = document.querySelector('.team-management-button');
        this.components.pageHeader = document.querySelector('.page-header');
        
        // Initialize component states
        this.updateAllComponents();
    }
    
    /**
     * Setup keyboard navigation for accessibility
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            switch (event.key) {
                case 'Escape':
                    // Clear any active selections or modals
                    this.clearActiveStates();
                    break;
                    
                case 'F5':
                    // Refresh system status
                    event.preventDefault();
                    this.requestSystemStatus();
                    break;
                    
                case '1':
                case '2':
                case '3':
                    // Quick game selection via number keys
                    if (event.ctrlKey) {
                        event.preventDefault();
                        this.quickGameSelection(parseInt(event.key));
                    }
                    break;
                    
                case 't':
                case 'T':
                    // Quick team management access
                    if (event.ctrlKey) {
                        event.preventDefault();
                        this.handleTeamManagementRequest();
                    }
                    break;
            }
        });
    }
    
    /**
     * Check initial system health
     */
    checkSystemHealth() {
        if (this.socket && this.socket.connected) {
            this.requestSystemStatus();
        } else {
            // Show offline status
            this.systemStatus.connection = 'disconnected';
            this.updateConnectionStatus();
        }
    }
    
    /**
     * Request current system status from server
     */
    requestSystemStatus() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('request_system_status');
            this.socket.emit('request_hardware_status');
            this.socket.emit('request_team_count');
        }
    }
    
    /**
     * Handle system status updates
     */
    handleSystemStatusUpdate(data) {
        console.log('System status update:', data);
        
        Object.assign(this.systemStatus, data);
        this.updateAllComponents();
        
        // Dispatch custom event for components
        document.dispatchEvent(new CustomEvent('system_status_changed', {
            detail: this.systemStatus
        }));
    }
    
    /**
     * Handle hardware status updates
     */
    handleHardwareStatus(data) {
        console.log('Hardware status update:', data);
        
        this.systemStatus.hardware = data.status;
        this.systemStatus.gpio_status = data.gpio_status;
        
        this.updateAllComponents();
        
        // Show alerts for hardware issues
        if (data.status === 'error') {
            this.showErrorMessage('Hardware error detected. Some games may be unavailable.');
        }
    }
    
    /**
     * Handle team registration events
     */
    handleTeamRegistered(data) {
        console.log('Team registered:', data);
        
        this.systemStatus.teams = data.team_count;
        this.updateAllComponents();
        
        this.showSuccessMessage(`Team ${data.team_name} registered successfully!`);
    }
    
    /**
     * Handle team removal events
     */
    handleTeamRemoved(data) {
        console.log('Team removed:', data);
        
        this.systemStatus.teams = data.team_count;
        this.updateAllComponents();
        
        this.showInfoMessage(`Team removed. Current teams: ${data.team_count}`);
    }
    
    /**
     * Handle system alerts
     */
    handleSystemAlert(data) {
        console.log('System alert:', data);
        
        switch (data.level) {
            case 'error':
                this.showErrorMessage(data.message);
                break;
            case 'warning':
                this.showWarningMessage(data.message);
                break;
            case 'info':
                this.showInfoMessage(data.message);
                break;
            case 'success':
                this.showSuccessMessage(data.message);
                break;
            default:
                this.showInfoMessage(data.message);
        }
    }
    
    /**
     * Handle game selection
     */
    handleGameSelection(gameData) {
        console.log('Game selected:', gameData);
        
        // Validate system readiness
        if (!this.validateGameStart(gameData.gameType)) {
            return;
        }
        
        // Show loading state
        this.setLoadingState(true);
        
        // Emit game start request
        if (this.socket && this.socket.connected) {
            this.socket.emit('start_game', {
                game_type: gameData.gameType,
                timestamp: Date.now()
            });
        } else {
            this.showErrorMessage('Cannot start game: No connection to server');
            this.setLoadingState(false);
        }
        
        // Navigate to game page (implement based on routing system)
        setTimeout(() => {
            this.navigateToGame(gameData.gameType);
        }, 1000);
    }
    
    /**
     * Handle team management request
     */
    handleTeamManagementRequest() {
        console.log('Team management requested');
        
        // Navigate to team management page
        this.navigateToTeamManagement();
    }
    
    /**
     * Validate if game can start
     */
    validateGameStart(gameType) {
        // Check system connection
        if (this.systemStatus.connection !== 'connected') {
            this.showErrorMessage('Cannot start game: Not connected to server');
            return false;
        }
        
        // Check hardware status
        if (this.systemStatus.hardware === 'error') {
            this.showErrorMessage('Cannot start game: Hardware error detected');
            return false;
        }
        
        // Check minimum team requirement
        if (this.systemStatus.teams < 2) {
            this.showErrorMessage('Cannot start game: At least 2 teams required');
            return false;
        }
        
        return true;
    }
    
    /**
     * Navigate to game page
     */
    navigateToGame(gameType) {
        // Implement navigation based on your routing system
        // This is a placeholder - adjust based on actual implementation
        const gameUrls = {
            'reaction-timer': '/reaction-timer',
            'wheel-game': '/wheel-game',
            'quiz-game': '/quiz-game'
        };
        
        const url = gameUrls[gameType];
        if (url) {
            window.location.href = url;
        } else {
            this.showErrorMessage('Invalid game type selected');
            this.setLoadingState(false);
        }
    }
    
    /**
     * Navigate to team management
     */
    navigateToTeamManagement() {
        // Implement navigation to team management page
        window.location.href = '/team-management';
    }
    
    /**
     * Quick game selection via keyboard
     */
    quickGameSelection(gameNumber) {
        const gameTypes = ['reaction-timer', 'wheel-game', 'quiz-game'];
        const gameType = gameTypes[gameNumber - 1];
        
        if (gameType) {
            this.handleGameSelection({ gameType });
        }
    }
    
    /**
     * Update all components with current system status
     */
    updateAllComponents() {
        this.updateConnectionStatus();
        
        // Dispatch events for component updates
        document.dispatchEvent(new CustomEvent('homepage_status_update', {
            detail: this.systemStatus
        }));
    }
    
    /**
     * Update connection status display
     */
    updateConnectionStatus() {
        const statusClass = `connection-${this.systemStatus.connection}`;
        document.body.classList.remove('connection-connected', 'connection-disconnected', 'connection-error');
        document.body.classList.add(statusClass);
    }
    
    /**
     * Set loading state for the page
     */
    setLoadingState(loading) {
        if (loading) {
            document.body.classList.add('loading');
        } else {
            document.body.classList.remove('loading');
        }
    }
    
    /**
     * Clear any active states
     */
    clearActiveStates() {
        // Remove any active selections or highlights
        document.querySelectorAll('.active, .selected, .highlighted').forEach(el => {
            el.classList.remove('active', 'selected', 'highlighted');
        });
    }
    
    /**
     * Show success message
     */
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }
    
    /**
     * Show error message
     */
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }
    
    /**
     * Show warning message
     */
    showWarningMessage(message) {
        this.showMessage(message, 'warning');
    }
    
    /**
     * Show info message
     */
    showInfoMessage(message) {
        this.showMessage(message, 'info');
    }
    
    /**
     * Show message with specified type
     */
    showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message-toast');
        existingMessages.forEach(msg => msg.remove());
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `message-toast message-${type}`;
        messageEl.textContent = message;
        messageEl.setAttribute('role', 'alert');
        messageEl.setAttribute('aria-live', 'polite');
        
        // Add to page
        document.body.appendChild(messageEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 5000);
        
        // Allow manual dismissal
        messageEl.addEventListener('click', () => {
            messageEl.remove();
        });
    }
    
    /**
     * Cleanup method for page unload
     */
    cleanup() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize HomePage when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.homePage = new HomePage();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.homePage) {
        window.homePage.cleanup();
    }
});

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HomePage;
}