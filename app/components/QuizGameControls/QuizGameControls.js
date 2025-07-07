/**
 * QuizGameControls Component
 * Handles game control buttons and status display for the Quiz Game
 */
class QuizGameControls {
    constructor() {
        this.container = null;
        this.startButton = null;
        this.stopButton = null;
        this.skipButton = null;
        this.statusText = null;
        this.questionCount = null;
        this.currentQuestion = null;
        this.totalQuestions = null;
        this.loading = null;
        this.socket = null;
        this.isGameActive = false;
        
        this.init();
    }

    init() {
        console.log('QuizGameControls: Initializing...');
        this.container = document.querySelector('.quiz-game-controls');
        if (!this.container) {
            console.error('QuizGameControls: Container not found');
            return;
        }

        this.setupElements();
        this.attachEventListeners();
        this.setupSocketConnection();
        console.log('QuizGameControls: Initialization complete');
    }

    setupElements() {
        // Buttons
        this.startButton = this.container.querySelector('[data-action="start"]');
        this.stopButton = this.container.querySelector('[data-action="stop"]');
        this.skipButton = this.container.querySelector('[data-action="skip"]');
        
        // Status elements
        this.statusText = this.container.querySelector('.quiz-game-controls__status-text');
        this.questionCount = this.container.querySelector('.quiz-game-controls__question-count');
        this.currentQuestion = this.container.querySelector('.quiz-game-controls__current');
        this.totalQuestions = this.container.querySelector('.quiz-game-controls__total');
        this.loading = this.container.querySelector('.quiz-game-controls__loading');
    }

    attachEventListeners() {
        if (this.startButton) {
            this.startButton.addEventListener('click', () => this.handleStartGame());
        }

        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.handleStopGame());
        }

        if (this.skipButton) {
            this.skipButton.addEventListener('click', () => this.handleSkipQuestion());
        }
    }

    setupSocketConnection() {
        // Wait for socket connection
        document.addEventListener('socketio_connected', () => {
            this.socket = window.socket;
            this.setupSocketHandlers();
        });

        // Check if socket already exists
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        console.log('QuizGameControls: Setting up socket handlers');

        // Game state events
        this.socket.on('quiz/game_started', (data) => {
            console.log('Quiz game started:', data);
            this.onGameStarted();
        });

        this.socket.on('quiz/game_stopped', (data) => {
            console.log('Quiz game stopped:', data);
            this.onGameStopped();
        });

        this.socket.on('quiz/game_state', (data) => {
            console.log('Game state update:', data);
            this.updateGameState(data);
        });

        this.socket.on('quiz/new_question', (data) => {
            console.log('New question:', data);
            this.updateQuestionCount(data.question_number, data.total_questions);
        });

        this.socket.on('quiz/game_over', (data) => {
            console.log('Game over:', data);
            this.onGameOver();
        });
    }

    handleStartGame() {
        if (!this.socket) {
            console.error('Socket not connected');
            return;
        }

        console.log('Starting quiz game...');
        this.showLoading(true);
        this.socket.emit('quiz/start_game', {});
        
        // Update UI immediately
        this.startButton.disabled = true;
        this.updateStatus('Starting game...');
    }

    handleStopGame() {
        if (!this.socket) {
            console.error('Socket not connected');
            return;
        }

        console.log('Stopping quiz game...');
        this.socket.emit('quiz/stop_game', {});
        
        // Update UI immediately
        this.stopButton.disabled = true;
        this.updateStatus('Stopping game...');
    }

    handleSkipQuestion() {
        if (!this.socket || !this.isGameActive) {
            console.error('Cannot skip question - game not active');
            return;
        }

        console.log('Skipping current question...');
        this.socket.emit('quiz/skip_question', {});
        
        // Temporarily disable skip button
        this.skipButton.disabled = true;
        setTimeout(() => {
            if (this.isGameActive) {
                this.skipButton.disabled = false;
            }
        }, 2000);
    }

    onGameStarted() {
        this.isGameActive = true;
        this.setGameState(true);
        this.updateStatus('Game in progress');
        
        if (this.questionCount) {
            this.questionCount.style.display = 'block';
        }
        
        // Emit custom event
        this.emitEvent('quiz_game_started');
    }

    onGameStopped() {
        this.isGameActive = false;
        this.setGameState(false);
        this.updateStatus('Ready to Start');
        
        if (this.questionCount) {
            this.questionCount.style.display = 'none';
        }
        
        // Emit custom event
        this.emitEvent('quiz_game_stopped');
    }

    onGameOver() {
        this.isGameActive = false;
        this.setGameState(false);
        this.updateStatus('Game Over');
        
        // Emit custom event
        this.emitEvent('quiz_game_over');
    }

    updateGameState(data) {
        // Update game active state
        this.isGameActive = data.state !== 'waiting' && data.state !== 'game_over';
        
        // Update question count
        if (data.questions_answered !== undefined) {
            this.updateQuestionCount(data.questions_answered + 1, data.total_questions);
        }
        
        // Update status text based on state
        const stateMessages = {
            'waiting': 'Ready to Start',
            'question_display': 'Displaying question...',
            'accepting_buzzes': 'Buzzers active!',
            'team_answering': `Team answering...`,
            'answer_result': 'Processing answer...',
            'game_over': 'Game Over'
        };
        
        if (stateMessages[data.state]) {
            this.updateStatus(stateMessages[data.state]);
        }
        
        // Enable/disable skip button based on state
        if (this.skipButton) {
            this.skipButton.disabled = !this.isGameActive || 
                data.state === 'answer_result' || 
                data.state === 'game_over';
        }
    }

    updateQuestionCount(current, total) {
        if (this.currentQuestion) {
            this.currentQuestion.textContent = current;
        }
        if (this.totalQuestions) {
            this.totalQuestions.textContent = total;
        }
    }

    setGameState(isActive) {
        this.isGameActive = isActive;
        
        if (this.startButton) {
            this.startButton.disabled = isActive;
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !isActive;
        }
        
        if (this.skipButton) {
            this.skipButton.disabled = !isActive;
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

    emitEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quizGameControls = new QuizGameControls();
    });
} else {
    window.quizGameControls = new QuizGameControls();
}