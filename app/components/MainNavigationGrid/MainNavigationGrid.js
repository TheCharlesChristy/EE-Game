/**
 * MainNavigationGrid Component
 * Provides the central game selection interface with large, accessible buttons
 * optimized for distance viewing in competitive gaming environments.
 */

class MainNavigationGrid {
    constructor() {
        this.container = document.querySelector('.main-navigation-grid');
        this.gameButtons = document.querySelectorAll('.game-button');
        this.errorMessage = document.getElementById('navigationError');
        
        // Component state
        this.systemStatus = 'unknown';
        this.teamCount = 0;
        this.availableGames = [];
        
        // WebSocket connection (will be injected by global WebSocket manager)
        this.socket = null;
        
        this.init();
    }
    
    /**
     * Initialize the component
     */
    init() {
        this.setupEventListeners();
        this.setupKeyboardNavigation();
        this.loadInitialData();
        this.connectWebSocket();
        
        // Emit component ready event
        this.emitEvent('component_ready', { component: 'MainNavigationGrid' });
    }
    
    /**
     * Setup event listeners for game button interactions
     */
    setupEventListeners() {
        this.gameButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                this.handleGameSelection(event);
            });
            
            button.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.handleGameSelection(event);
                }
            });
        });
    }
    
    /**
     * Setup keyboard navigation between game buttons
     */
    setupKeyboardNavigation() {
        this.gameButtons.forEach((button, index) => {
            button.addEventListener('keydown', (event) => {
                let targetIndex = index;
                
                switch(event.key) {
                    case 'ArrowLeft':
                        targetIndex = index > 0 ? index - 1 : this.gameButtons.length - 1;
                        break;
                    case 'ArrowRight':
                        targetIndex = index < this.gameButtons.length - 1 ? index + 1 : 0;
                        break;
                    case 'Home':
                        targetIndex = 0;
                        break;
                    case 'End':
                        targetIndex = this.gameButtons.length - 1;
                        break;
                    default:
                        return; // Don't prevent default for other keys
                }
                
                event.preventDefault();
                this.gameButtons[targetIndex].focus();
            });
        });
    }
    
    /**
     * Load initial data from APIs
     */
    async loadInitialData() {
        try {
            // Load available games
            await this.loadAvailableGames();
            
            // Load system status
            await this.loadSystemStatus();
            
            // Update UI based on loaded data
            this.updateGameButtonStates();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load game information. Please refresh the page.');
        }
    }
    
    /**
     * Load available games from API
     */
    async loadAvailableGames() {
        try {
            const response = await fetch('/api/games/available');
            if (response.ok) {
                this.availableGames = await response.json();
            } else {
                throw new Error('Failed to fetch available games');
            }
        } catch (error) {
            console.error('Error loading available games:', error);
            // Fallback to default games if API fails
            this.availableGames = [
                { id: 'reaction-timer', name: 'Reaction Timer', minTeams: 2 },
                { id: 'wheel-game', name: 'Wheel Game', minTeams: 2 },
                { id: 'quiz-game', name: 'Quiz Game', minTeams: 2 }
            ];
        }
    }
    
    /**
     * Load system status from API
     */
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system/status');
            if (response.ok) {
                const statusData = await response.json();
                this.systemStatus = statusData.status;
                this.teamCount = statusData.teamCount || 0;
            } else {
                throw new Error('Failed to fetch system status');
            }
        } catch (error) {
            console.error('Error loading system status:', error);
            this.systemStatus = 'error';
        }
    }
    
    /**
     * Connect to WebSocket for real-time updates
     */
    connectWebSocket() {
        // Check if global WebSocket manager exists
        if (window.GameWebSocket) {
            this.socket = window.GameWebSocket;
            this.setupWebSocketListeners();
        } else {
            // Fallback: create basic WebSocket connection
            try {
                this.socket = io();
                this.setupWebSocketListeners();
            } catch (error) {
                console.warn('WebSocket connection failed:', error);
            }
        }
    }
    
    /**
     * Setup WebSocket event listeners
     */
    setupWebSocketListeners() {
        if (!this.socket) return;
        
        // Listen for system status updates
        this.socket.on('system_status_update', (data) => {
            this.systemStatus = data.status;
            this.updateGameButtonStates();
        });
        
        // Listen for team count changes
        this.socket.on('team_count_changed', (data) => {
            this.teamCount = data.count;
            this.updateGameButtonStates();
        });
        
        // Listen for hardware status changes
        this.socket.on('hardware_status_changed', (data) => {
            this.updateGameButtonStates();
        });
    }
    
    /**
     * Handle game selection click/keyboard activation
     */
    async handleGameSelection(event) {
        const button = event.currentTarget;
        const gameId = button.dataset.game;
        const gameStatus = button.dataset.status;
        
        // Prevent action if game is unavailable
        if (gameStatus === 'unavailable') {
            this.showError('This game is currently unavailable. Please check system status.');
            return;
        }
        
        // Check team requirements
        const game = this.availableGames.find(g => g.id === gameId);
        if (game && this.teamCount < game.minTeams) {
            this.showError(`This game requires at least ${game.minTeams} teams. Please register more teams.`);
            button.dataset.status = 'requires-teams';
            this.updateGameButtonStatus(button);
            return;
        }
        
        try {
            // Show loading state
            button.classList.add('loading');
            this.hideError();
            
            // Emit game selection event
            this.emitEvent('game_selected', { 
                gameId: gameId, 
                timestamp: Date.now(),
                teamCount: this.teamCount 
            });
            
            // Validate game can start
            const canStart = await this.validateGameStart(gameId);
            if (!canStart) {
                throw new Error('Game validation failed');
            }
            
            // Navigate to game page
            this.navigateToGame(gameId);
            
        } catch (error) {
            console.error('Game selection failed:', error);
            this.showError('Unable to start game. Please check system status and try again.');
        } finally {
            // Remove loading state
            button.classList.remove('loading');
        }
    }
    
    /**
     * Validate that a game can start
     */
    async validateGameStart(gameId) {
        try {
            const response = await fetch(`/api/games/${gameId}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    teamCount: this.teamCount,
                    systemStatus: this.systemStatus
                })
            });
            
            return response.ok;
        } catch (error) {
            console.error('Game validation failed:', error);
            return false;
        }
    }
    
    /**
     * Navigate to the selected game page
     */
    navigateToGame(gameId) {
        // Use History API for smooth navigation
        const gameUrl = `/games/${gameId}`;
        
        if (window.history && window.history.pushState) {
            window.history.pushState({ gameId }, '', gameUrl);
            
            // Emit navigation event for router to handle
            this.emitEvent('navigate', { url: gameUrl, gameId });
        } else {
            // Fallback to direct navigation
            window.location.href = gameUrl;
        }
    }
    
    /**
     * Update game button states based on current system status
     */
    updateGameButtonStates() {
        this.gameButtons.forEach(button => {
            this.updateGameButtonStatus(button);
        });
    }
    
    /**
     * Update individual game button status
     */
    updateGameButtonStatus(button) {
        const gameId = button.dataset.game;
        const game = this.availableGames.find(g => g.id === gameId);
        const statusElement = button.querySelector('.game-status');
        
        // Determine button state
        let status = 'available';
        let statusText = 'Ready to Play';
        
        if (this.systemStatus === 'error') {
            status = 'unavailable';
            statusText = 'System Error';
        } else if (game && this.teamCount < game.minTeams) {
            status = 'requires-teams';
            statusText = `Needs ${game.minTeams} Teams`;
        } else if (this.systemStatus === 'warning') {
            status = 'available';
            statusText = 'Ready (Check Status)';
        }
        
        // Update button attributes and content
        button.dataset.status = status;
        if (statusElement) {
            statusElement.textContent = statusText;
            statusElement.dataset.status = status;
        }
        
        // Update accessibility attributes
        button.setAttribute('aria-disabled', status === 'unavailable');
        if (status === 'unavailable') {
            button.setAttribute('aria-describedby', 'navigationError');
        } else {
            button.removeAttribute('aria-describedby');
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        if (this.errorMessage) {
            this.errorMessage.querySelector('p').textContent = message;
            this.errorMessage.style.display = 'block';
            
            // Announce to screen readers
            this.errorMessage.setAttribute('aria-live', 'assertive');
            setTimeout(() => {
                this.errorMessage.setAttribute('aria-live', 'polite');
            }, 1000);
        }
    }
    
    /**
     * Hide error message
     */
    hideError() {
        if (this.errorMessage) {
            this.errorMessage.style.display = 'none';
        }
    }
    
    /**
     * Emit custom events for component communication
     */
    emitEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, {
            detail: { ...data, source: 'MainNavigationGrid' },
            bubbles: true
        });
        
        if (this.container) {
            this.container.dispatchEvent(event);
        } else {
            document.dispatchEvent(event);
        }
    }
    
    /**
     * Public method to update team count (called by other components)
     */
    updateTeamCount(count) {
        this.teamCount = count;
        this.updateGameButtonStates();
    }
    
    /**
     * Public method to update system status (called by other components)
     */
    updateSystemStatus(status) {
        this.systemStatus = status;
        this.updateGameButtonStates();
    }
    
    /**
     * Cleanup method for component destruction
     */
    destroy() {
        // Remove event listeners
        this.gameButtons.forEach(button => {
            button.replaceWith(button.cloneNode(true));
        });
        
        // Disconnect WebSocket listeners
        if (this.socket) {
            this.socket.off('system_status_update');
            this.socket.off('team_count_changed');
            this.socket.off('hardware_status_changed');
        }
        
        // Emit cleanup event
        this.emitEvent('component_destroyed', { component: 'MainNavigationGrid' });
    }
}

// Initialize component when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if component container exists
    if (document.querySelector('.main-navigation-grid')) {
        window.MainNavigationGrid = new MainNavigationGrid();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MainNavigationGrid;
}
