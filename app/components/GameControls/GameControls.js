class GameControls {
    constructor() {
        this.container = null;
        this.startButton = null;
        this.stopButton = null;
        this.statusText = null;
        this.loading = null;
        this.socket = null;
        this.isGameActive = false;
        
        this.init();
    }

    init() {
        this.container = document.querySelector('.game-controls');
        if (!this.container) {
            console.error('GameControls: Container not found');
            return;
        }

        this.startButton = this.container.querySelector('[data-action="start"]');
        this.stopButton = this.container.querySelector('[data-action="stop"]');
        this.testButton = this.container.querySelector('[data-action="test"]');
        this.statusText = this.container.querySelector('.game-controls__status-text');
        this.loading = this.container.querySelector('.game-controls__loading');

        this.setupEventListeners();
        this.setupSocketConnection();
    }

    setupEventListeners() {
        if (this.startButton) {
            this.startButton.addEventListener('click', () => this.startGame());
        }

        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopGame());
        }

        if (this.testButton) {
            this.testButton.addEventListener('click', () => this.testScreenStates());
        }

        // Listen for socket connection
        document.addEventListener('socketio_connected', () => {
            this.socket = window.socket;
            this.setupSocketHandlers();
        });
    }

    setupSocketConnection() {
        // If socket is already available
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        this.socket.on('game_started', (data) => {
            console.log('Game started:', data);
            this.setGameState(true);
            this.updateStatus('Game Active');
        });

        this.socket.on('game_stopped', (data) => {
            console.log('Game stopped:', data);
            this.setGameState(false);
            this.updateStatus('Game Stopped');
        });
    }

    startGame() {
        if (!this.socket) {
            console.error('Socket not connected');
            this.updateStatus('Connection Error');
            return;
        }

        this.showLoading(true);
        this.updateStatus('Starting Game...');
        
        this.socket.emit('reaction/start_game', {});
    }

    stopGame() {
        if (!this.socket) {
            console.error('Socket not connected');
            return;
        }

        this.showLoading(true);
        this.updateStatus('Stopping Game...');
        
        this.socket.emit('reaction/stop_game', {});
    }

    testScreenStates() {
        if (!this.socket) {
            console.error('Socket not connected');
            return;
        }

        const states = [
            { state: 'neutral', message: 'TEST NEUTRAL' },
            { state: 'wait', message: 'TEST WAIT' },
            { state: 'go', message: 'TEST GO' },
            { state: 'too_early', message: 'TEST TOO EARLY' },
            { state: 'results', message: 'TEST RESULTS' }
        ];

        let currentIndex = 0;
        const testInterval = setInterval(() => {
            if (currentIndex >= states.length) {
                clearInterval(testInterval);
                this.socket.emit('reaction/test_screen_state', { state: 'neutral', message: 'TEST COMPLETE' });
                return;
            }

            const currentState = states[currentIndex];
            console.log('Testing screen state:', currentState);
            this.socket.emit('reaction/test_screen_state', currentState);
            currentIndex++;
        }, 2000);
    }

    setGameState(isActive) {
        this.isGameActive = isActive;
        
        if (this.startButton) {
            this.startButton.disabled = isActive;
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !isActive;
        }

        this.showLoading(false);
    }

    updateStatus(message) {
        if (this.statusText) {
            this.statusText.textContent = message;
        }
    }

    showLoading(show) {
        if (this.loading) {
            if (show) {
                this.loading.classList.add('active');
            } else {
                this.loading.classList.remove('active');
            }
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.gameControls = new GameControls();
    });
} else {
    window.gameControls = new GameControls();
}