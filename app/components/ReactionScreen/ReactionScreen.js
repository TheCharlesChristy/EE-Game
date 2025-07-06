class ReactionScreen {
    constructor() {
        this.element = null;
        this.statusText = null;
        this.countdown = null;
        this.instructions = null;
        this.currentState = 'waiting';
        this.countdownTimer = null;
        this.init();
    }

    init() {
        this.element = document.getElementById('reactionScreen');
        this.statusText = document.getElementById('reactionStatusText');
        this.countdown = document.getElementById('reactionCountdown');
        this.instructions = document.getElementById('reactionInstructions');
        
        if (!this.element) {
            console.error('ReactionScreen: Element not found');
            return;
        }

        this.setState('waiting');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for WebSocket events
        if (window.socketManager) {
            window.socketManager.on('screen_state_change', (data) => {
                this.handleScreenStateChange(data);
            });

            window.socketManager.on('game_phase_update', (data) => {
                this.handleGamePhaseUpdate(data);
            });

            window.socketManager.on('round_start', (data) => {
                this.handleRoundStart(data);
            });

            window.socketManager.on('round_end', (data) => {
                this.handleRoundEnd(data);
            });

            window.socketManager.on('round_started', (data) => {
                this.handleRoundStarted(data);
            });
        }
    }

    setState(state, options = {}) {
        this.currentState = state;
        
        // Remove all state classes
        this.element.classList.remove('reaction-screen--green', 'reaction-screen--waiting', 'reaction-screen--hidden', 'reaction-screen--flashing');
        
        switch (state) {
            case 'waiting':
                this.element.classList.add('reaction-screen--waiting');
                this.statusText.textContent = 'WAITING FOR SIGNAL...';
                this.instructions.textContent = 'Press your button when the screen turns GREEN';
                this.countdown.textContent = '';
                break;
                
            case 'red':
                // Default red background (no additional class needed)
                this.statusText.textContent = 'GET READY...';
                this.instructions.textContent = 'Wait for GREEN - Do NOT press yet!';
                this.countdown.textContent = '';
                break;
                
            case 'green':
                this.element.classList.add('reaction-screen--green');
                this.statusText.textContent = 'PRESS NOW!';
                this.instructions.textContent = 'Press your button NOW!';
                this.countdown.textContent = '';
                break;
                
            case 'countdown':
                this.element.classList.add('reaction-screen--waiting');
                this.statusText.textContent = options.message || 'GET READY...';
                this.instructions.textContent = 'Next round starting soon...';
                if (options.count !== undefined) {
                    this.countdown.textContent = options.count;
                    this.countdown.classList.add('reaction-screen__countdown--pulse');
                    setTimeout(() => {
                        this.countdown.classList.remove('reaction-screen__countdown--pulse');
                    }, 1000);
                }
                break;
                
            case 'results':
                this.element.classList.add('reaction-screen--waiting');
                this.statusText.textContent = options.message || 'ROUND COMPLETE';
                this.instructions.textContent = options.details || 'Checking results...';
                this.countdown.textContent = '';
                break;
                
            case 'hidden':
                this.element.classList.add('reaction-screen--hidden');
                break;
        }
    }

    handleScreenStateChange(data) {
        if (data.state === 'red') {
            this.setState('red');
        } else if (data.state === 'green') {
            this.setState('green');
        } else if (data.state === 'waiting') {
            this.setState('waiting');
        }
    }

    handleGamePhaseUpdate(data) {
        switch (data.phase) {
            case 'waiting':
                this.setState('waiting');
                break;
            case 'preparing':
                this.setState('red');
                break;
            case 'active':
                this.setState('green');
                break;
            case 'complete':
                this.setState('results', {
                    message: 'ROUND COMPLETE',
                    details: 'Processing results...'
                });
                break;
        }
    }

    handleRoundStart(data) {
        this.setState('countdown', {
            message: `ROUND ${data.round || ''}`,
            details: 'Get ready...'
        });
    }

    handleRoundStarted(data) {
        this.setState('red');
        
        // Start countdown if provided
        if (data.countdown) {
            this.startCountdown(data.countdown);
        }
    }

    handleRoundEnd(data) {
        this.setState('results', {
            message: 'ROUND COMPLETE',
            details: data.message || 'Results processed'
        });
    }

    startCountdown(seconds) {
        this.clearCountdown();
        let remaining = seconds;
        
        this.countdownTimer = setInterval(() => {
            if (remaining > 0) {
                this.setState('countdown', {
                    count: remaining,
                    message: 'NEXT ROUND'
                });
                remaining--;
            } else {
                this.clearCountdown();
                this.setState('red');
            }
        }, 1000);
    }

    clearCountdown() {
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
    }

    show() {
        this.element.classList.remove('reaction-screen--hidden');
    }

    hide() {
        this.setState('hidden');
    }

    // Public methods for external control
    setWaiting() {
        this.setState('waiting');
    }

    setRed() {
        this.setState('red');
    }

    setGreen() {
        this.setState('green');
    }

    setMessage(message, details = '') {
        this.setState('results', { message, details });
    }

    destroy() {
        this.clearCountdown();
        if (window.socketManager) {
            window.socketManager.off('screen_state_change');
            window.socketManager.off('game_phase_update');
            window.socketManager.off('round_start');
            window.socketManager.off('round_end');
            window.socketManager.off('round_started');
        }
    }
}
