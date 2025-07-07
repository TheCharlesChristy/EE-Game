/**
 * QuizQuestionDisplay Component
 * Displays quiz questions and manages visual states
 */
class QuizQuestionDisplay {
    constructor() {
        this.container = null;
        this.content = null;
        this.instruction = null;
        this.questionText = null;
        this.pointsContainer = null;
        this.pointsValue = null;
        this.buzzerIndicator = null;
        this.overlay = null;
        this.socket = null;
        this.currentState = 'waiting';
        
        this.init();
    }

    init() {
        console.log('QuizQuestionDisplay: Initializing...');
        this.container = document.querySelector('.quiz-question-display');
        if (!this.container) {
            console.error('QuizQuestionDisplay: Container not found');
            return;
        }

        this.setupElements();
        this.setupSocketConnection();
        console.log('QuizQuestionDisplay: Initialization complete');
    }

    setupElements() {
        this.content = this.container.querySelector('.quiz-question-display__content');
        this.instruction = this.container.querySelector('.quiz-question-display__instruction');
        this.questionText = this.container.querySelector('.quiz-question-display__text');
        this.pointsContainer = this.container.querySelector('.quiz-question-display__points');
        this.pointsValue = this.container.querySelector('.quiz-question-display__points-value');
        this.buzzerIndicator = this.container.querySelector('.quiz-question-display__buzzer-indicator');
        this.overlay = this.container.querySelector('.quiz-question-display__overlay');
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

        console.log('QuizQuestionDisplay: Setting up socket handlers');

        // Game state events
        this.socket.on('quiz/game_state', (data) => {
            this.updateState(data.state);
        });

        // New question event
        this.socket.on('quiz/new_question', (data) => {
            console.log('New question received:', data);
            this.displayQuestion(data);
        });

        // Buzzers enabled event
        this.socket.on('quiz/buzzers_enabled', (data) => {
            console.log('Buzzers enabled');
            this.showBuzzersActive();
        });

        // Team buzzed event
        this.socket.on('quiz/team_buzzed', (data) => {
            console.log('Team buzzed:', data);
            this.onTeamBuzzed(data);
        });

        // Answer result event
        this.socket.on('quiz/answer_result', (data) => {
            console.log('Answer result:', data);
            this.showAnswerResult(data.correct);
        });

        // Question skipped event
        this.socket.on('quiz/question_skipped', (data) => {
            console.log('Question skipped');
            this.onQuestionSkipped();
        });

        // Resume buzzing event
        this.socket.on('quiz/resume_buzzing', (data) => {
            console.log('Resume buzzing');
            this.showBuzzersActive();
        });

        // Game over event
        this.socket.on('quiz/game_over', (data) => {
            console.log('Game over');
            this.onGameOver();
        });

        // Game stopped event
        this.socket.on('quiz/game_stopped', (data) => {
            this.resetDisplay();
        });
    }

    updateState(state) {
        this.currentState = state;
        
        if (this.content) {
            // Map backend states to display states
            const stateMap = {
                'waiting': 'waiting',
                'question_display': 'question',
                'accepting_buzzes': 'buzzers-active',
                'team_answering': 'answering',
                'answer_result': 'result',
                'game_over': 'game-over'
            };
            
            this.content.setAttribute('data-state', stateMap[state] || state);
        }
    }

    displayQuestion(data) {
        // Hide instruction
        if (this.instruction) {
            this.instruction.style.display = 'none';
        }

        // Display question text
        if (this.questionText) {
            this.questionText.textContent = data.question;
            this.questionText.style.display = 'block';
        }

        // Display points
        if (this.pointsValue && this.pointsContainer) {
            this.pointsValue.textContent = data.points;
            this.pointsContainer.style.display = 'flex';
        }

        // Hide buzzer indicator initially
        if (this.buzzerIndicator) {
            this.buzzerIndicator.style.display = 'none';
        }

        // Update state
        this.updateState('question');
        
        // Emit event
        this.emitEvent('question_displayed', data);
    }

    showBuzzersActive() {
        if (this.buzzerIndicator) {
            this.buzzerIndicator.style.display = 'flex';
        }
        
        this.updateState('buzzers-active');
        
        // Add visual effect
        this.container.classList.add('quiz-question-display--buzzers-active');
        setTimeout(() => {
            this.container.classList.remove('quiz-question-display--buzzers-active');
        }, 500);
    }

    onTeamBuzzed(data) {
        if (this.buzzerIndicator) {
            this.buzzerIndicator.style.display = 'none';
        }
        
        this.updateState('answering');
        
        // Update instruction to show who buzzed
        if (this.instruction && data.team_name) {
            this.instruction.textContent = `${data.team_name} buzzed in!`;
            this.instruction.style.display = 'block';
        }
    }

    showAnswerResult(correct) {
        // Flash effect
        const flashClass = correct ? 'quiz-question-display--correct' : 'quiz-question-display--incorrect';
        this.container.classList.add(flashClass);
        
        setTimeout(() => {
            this.container.classList.remove(flashClass);
        }, 1000);
        
        // Update instruction
        if (this.instruction) {
            this.instruction.textContent = correct ? 'Correct!' : 'Incorrect!';
            this.instruction.style.display = 'block';
        }
    }

    onQuestionSkipped() {
        if (this.instruction) {
            this.instruction.textContent = 'Question skipped';
            this.instruction.style.display = 'block';
        }
        
        // Clear question after a moment
        setTimeout(() => {
            this.clearQuestion();
        }, 2000);
    }

    onGameOver() {
        this.clearQuestion();
        
        if (this.instruction) {
            this.instruction.textContent = 'Game Over!';
            this.instruction.style.display = 'block';
        }
        
        this.updateState('game-over');
    }

    clearQuestion() {
        if (this.questionText) {
            this.questionText.textContent = '';
        }
        
        if (this.pointsContainer) {
            this.pointsContainer.style.display = 'none';
        }
        
        if (this.buzzerIndicator) {
            this.buzzerIndicator.style.display = 'none';
        }
    }

    resetDisplay() {
        this.clearQuestion();
        
        if (this.instruction) {
            this.instruction.textContent = 'Press START to begin the quiz game';
            this.instruction.style.display = 'block';
        }
        
        this.updateState('waiting');
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
        window.quizQuestionDisplay = new QuizQuestionDisplay();
    });
} else {
    window.quizQuestionDisplay = new QuizQuestionDisplay();
}