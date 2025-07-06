class GameControlPanel {
    constructor() {
        this.element = null;
        this.statusIndicator = null;
        this.statusText = null;
        this.startBtn = null;
        this.stopBtn = null;
        this.resetBtn = null;
        this.abortBtn = null;
        this.navigationBtn = null;
        this.gameState = 'waiting'; // waiting, active, paused, stopped
        this.init();
    }

    init() {
        this.element = document.getElementById('gameControlPanel');
        this.statusIndicator = document.getElementById('gameStatusIndicator');
        this.statusText = document.getElementById('gameStatusText');
        this.startBtn = document.getElementById('startGameBtn');
        this.stopBtn = document.getElementById('stopGameBtn');
        this.resetBtn = document.getElementById('resetGameBtn');
        this.abortBtn = document.getElementById('abortGameBtn');
        this.navigationBtn = document.getElementById('navigationBtn');
        
        if (!this.element) {
            console.error('GameControlPanel: Element not found');
            return;
        }

        this.setupEventListeners();
        this.updateControlState();
    }

    setupEventListeners() {
        // Button click handlers
        if (this.startBtn) {
            this.startBtn.addEventListener('click', () => this.handleStartGame());
        }
        
        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.handleStopGame());
        }
        
        if (this.resetBtn) {
            this.resetBtn.addEventListener('click', () => this.handleResetGame());
        }
        
        if (this.abortBtn) {
            this.abortBtn.addEventListener('click', () => this.handleAbortGame());
        }
        
        if (this.navigationBtn) {
            this.navigationBtn.addEventListener('click', () => this.handleNavigateToMenu());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcut(e));

        // WebSocket event listeners
        if (window.socketManager) {
            window.socketManager.on('game_state_change', (data) => {
                this.handleGameStateChange(data);
            });

            window.socketManager.on('game_started', (data) => {
                this.handleGameStarted(data);
            });

            window.socketManager.on('game_ended', (data) => {
                this.handleGameEnded(data);
            });

            window.socketManager.on('error_occurred', (data) => {
                this.handleError(data);
            });

            window.socketManager.on('system_status_update', (data) => {
                this.handleSystemStatusUpdate(data);
            });
        }
    }

    handleStartGame() {
        if (this.gameState === 'waiting' || this.gameState === 'stopped') {
            this.setButtonLoading(this.startBtn, true);
            this.sendCommand('start_game');
        }
    }

    handleStopGame() {
        if (this.gameState === 'active') {
            this.setButtonLoading(this.stopBtn, true);
            this.sendCommand('stop_game');
        }
    }

    handleResetGame() {
        this.setButtonLoading(this.resetBtn, true);
        this.sendCommand('reset_game');
    }

    handleAbortGame() {
        if (this.gameState === 'active') {
            // Show confirmation for abort
            if (confirm('Are you sure you want to abort the game? All progress will be lost.')) {
                this.setButtonLoading(this.abortBtn, true);
                this.sendCommand('abort_game');
            }
        }
    }

    handleNavigateToMenu() {
        if (this.gameState === 'active') {
            if (confirm('Are you sure you want to return to the main menu? The current game will be stopped.')) {
                this.sendCommand('navigate_to_menu');
            }
        } else {
            this.sendCommand('navigate_to_menu');
        }
    }

    handleKeyboardShortcut(event) {
        // Don't trigger shortcuts if user is typing in an input
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        switch (event.key.toLowerCase()) {
            case ' ': // Space bar
                event.preventDefault();
                if (this.gameState === 'waiting' || this.gameState === 'stopped') {
                    this.handleStartGame();
                } else if (this.gameState === 'active') {
                    this.handleStopGame();
                }
                break;
                
            case 'r':
                event.preventDefault();
                this.handleResetGame();
                break;
                
            case 'escape':
                event.preventDefault();
                this.handleAbortGame();
                break;
                
            case 'h':
                event.preventDefault();
                this.handleNavigateToMenu();
                break;
        }
    }

    sendCommand(command, data = {}) {
        if (window.socketManager) {
            window.socketManager.emit(command, {
                timestamp: Date.now(),
                ...data
            });
        } else {
            console.error('SocketManager not available');
            this.clearAllButtonLoading();
        }
    }

    handleGameStateChange(data) {
        this.setGameState(data.state);
    }

    handleGameStarted(data) {
        this.setGameState('active');
        this.clearAllButtonLoading();
    }

    handleGameEnded(data) {
        this.setGameState('stopped');
        this.clearAllButtonLoading();
    }

    handleError(data) {
        console.error('Game Control Error:', data);
        this.clearAllButtonLoading();
        
        // Show error message (could be enhanced with a toast/notification system)
        if (data.message) {
            alert(`Error: ${data.message}`);
        }
    }

    handleSystemStatusUpdate(data) {
        // Update control availability based on system status
        const systemReady = data.system && data.system.status === 'operational';
        const hasTeams = data.teams && data.teams.count > 0;
        
        if (!systemReady) {
            this.disableAllControls();
        } else {
            this.updateControlState();
        }
    }

    setGameState(state) {
        this.gameState = state;
        this.updateStatusDisplay();
        this.updateControlState();
    }

    updateStatusDisplay() {
        // Remove all status classes
        this.statusIndicator.className = 'game-control-panel__status-indicator';
        
        switch (this.gameState) {
            case 'waiting':
                this.statusIndicator.classList.add('game-control-panel__status-indicator--waiting');
                this.statusText.textContent = 'Waiting';
                break;
                
            case 'active':
                this.statusIndicator.classList.add('game-control-panel__status-indicator--active');
                this.statusText.textContent = 'Active';
                break;
                
            case 'paused':
                this.statusIndicator.classList.add('game-control-panel__status-indicator--paused');
                this.statusText.textContent = 'Paused';
                break;
                
            case 'stopped':
                this.statusIndicator.classList.add('game-control-panel__status-indicator--stopped');
                this.statusText.textContent = 'Stopped';
                break;
        }
    }

    updateControlState() {
        switch (this.gameState) {
            case 'waiting':
            case 'stopped':
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.resetBtn.disabled = false;
                this.abortBtn.disabled = true;
                this.navigationBtn.disabled = false;
                break;
                
            case 'active':
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.resetBtn.disabled = true;
                this.abortBtn.disabled = false;
                this.navigationBtn.disabled = false;
                break;
                
            case 'paused':
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.resetBtn.disabled = false;
                this.abortBtn.disabled = false;
                this.navigationBtn.disabled = false;
                break;
        }
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.classList.add('game-control-panel__button--loading');
            button.disabled = true;
        } else {
            button.classList.remove('game-control-panel__button--loading');
            this.updateControlState(); // This will set proper disabled state
        }
    }

    clearAllButtonLoading() {
        [this.startBtn, this.stopBtn, this.resetBtn, this.abortBtn].forEach(btn => {
            if (btn) {
                btn.classList.remove('game-control-panel__button--loading');
            }
        });
        this.updateControlState();
    }

    disableAllControls() {
        [this.startBtn, this.stopBtn, this.resetBtn, this.abortBtn, this.navigationBtn].forEach(btn => {
            if (btn) {
                btn.disabled = true;
            }
        });
    }

    enableAllControls() {
        this.updateControlState();
    }

    // Public methods for external control
    getGameState() {
        return this.gameState;
    }

    requestStatus() {
        this.sendCommand('request_status');
    }

    destroy() {
        document.removeEventListener('keydown', this.handleKeyboardShortcut);
        
        if (window.socketManager) {
            window.socketManager.off('game_state_change');
            window.socketManager.off('game_started');
            window.socketManager.off('game_ended');
            window.socketManager.off('error_occurred');
            window.socketManager.off('system_status_update');
        }
    }
}
