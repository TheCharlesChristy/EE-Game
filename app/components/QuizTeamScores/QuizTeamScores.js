/**
 * QuizTeamScores Component
 * Displays team scores and states during quiz game
 */
class QuizTeamScores {
    constructor() {
        this.container = null;
        this.grid = null;
        this.socket = null;
        this.teams = {};
        this.leadingTeamId = null;
        
        this.init();
    }

    init() {
        console.log('QuizTeamScores: Initializing...');
        this.container = document.querySelector('.quiz-team-scores');
        if (!this.container) {
            console.error('QuizTeamScores: Container not found');
            return;
        }

        this.setupElements();
        this.setupSocketConnection();
        console.log('QuizTeamScores: Initialization complete');
    }

    setupElements() {
        this.grid = this.container.querySelector('.quiz-team-scores__grid');
        if (!this.grid) {
            console.error('QuizTeamScores: Grid element not found');
            return;
        }
    }

    setupSocketConnection() {
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
        } else {
            // Wait for socket to be available
            const checkSocket = () => {
                if (window.socket) {
                    this.socket = window.socket;
                    this.setupSocketHandlers();
                } else {
                    setTimeout(checkSocket, 100);
                }
            };
            checkSocket();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        // Listen for team score updates
        this.socket.on('quiz/team_scores', (data) => {
            console.log('QuizTeamScores: Received team scores:', data);
            this.updateTeamScores(data.scores);
        });

        // Listen for team buzzer events
        this.socket.on('quiz/team_buzzed', (data) => {
            console.log('QuizTeamScores: Team buzzed:', data);
            this.onTeamBuzzed(data.team_id);
        });

        // Listen for answer results
        this.socket.on('quiz/answer_result', (data) => {
            console.log('QuizTeamScores: Answer result:', data);
            this.onAnswerResult(data);
        });

        // Listen for game state changes
        this.socket.on('quiz/game_state', (data) => {
            this.onGameStateChange(data);
        });

        // Listen for resume buzzing
        this.socket.on('quiz/resume_buzzing', (data) => {
            this.onResumeBuzzing();
        });

        // Listen for game over
        this.socket.on('quiz/game_over', (data) => {
            this.onGameOver(data);
        });

        console.log('QuizTeamScores: Socket handlers setup complete');
    }

    updateTeamScores(scores) {
        this.teams = scores;
        this.renderTeamCards();
        this.updateLeadingTeam();
    }

    renderTeamCards() {
        if (!this.grid) return;

        // Clear existing cards
        this.grid.innerHTML = '';

        // Create cards for each team
        Object.entries(this.teams).forEach(([teamId, teamData]) => {
            const card = this.createTeamCard(teamId, teamData);
            this.grid.appendChild(card);
        });
    }

    createTeamCard(teamId, teamData) {
        const card = document.createElement('div');
        card.className = 'quiz-team-card';
        card.dataset.teamId = teamId;

        // Add state classes
        if (teamData.locked_out) {
            card.classList.add('quiz-team-card--locked');
        }
        if (teamData.has_buzzed) {
            card.classList.add('quiz-team-card--buzzing');
        }

        card.innerHTML = `
            <div class="quiz-team-card__name">${teamData.name}</div>
            <div class="quiz-team-card__score">${teamData.score}</div>
            <div class="quiz-team-card__status">${this.getTeamStatus(teamData)}</div>
        `;

        return card;
    }

    getTeamStatus(teamData) {
        if (teamData.locked_out) {
            return 'Locked Out';
        }
        if (teamData.has_buzzed) {
            return 'Buzzed In';
        }
        return 'Ready';
    }

    onTeamBuzzed(teamId) {
        const card = this.getTeamCard(teamId);
        if (!card) return;

        // Add buzzing state
        card.classList.add('quiz-team-card--buzzing');
        
        // Update status
        const status = card.querySelector('.quiz-team-card__status');
        if (status) {
            status.textContent = 'Buzzed In';
        }
    }

