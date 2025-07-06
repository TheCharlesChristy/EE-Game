/**
 * Reaction Game Template Controller
 * Coordinates all components and manages the reaction timer game state
 */

class ReactionGameController {
    constructor() {
        this.socketManager = null;
        this.components = {};
        this.gameState = {
            isActive: false,
            currentRound: 0,
            totalRounds: 20,
            activeTeams: [],
            gamePhase: 'waiting' // waiting, preparing, active, complete
        };
        
        this.init();
    }

    init() {
        console.log('Initializing Reaction Game Controller');
        
        // Initialize WebSocket connection
        this.initializeWebSocket();
        
        // Initialize all components
        this.initializeComponents();
        
        // Set up template-level event handlers
        this.setupEventHandlers();
        
        // Request initial system status
        this.requestInitialStatus();
        
        console.log('Reaction Game Controller initialized');
    }

    initializeWebSocket() {
        // Initialize WebSocket manager if not already available
        if (!window.socketManager) {
            // Basic WebSocket manager (simplified for this MVP)
            window.socketManager = {
                socket: null,
                events: new Map(),
                
                init: function() {
                    this.socket = io();
                    this.setupSocketEvents();
                },
                
                setupSocketEvents: function() {
                    this.socket.on('connect', () => {
                        console.log('Connected to server');
                    });
                    
                    this.socket.on('disconnect', () => {
                        console.log('Disconnected from server');
                    });
                    
                    // Generic event handler
                    this.socket.onAny((eventName, data) => {
                        if (this.events.has(eventName)) {
                            this.events.get(eventName).forEach(callback => {
                                try {
                                    callback(data);
                                } catch (error) {
                                    console.error(`Error in ${eventName} handler:`, error);
                                }
                            });
                        }
                    });
                },
                
                on: function(event, callback) {
                    if (!this.events.has(event)) {
                        this.events.set(event, []);
                    }
                    this.events.get(event).push(callback);
                },
                
                off: function(event, callback) {
                    if (this.events.has(event)) {
                        const handlers = this.events.get(event);
                        const index = handlers.indexOf(callback);
                        if (index > -1) {
                            handlers.splice(index, 1);
                        }
                    }
                },
                
                emit: function(event, data) {
                    if (this.socket) {
                        this.socket.emit(event, data);
                    }
                }
            };
            
            window.socketManager.init();
        }
        
        this.socketManager = window.socketManager;
    }

    initializeComponents() {
        try {
            // Initialize all components
            this.components.reactionScreen = new ReactionScreen();
            this.components.teamStatusDisplay = new TeamStatusDisplay();
            this.components.gameControlPanel = new GameControlPanel();
            this.components.roundProgressIndicator = new RoundProgressIndicator();
            this.components.resultsDisplay = new ResultsDisplay();
            this.components.ledStatusIndicator = new LEDStatusIndicator();
            
            // Make LED status indicator globally available
            window.ledStatusIndicator = this.components.ledStatusIndicator;
            
            console.log('All components initialized successfully');
        } catch (error) {
            console.error('Error initializing components:', error);
        }
    }

