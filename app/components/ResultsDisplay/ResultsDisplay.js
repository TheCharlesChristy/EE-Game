class ResultsDisplay {
    constructor() {
        this.element = null;
        this.titleElement = null;
        this.roundInfoElement = null;
        this.roundResultsElement = null;
        this.gameStatsElement = null;
        this.winnerAnnouncementElement = null;
        this.continueBtn = null;
        this.newGameBtn = null;
        this.backToMenuBtn = null;
        
        this.currentResults = null;
        this.gameStatistics = null;
        this.isVisible = false;
        
        this.init();
    }

    init() {
        this.element = document.getElementById('resultsDisplay');
        this.titleElement = document.getElementById('resultsTitle');
        this.roundInfoElement = document.getElementById('roundInfo');
        this.roundResultsElement = document.getElementById('roundResults');
        this.gameStatsElement = document.getElementById('gameStats');
        this.winnerAnnouncementElement = document.getElementById('winnerAnnouncement');
        this.continueBtn = document.getElementById('continueBtn');
        this.newGameBtn = document.getElementById('newGameBtn');
        this.backToMenuBtn = document.getElementById('backToMenuBtn');
        
        if (!this.element) {
            console.error('ResultsDisplay: Element not found');
            return;
        }

        this.setupEventListeners();
        this.hide(); // Start hidden
    }

    setupEventListeners() {
        // Button click handlers
        if (this.continueBtn) {
            this.continueBtn.addEventListener('click', () => this.handleContinue());
        }
        
        if (this.newGameBtn) {
            this.newGameBtn.addEventListener('click', () => this.handleNewGame());
        }
        
        if (this.backToMenuBtn) {
            this.backToMenuBtn.addEventListener('click', () => this.handleBackToMenu());
        }

        // WebSocket event listeners
        if (window.socketManager) {
            window.socketManager.on('round_complete', (data) => {
                this.handleRoundComplete(data);
            });

            window.socketManager.on('game_results', (data) => {
                this.handleGameResults(data);
            });

            window.socketManager.on('winner_announced', (data) => {
                this.handleWinnerAnnounced(data);
            });

            window.socketManager.on('statistics_update', (data) => {
                this.handleStatisticsUpdate(data);
            });
        }
    }

    handleRoundComplete(data) {
        this.currentResults = data;
        this.showRoundResults(data);
    }

    handleGameResults(data) {
        this.gameStatistics = data;
        this.showGameResults(data);
    }

    handleWinnerAnnounced(data) {
        this.showWinnerAnnouncement(data);
    }

    handleStatisticsUpdate(data) {
        this.gameStatistics = data;
        if (this.isVisible && this.gameStatsElement.style.display !== 'none') {
            this.updateGameStatistics();
        }
    }

    showRoundResults(data) {
        this.show();
        
        // Update header
        this.titleElement.textContent = 'Round Results';
        this.roundInfoElement.textContent = `Round ${data.round || ''} Complete`;
        
        // Show round results, hide other sections
        this.roundResultsElement.style.display = 'block';
        this.gameStatsElement.style.display = 'none';
        this.winnerAnnouncementElement.style.display = 'none';
        
        // Show continue button, hide others
        this.continueBtn.style.display = 'inline-block';
        this.newGameBtn.style.display = 'none';
        
        // Render team results
        this.renderTeamResults(data.results || data.teams || []);
    }

    showGameResults(data) {
        this.show();
        
        // Update header
        this.titleElement.textContent = 'Game Results';
        this.roundInfoElement.textContent = 'Game Complete';
        
        // Show game stats, hide round results
        this.roundResultsElement.style.display = 'none';
        this.gameStatsElement.style.display = 'block';
        this.winnerAnnouncementElement.style.display = 'none';
        
        // Show new game button, hide continue
        this.continueBtn.style.display = 'none';
        this.newGameBtn.style.display = 'inline-block';
        
        // Update statistics
        this.updateGameStatistics();
    }

    showWinnerAnnouncement(data) {
        this.show();
        
        // Update header
        this.titleElement.textContent = 'Game Complete';
        this.roundInfoElement.textContent = 'Winner Announced';
        
        // Show winner announcement, hide other sections
        this.roundResultsElement.style.display = 'none';
        this.gameStatsElement.style.display = 'none';
        this.winnerAnnouncementElement.style.display = 'block';
        
        // Show new game button
        this.continueBtn.style.display = 'none';
        this.newGameBtn.style.display = 'inline-block';
        
        // Update winner info
        this.updateWinnerDisplay(data);
        this.createConfetti();
    }

    renderTeamResults(results) {
        if (!this.roundResultsElement) return;
        
        const gridDiv = document.createElement('div');
        gridDiv.className = 'results-display__results-grid';
        
        results.forEach((result, index) => {
            const teamDiv = document.createElement('div');
            teamDiv.className = 'results-display__team-result';
            
            // Determine result status
            let statusClass = '';
            let statusText = '';
            let timeDisplay = '—';
            
            if (result.eliminated) {
                statusClass = 'results-display__team-result--eliminated';
                statusText = 'Eliminated';
            } else if (result.pressed || result.reaction_time !== undefined) {
                statusClass = 'results-display__team-result--success';
                statusText = 'Passed';
                timeDisplay = `${result.reaction_time || result.time || 0}ms`;
            } else {
                statusClass = 'results-display__team-result--failed';
                statusText = 'Failed';
            }
            
            teamDiv.classList.add(statusClass);
            
            // Determine time styling
            let timeClass = 'results-display__team-time';
            if (result.reaction_time <= 100) {
                timeClass += ' results-display__team-time--fast';
            } else if (result.reaction_time >= 300) {
                timeClass += ' results-display__team-time--slow';
            }
            
            teamDiv.innerHTML = `
                <div class="results-display__team-name">
                    ${result.team_name || result.name || `Team ${result.team_id || index + 1}`}
                </div>
                <div class="results-display__team-status results-display__team-status--${statusText.toLowerCase()}">
                    ${statusText}
                </div>
                <div class="${timeClass}">
                    ${timeDisplay}
                </div>
                <div class="results-display__team-lives">
                    Lives: ${this.renderLivesDots(result.lives || 0, result.max_lives || 3)}
                </div>
            `;
            
            gridDiv.appendChild(teamDiv);
        });
        
        this.roundResultsElement.innerHTML = '';
        this.roundResultsElement.appendChild(gridDiv);
    }

    renderLivesDots(currentLives, maxLives) {
        let dotsHTML = '';
        for (let i = 0; i < maxLives; i++) {
            const dotClass = i < currentLives ? 
                'results-display__life-dot results-display__life-dot--active' : 
                'results-display__life-dot results-display__life-dot--lost';
            dotsHTML += `<div class="${dotClass}"></div>`;
        }
        return dotsHTML;
    }

    updateGameStatistics() {
        if (!this.gameStatistics) return;
        
        const stats = this.gameStatistics;
        
        // Update stat values
        this.updateStatElement('totalRoundsPlayed', stats.total_rounds || stats.rounds_played || 0);
        this.updateStatElement('averageTime', this.formatTime(stats.average_time || stats.avg_reaction_time));
        this.updateStatElement('fastestTime', this.formatTime(stats.fastest_time || stats.best_time));
        this.updateStatElement('teamsEliminated', stats.teams_eliminated || stats.eliminated_count || 0);
    }

    updateStatElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    formatTime(timeMs) {
        if (timeMs === undefined || timeMs === null) return '—';
        return `${timeMs}ms`;
    }

    updateWinnerDisplay(data) {
        const winnerTeamElement = document.getElementById('winnerTeam');
        const winnerStatsElement = document.getElementById('winnerStats');
        
        if (winnerTeamElement && data.winner) {
            winnerTeamElement.textContent = data.winner.team_name || data.winner.name || `Team ${data.winner.team_id}`;
        }
        
        if (winnerStatsElement && data.winner) {
            const stats = [];
            if (data.winner.average_time) {
                stats.push(`Average time: ${data.winner.average_time}ms`);
            }
            if (data.winner.rounds_completed !== undefined) {
                stats.push(`Completed ${data.winner.rounds_completed} rounds`);
            }
            
            winnerStatsElement.textContent = stats.length > 0 ? 
                stats.join(' • ') : 
                'Congratulations on winning the game!';
        }
    }

    createConfetti() {
        const confettiContainer = document.getElementById('confetti');
        if (!confettiContainer) return;
        
        // Clear existing confetti
        confettiContainer.innerHTML = '';
        
        // Create confetti pieces
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti-piece';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.animationDelay = Math.random() * 3 + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
            confettiContainer.appendChild(confetti);
        }
    }

    handleContinue() {
        this.sendCommand('continue_game');
        this.hide();
    }

    handleNewGame() {
        this.sendCommand('start_new_game');
        this.hide();
    }

    handleBackToMenu() {
        this.sendCommand('navigate_to_menu');
        this.hide();
    }

    sendCommand(command, data = {}) {
        if (window.socketManager) {
            window.socketManager.emit(command, {
                timestamp: Date.now(),
                ...data
            });
        } else {
            console.error('SocketManager not available');
        }
    }

    show() {
        this.isVisible = true;
        this.element.classList.remove('results-display--hidden');
        this.element.style.display = 'block';
    }

    hide() {
        this.isVisible = false;
        this.element.classList.add('results-display--hidden');
    }

    // Public methods for external control
    showResults(type, data) {
        switch (type) {
            case 'round':
                this.showRoundResults(data);
                break;
            case 'game':
                this.showGameResults(data);
                break;
            case 'winner':
                this.showWinnerAnnouncement(data);
                break;
        }
    }

    clear() {
        this.currentResults = null;
        this.gameStatistics = null;
        this.hide();
    }

    isShown() {
        return this.isVisible;
    }

    destroy() {
        if (window.socketManager) {
            window.socketManager.off('round_complete');
            window.socketManager.off('game_results');
            window.socketManager.off('winner_announced');
            window.socketManager.off('statistics_update');
        }
    }
}
