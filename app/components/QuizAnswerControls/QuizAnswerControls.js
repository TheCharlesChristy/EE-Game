/**
 * QuizAnswerControls Component
 * Handles answer marking controls for the game runner
 */
class QuizAnswerControls {
    constructor() {
        this.container = null;
        this.teamNameElement = null;
        this.correctButton = null;
        this.incorrectButton = null;
        this.socket = null;
        this.currentTeam = null;
        
        this.init();
    }

    init() {
        console.log('QuizAnswerControls: Initializing...');
        this.container = document.querySelector('.quiz-answer-controls');
        if (!this.container) {
            console.error('QuizAnswerControls: Container not found');
            return;
        }

        this.setupElements();
        this.attachEventListeners();
        this.setupSocketConnection();
        console.log('QuizAnswerControls: Initialization complete');
    }

    setupElements() {
        this.teamNameElement = this.container.querySelector('.quiz-answer-controls__team-name');
        this.correctButton = this.container.querySelector('[data-action="correct"]');
        this.incorrectButton = this.container.querySelector('[data-action="incorrect"]');
    }

    attachEventListeners() {
        if (this.correctButton) {
            this.correctButton.addEventListener('click', () => this.handleCorrectAnswer());
        }

        if (this.incorrectButton) {
            this.incorrectButton.addEventListener('click', () => this.handleIncorrectAnswer());
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

        console.log('QuizAnswerControls: Setting up socket handlers');

        // Team buzzed event
        this.socket.on('quiz/team_buzzed', (data) => {
            console.log('Team buzzed, showing answer controls:', data);
            this.showControls(data.team_id, data.team_name);
        });

        // Answer result event
        this.socket.on('quiz/answer_result', (data) => {
            console.log('Answer result received');
            this.hideControls();
        });

        // Resume buzzing event (incorrect answer)
        this.socket.on('quiz/resume_buzzing', (data) => {
            console.log('Resume buzzing, hiding controls');
            this.hideControls();
        });

        // Question skipped event
        this.socket.on('quiz/question_skipped', (data) => {
            this.hideControls();
        });

        // New question event
        this.socket.on('quiz/new_question', (data) => {
            this.hideControls();
        });

        // Game stopped event
        this.socket.on('quiz/game_stopped', (data) => {
            this.hideControls();
        });
    }

    showControls(teamId, teamName) {
        this.currentTeam = teamId;
        
        if (this.teamNameElement) {
            this.teamNameElement.textContent = teamName || teamId;
        }
        
        // Enable buttons
        if (this.correctButton) {
            this.correctButton.disabled = false;
        }
        if (this.incorrectButton) {
            this.incorrectButton.disabled = false;
        }
        
        // Show container with animation
        this.container.style.display = 'block';
        this.container.classList.add('quiz-answer-controls--show');
        
        // Emit event
        this.emitEvent('answer_controls_shown', { teamId, teamName });
    }

    hideControls() {
        this.currentTeam = null;
        
        // Hide container
        this.container.style.display = 'none';
        this.container.classList.remove('quiz-answer-controls--show');
        
        // Reset team name
        if (this.teamNameElement) {
            this.teamNameElement.textContent = '-';
        }
        
        // Emit event
        this.emitEvent('answer_controls_hidden');
    }

    handleCorrectAnswer() {
        if (!this.socket || !this.currentTeam) {
            console.error('Cannot mark answer - no team buzzing');
            return;
        }

        console.log('Marking answer as correct');
        
        // Disable buttons to prevent double-clicking
        this.disableButtons();
        
        // Send to server
        this.socket.emit('quiz/mark_answer', { correct: true });
        
        // Visual feedback
        this.correctButton.classList.add('quiz-answer-controls__button--clicked');
        
        // Emit event
        this.emitEvent('answer_marked', { correct: true, teamId: this.currentTeam });
    }

    handleIncorrectAnswer() {
        if (!this.socket || !this.currentTeam) {
            console.error('Cannot mark answer - no team buzzing');
            return;
        }

        console.log('Marking answer as incorrect');
        
        // Disable buttons to prevent double-clicking
        this.disableButtons();
        
        // Send to server
        this.socket.emit('quiz/mark_answer', { correct: false });
        
        // Visual feedback
        this.incorrectButton.classList.add('quiz-answer-controls__button--clicked');
        
        // Emit event
        this.emitEvent('answer_marked', { correct: false, teamId: this.currentTeam });
    }

    disableButtons() {
        if (this.correctButton) {
            this.correctButton.disabled = true;
        }
        if (this.incorrectButton) {
            this.incorrectButton.disabled = true;
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
        window.quizAnswerControls = new QuizAnswerControls();
    });
} else {
    window.quizAnswerControls = new QuizAnswerControls();
}