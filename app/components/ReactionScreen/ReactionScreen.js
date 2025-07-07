class ReactionScreen {
    constructor() {
        this.container = null;
        this.content = null;
        this.mainText = null;
        this.symbol = null;
        this.countdownText = null;
        this.socket = null;
        this.currentState = 'neutral';
        
        this.init();
    }

    init() {
        console.log('ReactionScreen: Initializing...');
        this.container = document.querySelector('.reaction-screen');
        if (!this.container) {
            console.error('ReactionScreen: Container not found');
            return;
        }
        console.log('ReactionScreen: Container found');

        this.content = this.container.querySelector('.reaction-screen__content');
        this.mainText = this.container.querySelector('.reaction-screen__text');
        this.symbol = this.container.querySelector('.reaction-screen__symbol');
        this.countdownText = this.container.querySelector('.reaction-screen__countdown-text');

        console.log('ReactionScreen: Elements found:', {
            content: !!this.content,
            mainText: !!this.mainText,
            symbol: !!this.symbol,
            countdownText: !!this.countdownText
        });

        this.setupSocketConnection();
        this.setState('neutral'); // Initialize to neutral state
        console.log('ReactionScreen: Initialization complete');
    }

    setupSocketConnection() {
        // Listen for socket connection
        document.addEventListener('socketio_connected', () => {
            this.socket = window.socket;
            this.setupSocketHandlers();
        });

        // If socket is already available
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        console.log('ReactionScreen: Setting up socket handlers');

        // Listen for screen state changes from the game
        this.socket.on('reaction/screen_state', (data) => {
            console.log('ReactionScreen: Screen state update received:', data);
            if (data.state) {
                this.setState(data.state, data.message);
            }
        });

        // Listen for game events
        this.socket.on('game_started', (data) => {
            console.log('ReactionScreen: Game started event received:', data);
            this.setState('wait', 'GET READY');
        });

        this.socket.on('game_stopped', (data) => {
            console.log('ReactionScreen: Game stopped event received:', data);
            this.setState('neutral', 'GAME STOPPED');
        });

        // Listen for countdown updates
        this.socket.on('reaction/countdown', (data) => {
            if (data.count !== undefined) {
                this.updateCountdown(data.count);
            }
        });
    }

    setState(state, message = null) {
        console.log(`ReactionScreen: Setting state to '${state}' with message '${message}'`);
        this.currentState = state;
        
        if (this.content) {
            this.content.setAttribute('data-state', state);
            console.log(`ReactionScreen: Set data-state attribute to '${state}'`);
        } else {
            console.error('ReactionScreen: Content element not found!');
        }

        // Update text and symbol based on state
        switch (state) {
            case 'neutral':
                this.updateDisplay(message || 'GET READY', '⚡');
                break;
            case 'wait':
                this.updateDisplay(message || 'WAIT...', '🔴');
                break;
            case 'go':
                this.updateDisplay(message || 'GO!', '🟢');
                break;
            case 'too_early':
                this.updateDisplay(message || 'TOO EARLY!', '❌');
                break;
            case 'results':
                this.updateDisplay(message || 'ROUND COMPLETE', '🏁');
                break;
            default:
                this.updateDisplay(message || 'READY', '⚡');
        }

        console.log(`ReactionScreen: State change complete - current state: ${state}`);
    }

    updateDisplay(text, symbol) {
        if (this.mainText) {
            this.mainText.textContent = text;
        }
        
        if (this.symbol) {
            this.symbol.textContent = symbol;
        }

        // Clear countdown when updating main display
        this.clearCountdown();
    }

    updateCountdown(count) {
        if (this.countdownText) {
            if (count > 0) {
                this.countdownText.textContent = count.toString();
            } else {
                this.countdownText.textContent = '';
            }
        }
    }

    clearCountdown() {
        if (this.countdownText) {
            this.countdownText.textContent = '';
        }
    }

    getCurrentState() {
        return this.currentState;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.reactionScreen = new ReactionScreen();
    });
} else {
    window.reactionScreen = new ReactionScreen();
}