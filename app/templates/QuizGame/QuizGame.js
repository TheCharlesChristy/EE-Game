/**
 * QuizGame Template JavaScript
 * Initializes and coordinates all quiz game components
 */
class QuizGameTemplate {
    constructor() {
        this.socket = null;
        this.gameState = 'waiting';
        this.components = {};
        
        this.init();
    }

    init() {
        console.log('QuizGame Template: Initializing...');
        
        this.setupSocketConnection();
        this.setupGlobalEventHandlers();
        
        console.log('QuizGame Template: Initialization complete');
    }

    setupSocketConnection() {
        // Initialize socket connection
        this.socket = io();
        window.socket = this.socket;

        // Setup global socket handlers
        this.socket.on('connect', () => {
            console.log('QuizGame: Connected to server');
            this.onSocketConnected();
        });

        this.socket.on('disconnect', () => {
            console.log('QuizGame: Disconnected from server');
            this.onSocketDisconnected();
        });

        // Quiz game specific events
        this.socket.on('quiz/game_started', (data) => {
            console.log('QuizGame: Game started:', data);
            this.onGameStarted(data);
        });

        this.socket.on('quiz/game_stopped', (data) => {
            console.log('QuizGame: Game stopped:', data);
            this.onGameStopped(data);
        });

        this.socket.on('quiz/new_question', (data) => {
            console.log('QuizGame: New question:', data);
            this.onNewQuestion(data);
        });

        this.socket.on('quiz/buzzers_enabled', (data) => {
            console.log('QuizGame: Buzzers enabled:', data);
            this.onBuzzersEnabled(data);
        });

        this.socket.on('quiz/team_buzzed', (data) => {
            console.log('QuizGame: Team buzzed:', data);
            this.onTeamBuzzed(data);
        });

        this.socket.on('quiz/answer_result', (data) => {
            console.log('QuizGame: Answer result:', data);
            this.onAnswerResult(data);
        });

        this.socket.on('quiz/question_skipped', (data) => {
            console.log('QuizGame: Question skipped:', data);
            this.onQuestionSkipped(data);
        });

        this.socket.on('quiz/resume_buzzing', (data) => {
            console.log('QuizGame: Resume buzzing:', data);
            this.onResumeBuzzing(data);
        });

        this.socket.on('quiz/game_over', (data) => {
            console.log('QuizGame: Game over:', data);
            this.onGameOver(data);
        });

        this.socket.on('quiz/game_state', (data) => {
            console.log('QuizGame: Game state update:', data);
            this.onGameStateUpdate(data);
        });

        this.socket.on('quiz/team_scores', (data) => {
            console.log('QuizGame: Team scores update:', data);
            this.onTeamScoresUpdate(data);
        });

        this.socket.on('error', (data) => {
            console.error('QuizGame: Server error:', data);
            this.onError(data);
        });

        console.log('QuizGame: Socket connection setup complete');
    }

    setupGlobalEventHandlers() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // Request current game state when page becomes visible
                this.requestGameState();
            }
        });

        // Handle window beforeunload
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.disconnect();
            }
        });
    }

    onSocketConnected() {
        // Request current game state
        this.requestGameState();
    }

    onSocketDisconnected() {
        // Handle disconnection
        this.showConnectionStatus('Disconnected from server', 'error');
    }

    onGameStarted(data) {
        this.gameState = 'active';
        this.showNotification('Quiz game started!', 'success');
    }

    onGameStopped(data) {
        this.gameState = 'stopped';
        this.showNotification('Quiz game stopped', 'info');
    }

    onNewQuestion(data) {
        // Question display component will handle this
        this.showNotification(`Question ${data.question_number} of ${data.total_questions}`, 'info');
    }

    onBuzzersEnabled(data) {
        this.showNotification('Buzzers are now active!', 'success');
    }

    onTeamBuzzed(data) {
        if (data.is_first) {
            this.showNotification(`${data.team_name} buzzed in first!`, 'info');
        }
    }

    onAnswerResult(data) {
        if (data.correct) {
            this.showNotification(`${data.team_name} answered correctly! +${data.points_awarded} points`, 'success');
        } else {
            this.showNotification(`${data.team_name} answered incorrectly`, 'warning');
        }
    }

    onQuestionSkipped(data) {
        this.showNotification(data.message, 'info');
    }

    onResumeBuzzing(data) {
        this.showNotification(data.message, 'info');
    }

    onGameOver(data) {
        this.gameState = 'over';
        
        if (data.winners && data.winners.length > 0) {
            if (data.winners.length === 1) {
                this.showNotification(`🎉 ${data.winners[0].name} wins with ${data.winners[0].score} points!`, 'success', 5000);
            } else {
                const winnerNames = data.winners.map(w => w.name).join(', ');
                this.showNotification(`🎉 Tie game! Winners: ${winnerNames}`, 'success', 5000);
            }
        } else {
            this.showNotification('Game over!', 'info');
        }
    }

    onGameStateUpdate(data) {
        this.gameState = data.state;
        // Individual components will handle their own state updates
    }

    onTeamScoresUpdate(data) {
        // Team scores component will handle this
    }

    onError(data) {
        this.showNotification(data.message || 'An error occurred', 'error');
    }

    requestGameState() {
        if (this.socket) {
            this.socket.emit('quiz/get_game_state', {});
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `quiz-game__notification quiz-game__notification--${type}`;
        notification.textContent = message;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'polite');

        // Add to page
        document.body.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.classList.add('quiz-game__notification--show');
        }, 10);

        // Remove after duration
        setTimeout(() => {
            notification.classList.remove('quiz-game__notification--show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    showConnectionStatus(message, type = 'info') {
        // Show persistent connection status
        let statusElement = document.querySelector('.quiz-game__connection-status');
        
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.className = 'quiz-game__connection-status';
            document.body.appendChild(statusElement);
        }

        statusElement.className = `quiz-game__connection-status quiz-game__connection-status--${type}`;
        statusElement.textContent = message;

        if (type === 'error') {
            statusElement.style.display = 'block';
        } else {
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 3000);
        }
    }

    emitEvent(eventName, data = {}) {
        if (this.socket) {
            console.log(`QuizGame Template: Emitting ${eventName}:`, data);
            this.socket.emit(eventName, data);
        }
    }
}

// Initialize the template when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quizGameTemplate = new QuizGameTemplate();
    });
} else {
    window.quizGameTemplate = new QuizGameTemplate();
}