    onAnswerResult(data) {
        const { team_id, correct, points_awarded, new_score } = data;
        const card = this.getTeamCard(team_id);
        if (!card) return;

        // Update score with animation
        const scoreElement = card.querySelector('.quiz-team-card__score');
        if (scoreElement && correct) {
            scoreElement.textContent = new_score;
            scoreElement.classList.add('quiz-team-card__score--increase');
            
            // Remove animation class after animation completes
            setTimeout(() => {
                scoreElement.classList.remove('quiz-team-card__score--increase');
            }, 1000);
        }

        // Update team state classes
        if (correct) {
            card.classList.remove('quiz-team-card--buzzing');
        } else {
            card.classList.remove('quiz-team-card--buzzing');
            card.classList.add('quiz-team-card--locked');
            
            const status = card.querySelector('.quiz-team-card__status');
            if (status) {
                status.textContent = 'Locked Out';
            }
        }
    }

    onGameStateChange(data) {
        const { state, current_answering_team } = data;
        
        // Remove answering state from all cards
        this.grid.querySelectorAll('.quiz-team-card').forEach(card => {
            card.classList.remove('quiz-team-card--answering');
        });

        // Add answering state to current team
        if (current_answering_team && state === 'team_answering') {
            const card = this.getTeamCard(current_answering_team);
            if (card) {
                card.classList.add('quiz-team-card--answering');
            }
        }
    }

    onResumeBuzzing() {
        // Remove buzzing state from all teams except locked out ones
        this.grid.querySelectorAll('.quiz-team-card').forEach(card => {
            if (!card.classList.contains('quiz-team-card--locked')) {
                card.classList.remove('quiz-team-card--buzzing', 'quiz-team-card--answering');
                
                const status = card.querySelector('.quiz-team-card__status');
                if (status) {
                    status.textContent = 'Ready';
                }
            }
        });
    }

    onGameOver(data) {
        // Remove all active states
        this.grid.querySelectorAll('.quiz-team-card').forEach(card => {
            card.classList.remove('quiz-team-card--buzzing', 'quiz-team-card--answering', 'quiz-team-card--locked');
            
            const status = card.querySelector('.quiz-team-card__status');
            if (status) {
                status.textContent = 'Final Score';
            }
        });

        // Highlight winners
        if (data.winners) {
            data.winners.forEach(winner => {
                const card = this.getTeamCard(winner.team_id);
                if (card) {
                    card.classList.add('quiz-team-card--leading');
                    
                    const status = card.querySelector('.quiz-team-card__status');
                    if (status) {
                        status.textContent = 'Winner!';
                    }
                }
            });
        }
    }

    updateLeadingTeam() {
        if (!this.teams || Object.keys(this.teams).length === 0) return;

        // Find team with highest score
        let maxScore = Math.max(...Object.values(this.teams).map(team => team.score));
        let leadingTeams = Object.entries(this.teams).filter(([_, team]) => team.score === maxScore);

        // Remove leading class from all cards
        this.grid.querySelectorAll('.quiz-team-card').forEach(card => {
            card.classList.remove('quiz-team-card--leading');
        });

        // Add leading class to current leaders (only if score > 0 and not tied with everyone)
        if (maxScore > 0 && leadingTeams.length < Object.keys(this.teams).length) {
            leadingTeams.forEach(([teamId, _]) => {
                const card = this.getTeamCard(teamId);
                if (card) {
                    card.classList.add('quiz-team-card--leading');
                }
            });
        }
    }

    getTeamCard(teamId) {
        return this.grid.querySelector(`[data-team-id="${teamId}"]`);
    }

    resetScores() {
        // Remove all state classes and reset display
        this.grid.querySelectorAll('.quiz-team-card').forEach(card => {
            card.classList.remove('quiz-team-card--buzzing', 'quiz-team-card--locked', 'quiz-team-card--answering', 'quiz-team-card--leading');
            
            const scoreElement = card.querySelector('.quiz-team-card__score');
            if (scoreElement) {
                scoreElement.textContent = '0';
            }
            
            const status = card.querySelector('.quiz-team-card__status');
            if (status) {
                status.textContent = 'Ready';
            }
        });
    }

    emitEvent(eventName, data = {}) {
        if (this.socket) {
            console.log(`QuizTeamScores: Emitting ${eventName}:`, data);
            this.socket.emit(eventName, data);
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quizTeamScores = new QuizTeamScores();
    });
} else {
    window.quizTeamScores = new QuizTeamScores();
}