    setupEventHandlers() {
        // Template-level WebSocket event handlers
        if (this.socketManager) {
            // Game state management events
            this.socketManager.on('game_started', (data) => {
                this.handleGameStarted(data);
            });
            
            this.socketManager.on('game_ended', (data) => {
                this.handleGameEnded(data);
            });
            
            this.socketManager.on('round_started', (data) => {
                this.handleRoundStarted(data);
            });
            
            this.socketManager.on('round_complete', (data) => {
                this.handleRoundComplete(data);
            });
            
            this.socketManager.on('winner_announced', (data) => {
                this.handleWinnerAnnounced(data);
            });
            
            // Navigation events
            this.socketManager.on('navigate_to_menu', () => {
                this.handleNavigateToMenu();
            });
            
            // Error handling
            this.socketManager.on('error_occurred', (data) => {
                this.handleError(data);
            });
        }
        
        // Keyboard shortcuts for quick actions
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });
        
        // Window events
        window.addEventListener('beforeunload', (e) => {
            this.handleBeforeUnload(e);
        });
        
        // Visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
    }

    requestInitialStatus() {
        if (this.socketManager) {
            // Request current system status
            this.socketManager.emit('request_status');
            
            // Request team data
            this.socketManager.emit('request_team_status');
            
            // Request hardware status
            this.socketManager.emit('request_hardware_status');
            
            // Request LED status
            this.socketManager.emit('request_led_status');
        }
    }

    // Game Event Handlers
    handleGameStarted(data) {
        console.log('Game started:', data);
        
        this.gameState.isActive = true;
        this.gameState.currentRound = 0;
        this.gameState.activeTeams = data.teams || [];
        this.gameState.gamePhase = 'preparing';
        
        // Update layout state
        this.updateLayoutState('game-active');
        
        // Hide results if showing
        if (this.components.resultsDisplay) {
            this.components.resultsDisplay.hide();
        }
        
        // Show reaction screen
        if (this.components.reactionScreen) {
            this.components.reactionScreen.setWaiting();
        }
    }

    handleGameEnded(data) {
        console.log('Game ended:', data);
        
        this.gameState.isActive = false;
        this.gameState.gamePhase = 'complete';
        
        // Update layout state
        this.updateLayoutState('game-complete');
        
        // Show final results
        if (this.components.resultsDisplay && data.final_results) {
            this.components.resultsDisplay.showResults('game', data.final_results);
        }
    }

    handleRoundStarted(data) {
        console.log('Round started:', data);
        
        this.gameState.currentRound = data.round || this.gameState.currentRound + 1;
        this.gameState.gamePhase = 'preparing';
        
        // Update reaction screen
        if (this.components.reactionScreen) {
            this.components.reactionScreen.setRed();
        }
    }

    handleRoundComplete(data) {
        console.log('Round complete:', data);
        
        this.gameState.gamePhase = 'complete';
        
        // Show round results
        if (this.components.resultsDisplay) {
            this.components.resultsDisplay.showResults('round', data);
            this.updateLayoutState('results-showing');
        }
    }

    handleWinnerAnnounced(data) {
        console.log('Winner announced:', data);
        
        // Show winner announcement
        if (this.components.resultsDisplay) {
            this.components.resultsDisplay.showResults('winner', data);
            this.updateLayoutState('winner-mode');
        }
    }

    handleNavigateToMenu() {
        console.log('Navigating to menu');
        
        // Clean up current game state
        this.cleanup();
        
        // Navigate to main menu (this would typically be handled by a router)
        window.location.href = '/';
    }

    handleError(data) {
        console.error('Game error:', data);
        
        // Show error message (could be enhanced with a toast notification system)
        alert(`Game Error: ${data.message || 'An unknown error occurred'}`);
    }

    // Utility Event Handlers
    handleGlobalKeyboard(event) {
        // Only handle global shortcuts if not typing in an input
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch (event.key.toLowerCase()) {
            case 'f':
                // Toggle fullscreen mode
                event.preventDefault();
                this.toggleFullscreenMode();
                break;
                
            case 'p':
                // Quick pause/resume (if implemented)
                event.preventDefault();
                break;
        }
    }

    handleBeforeUnload(event) {
        if (this.gameState.isActive) {
            event.preventDefault();
            event.returnValue = 'A game is currently in progress. Are you sure you want to leave?';
            return event.returnValue;
        }
    }

    handleVisibilityChange() {
        if (document.hidden && this.gameState.isActive) {
            console.log('Tab became hidden during active game');
            // Could pause game or show warning
        } else if (!document.hidden && this.gameState.isActive) {
            console.log('Tab became visible during active game');
            // Could resume game or refresh state
        }
    }

    // Layout Management
    updateLayoutState(state) {
        const layout = document.querySelector('.reaction-game-layout');
        if (layout) {
            // Remove all state classes
            layout.classList.remove(
                'reaction-game-layout--game-active',
                'reaction-game-layout--results-showing',
                'reaction-game-layout--winner-mode',
                'reaction-game-layout--fullscreen-mode'
            );
            
            // Add new state class
            if (state) {
                layout.classList.add(`reaction-game-layout--${state}`);
            }
        }
    }

    toggleFullscreenMode() {
        const layout = document.querySelector('.reaction-game-layout');
        if (layout) {
            layout.classList.toggle('reaction-game-layout--fullscreen-mode');
        }
    }

    // Game Control Methods
    startNewGame() {
        if (this.socketManager) {
            this.socketManager.emit('start_game', {
                game_type: 'reaction_timer',
                timestamp: Date.now()
            });
        }
    }

    stopCurrentGame() {
        if (this.socketManager) {
            this.socketManager.emit('stop_game', {
                timestamp: Date.now()
            });
        }
    }

    resetGame() {
        if (this.socketManager) {
            this.socketManager.emit('reset_game', {
                timestamp: Date.now()
            });
        }
    }

    // Cleanup
    cleanup() {
        console.log('Cleaning up Reaction Game Controller');
        
        // Destroy all components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.destroy === 'function') {
                component.destroy();
            }
        });
        
        // Clear components
        this.components = {};
        
        // Reset game state
        this.gameState = {
            isActive: false,
            currentRound: 0,
            totalRounds: 20,
            activeTeams: [],
            gamePhase: 'waiting'
        };
        
        // Clean up global references
        if (window.ledStatusIndicator) {
            delete window.ledStatusIndicator;
        }
    }

    // Public API
    getGameState() {
        return { ...this.gameState };
    }

    getComponents() {
        return { ...this.components };
    }

    isGameActive() {
        return this.gameState.isActive;
    }
}

// Initialize the reaction game controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.reactionGameController = new ReactionGameController();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.reactionGameController) {
        window.reactionGameController.cleanup();
    }
});
