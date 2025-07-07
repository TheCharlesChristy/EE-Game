/**
 * QuizGameControls Component with Filter Integration
 * Manages quiz game controls and question filtering
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
        
        // Filter elements
        this.questionSetSelect = null;
        this.questionTypeSelect = null;
        this.selectedQuestionSet = 'all';
        this.selectedQuestionType = 'all';
        
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
        this.setupEventListeners();
        this.setupSocketConnection();
        console.log('QuizGameControls: Initialization complete');
    }

    setupElements() {
        // Game control buttons
        this.startButton = this.container.querySelector('[data-action="start"]');
        this.stopButton = this.container.querySelector('[data-action="stop"]');
        this.skipButton = this.container.querySelector('[data-action="skip"]');
        
        // Status elements
        this.statusText = this.container.querySelector('.quiz-game-controls__status-text');
        this.questionCount = this.container.querySelector('.quiz-game-controls__question-count');
        this.currentQuestion = this.container.querySelector('.quiz-game-controls__current');
        this.totalQuestions = this.container.querySelector('.quiz-game-controls__total');
        this.loading = this.container.querySelector('.quiz-game-controls__loading');
        
        // Filter elements
        this.questionSetSelect = this.container.querySelector('#question-set-select');
        this.questionTypeSelect = this.container.querySelector('#question-type-select');
    }

    setupEventListeners() {
        // Button event listeners
        if (this.startButton) {
            this.startButton.addEventListener('click', () => this.startGame());
        }
        
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopGame());
        }
        
        if (this.skipButton) {
            this.skipButton.addEventListener('click', () => this.skipQuestion());
        }
        
        // Filter event listeners
        if (this.questionSetSelect) {
            this.questionSetSelect.addEventListener('change', (e) => this.onQuestionSetChange(e));
        }
        
        if (this.questionTypeSelect) {
            this.questionTypeSelect.addEventListener('change', (e) => this.onQuestionTypeChange(e));
        }
    }

    setupSocketConnection() {
        // Wait for socket connection
        document.addEventListener('socketio_connected', () => {
            this.socket = window.socket;
            this.setupSocketHandlers();
            this.loadQuestionSets(); // Load question sets when connected
        });

        // Check if socket already exists
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
            this.loadQuestionSets(); // Load question sets when connected
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        console.log('QuizGameControls: Setting up socket handlers');

        // Game state handlers
        this.socket.on('game_started', () => this.onGameStarted());
        this.socket.on('quiz/game_started', () => this.onGameStarted());
        
        this.socket.on('game_stopped', () => this.onGameStopped());
        this.socket.on('quiz/game_stopped', () => this.onGameStopped());
        
        this.socket.on('quiz/game_over', () => this.onGameOver());
        
        this.socket.on('quiz/game_state', (data) => this.updateGameState(data));
        
        // Filter data handlers
        this.socket.on('quiz/question_sets', (data) => this.updateQuestionSets(data));
        this.socket.on('quiz/question_types', (data) => this.updateQuestionTypes(data));
    }

    // Filter Methods
    loadQuestionSets() {
        if (!this.socket) return;
        
        console.log('Loading question sets...');
        this.setFilterLoading(this.questionSetSelect, true);
        this.socket.emit('quiz/get_question_sets', {});
    }

    onQuestionSetChange(event) {
        this.selectedQuestionSet = event.target.value;
        console.log('Question set changed to:', this.selectedQuestionSet);
        
        // Reset question type to 'all'
        this.selectedQuestionType = 'all';
        if (this.questionTypeSelect) {
            this.questionTypeSelect.value = 'all';
        }
        
        // Load question types for the selected set
        this.loadQuestionTypes();
    }

    onQuestionTypeChange(event) {
        this.selectedQuestionType = event.target.value;
        console.log('Question type changed to:', this.selectedQuestionType);
    }

    loadQuestionTypes() {
        if (!this.socket) return;
        
        console.log('Loading question types for set:', this.selectedQuestionSet);
        this.setFilterLoading(this.questionTypeSelect, true);
        this.questionTypeSelect.disabled = true;
        
        this.socket.emit('quiz/get_question_types', {
            question_set: this.selectedQuestionSet
        });
    }

    updateQuestionSets(data) {
        console.log('Received question sets:', data);
        
        if (!this.questionSetSelect || !data.question_sets) return;
        
        // Clear existing options except 'all'
        this.questionSetSelect.innerHTML = '<option value="all">All Question Sets</option>';
        
        // Add new options
        data.question_sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set;
            option.textContent = this.formatQuestionSetName(set);
            this.questionSetSelect.appendChild(option);
        });
        
        this.setFilterLoading(this.questionSetSelect, false);
        
        // Enable question type select if a specific set is selected
        if (this.selectedQuestionSet !== 'all') {
            this.loadQuestionTypes();
        }
    }

    updateQuestionTypes(data) {
        console.log('Received question types:', data);
        
        if (!this.questionTypeSelect || !data.question_types) return;
        
        // Clear existing options except 'all'
        this.questionTypeSelect.innerHTML = '<option value="all">All Types</option>';
        
        // Add new options
        data.question_types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = this.formatQuestionTypeName(type);
            this.questionTypeSelect.appendChild(option);
        });
        
        this.setFilterLoading(this.questionTypeSelect, false);
        this.questionTypeSelect.disabled = false;
    }

    setFilterLoading(selectElement, isLoading) {
        if (!selectElement) return;
        
        if (isLoading) {
            selectElement.classList.add('quiz-game-controls__filter-select--loading');
        } else {
            selectElement.classList.remove('quiz-game-controls__filter-select--loading');
        }
    }

    formatQuestionSetName(setName) {
        // Format the set name for display (e.g., "general_knowledge" -> "General Knowledge")
        return setName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    formatQuestionTypeName(typeName) {
        // Format the type name for display
        return typeName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    // Game Control Methods
    startGame() {
        if (!this.socket || this.isGameActive) return;
        
        console.log('Starting quiz game with filters:', {
            question_set: this.selectedQuestionSet,
            question_type: this.selectedQuestionType
        });
        
        this.showLoading();
        
        // Disable filters during game
        if (this.questionSetSelect) this.questionSetSelect.disabled = true;
        if (this.questionTypeSelect) this.questionTypeSelect.disabled = true;
        
        // Emit start game with filter parameters
        this.socket.emit('quiz/start_game', {
            question_set: this.selectedQuestionSet,
            question_type: this.selectedQuestionType
        });
        
        setTimeout(() => {
            this.hideLoading();
            if (this.isGameActive) {
                this.skipButton.disabled = false;
            }
        }, 2000);
    }

    stopGame() {
        if (!this.socket || !this.isGameActive) return;
        
        console.log('Stopping quiz game');
        this.socket.emit('quiz/stop_game', {});
        
        // Re-enable filters
        if (this.questionSetSelect) this.questionSetSelect.disabled = false;
        if (this.questionTypeSelect && this.selectedQuestionSet !== 'all') {
            this.questionTypeSelect.disabled = false;
        }
    }

    skipQuestion() {
        if (!this.socket || !this.isGameActive) return;
        
        console.log('Skipping current question');
        this.socket.emit('quiz/skip_question', {});
    }

    // UI Update Methods
    showLoading() {
        if (this.loading) {
            this.loading.classList.add('active');
        }
    }

    hideLoading() {
        if (this.loading) {
            this.loading.classList.remove('active');
        }
    }

    setGameState(active) {
        this.isGameActive = active;
        
        if (this.startButton) {
            this.startButton.disabled = active;
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !active;
        }
        
        if (this.skipButton) {
            this.skipButton.disabled = !active;
        }
    }

    updateStatus(text) {
        if (this.statusText) {
            this.statusText.textContent = text;
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
        
        // Re-enable filters
        if (this.questionSetSelect) this.questionSetSelect.disabled = false;
        if (this.questionTypeSelect && this.selectedQuestionSet !== 'all') {
            this.questionTypeSelect.disabled = false;
        }
        
        // Emit custom event
        this.emitEvent('quiz_game_stopped');
    }

    onGameOver() {
        this.isGameActive = false;
        this.setGameState(false);
        this.updateStatus('Game Over');
        
        // Re-enable filters
        if (this.questionSetSelect) this.questionSetSelect.disabled = false;
        if (this.questionTypeSelect && this.selectedQuestionSet !== 'all') {
            this.questionTypeSelect.disabled = false;
        }
        
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
            'team_answering': 'Team answering...',
            'answer_result': 'Showing result...',
            'game_over': 'Game Over'
        };
        
        this.updateStatus(stateMessages[data.state] || data.state);
    }

    // Helper method to emit custom events
    emitEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quizGameControls = new QuizGameControls();
    });
} else {
    window.quizGameControls = new QuizGameControls();
}