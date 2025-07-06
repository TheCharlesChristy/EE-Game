class TeamStatusDisplay {
    constructor() {
        this.element = null;
        this.gridElement = null;
        this.activeTeamsElement = null;
        this.teams = new Map();
        this.maxLives = 3;
        this.init();
    }

    init() {
        this.element = document.getElementById('teamStatusDisplay');
        this.gridElement = document.getElementById('teamStatusGrid');
        this.activeTeamsElement = document.getElementById('activeTeamsCount');
        
        if (!this.element) {
            console.error('TeamStatusDisplay: Element not found');
            return;
        }

        this.setupEventListeners();
        this.loadInitialTeams();
    }

    setupEventListeners() {
        // Listen for WebSocket events
        if (window.socketManager) {
            window.socketManager.on('team_status_update', (data) => {
                this.handleTeamStatusUpdate(data);
            });

            window.socketManager.on('lives_changed', (data) => {
                this.handleLivesChanged(data);
            });

            window.socketManager.on('team_eliminated', (data) => {
                this.handleTeamEliminated(data);
            });

            window.socketManager.on('round_results', (data) => {
                this.handleRoundResults(data);
            });

            window.socketManager.on('button_press', (data) => {
                this.handleButtonPress(data);
            });

            window.socketManager.on('led_status_update', (data) => {
                this.handleLEDStatusUpdate(data);
            });

            window.socketManager.on('game_started', (data) => {
                this.handleGameStarted(data);
            });

            window.socketManager.on('game_ended', (data) => {
                this.handleGameEnded(data);
            });
        }
    }

    loadInitialTeams() {
        // Request current team data
        if (window.socketManager) {
            window.socketManager.emit('request_team_status');
        }
    }

    handleTeamStatusUpdate(data) {
        if (data.teams) {
            data.teams.forEach(team => {
                this.updateTeam(team);
            });
        } else if (data.team_id) {
            this.updateTeam(data);
        }
        this.updateActiveTeamsCount();
    }

    handleLivesChanged(data) {
        const team = this.teams.get(data.team_id);
        if (team) {
            team.lives = data.lives;
            team.eliminated = data.lives <= 0;
            this.updateTeamCard(data.team_id);
            this.updateActiveTeamsCount();
        }
    }

    handleTeamEliminated(data) {
        const team = this.teams.get(data.team_id);
        if (team) {
            team.eliminated = true;
            team.lives = 0;
            this.updateTeamCard(data.team_id);
            this.updateActiveTeamsCount();
        }
    }

    handleRoundResults(data) {
        if (data.results) {
            data.results.forEach(result => {
                const team = this.teams.get(result.team_id);
                if (team) {
                    team.lastReactionTime = result.reaction_time;
                    team.buttonPressed = result.pressed;
                    team.roundsCompleted = (team.roundsCompleted || 0) + 1;
                    this.updateTeamCard(result.team_id);
                }
            });
        }
    }

    handleButtonPress(data) {
        const team = this.teams.get(data.team_id);
        if (team) {
            team.lastReactionTime = data.reaction_time_ms;
            team.buttonPressed = true;
            this.updateTeamCard(data.team_id);
            this.animateButtonPress(data.team_id);
        }
    }

    handleLEDStatusUpdate(data) {
        if (data.teams) {
            data.teams.forEach(teamStatus => {
                const team = this.teams.get(teamStatus.team_id);
                if (team) {
                    team.ledStatus = teamStatus.led_status;
                    this.updateTeamCard(teamStatus.team_id);
                }
            });
        } else if (data.team_id) {
            const team = this.teams.get(data.team_id);
            if (team) {
                team.ledStatus = data.led_status;
                this.updateTeamCard(data.team_id);
            }
        }
    }

    handleGameStarted(data) {
        // Reset all team states for new game
        data.teams.forEach(teamId => {
            const team = this.teams.get(teamId);
            if (team) {
                team.lives = this.maxLives;
                team.eliminated = false;
                team.buttonPressed = false;
                team.lastReactionTime = null;
                team.roundsCompleted = 0;
                this.updateTeamCard(teamId);
            }
        });
        this.updateActiveTeamsCount();
    }

    handleGameEnded(data) {
        // Mark winner and update final standings
        if (data.winner && data.winner.team_id) {
            const winnerTeam = this.teams.get(data.winner.team_id);
            if (winnerTeam) {
                winnerTeam.isWinner = true;
                this.updateTeamCard(data.winner.team_id);
            }
        }
    }

    updateTeam(teamData) {
        this.teams.set(teamData.team_id, {
            id: teamData.team_id,
            name: teamData.name || `Team ${teamData.team_id}`,
            lives: teamData.lives !== undefined ? teamData.lives : this.maxLives,
            eliminated: teamData.eliminated || false,
            buttonPressed: teamData.button_pressed || false,
            lastReactionTime: teamData.last_reaction_time || null,
            ledStatus: teamData.led_status || 'off',
            roundsCompleted: teamData.rounds_completed || 0,
            isWinner: teamData.is_winner || false
        });
        
        this.renderTeamCard(teamData.team_id);
    }

    renderTeamCard(teamId) {
        const team = this.teams.get(teamId);
        if (!team) return;

        let card = document.getElementById(`team-card-${teamId}`);
        if (!card) {
            card = document.createElement('div');
            card.id = `team-card-${teamId}`;
            card.className = 'team-status-card';
            this.gridElement.appendChild(card);
        }

        // Update card classes
        card.className = 'team-status-card';
        if (!team.eliminated) {
            card.classList.add('team-status-card--active');
        } else {
            card.classList.add('team-status-card--eliminated');
        }
        if (team.buttonPressed) {
            card.classList.add('team-status-card--pressed');
        }

        card.innerHTML = `
            <div class="team-status-card__header">
                <h4 class="team-status-card__name">${team.name}</h4>
                <span class="team-status-card__id">Team ${team.id}</span>
            </div>
            
            <div class="team-status-card__status">
                <div class="team-status-display__status-indicator ${this.getStatusIndicatorClass(team)}"></div>
                <span class="team-status-card__status-text ${this.getStatusTextClass(team)}">
                    ${this.getStatusText(team)}
                </span>
            </div>
            
            <div class="team-status-card__lives">
                <span class="team-status-card__lives-label">Lives:</span>
                <div class="team-status-card__lives-dots">
                    ${this.renderLivesDots(team.lives)}
                </div>
            </div>
            
            <div class="team-status-card__metrics">
                <div class="team-status-card__metric">
                    <span class="team-status-card__metric-value">
                        ${team.lastReactionTime ? `${team.lastReactionTime}ms` : '—'}
                    </span>
                    <span class="team-status-card__metric-label">Last Time</span>
                </div>
                <div class="team-status-card__metric">
                    <span class="team-status-card__metric-value">${team.roundsCompleted}</span>
                    <span class="team-status-card__metric-label">Rounds</span>
                </div>
            </div>
            
            <div class="team-status-card__led-status ${this.getLEDStatusClass(team)}"></div>
        `;
    }

    updateTeamCard(teamId) {
        this.renderTeamCard(teamId);
    }

    getStatusIndicatorClass(team) {
        if (team.eliminated) return 'team-status-display__status-indicator--eliminated';
        if (team.buttonPressed) return 'team-status-display__status-indicator--active';
        return 'team-status-display__status-indicator--waiting';
    }

    getStatusTextClass(team) {
        if (team.eliminated) return 'team-status-card__status-text--eliminated';
        if (team.buttonPressed) return 'team-status-card__status-text--active';
        return 'team-status-card__status-text--waiting';
    }

    getStatusText(team) {
        if (team.isWinner) return 'WINNER!';
        if (team.eliminated) return 'Eliminated';
        if (team.buttonPressed) return 'Button Pressed';
        return 'Waiting';
    }

    getLEDStatusClass(team) {
        const baseClass = 'team-status-card__led-status';
        switch (team.ledStatus) {
            case 'on':
                return `${baseClass} team-status-card__led-status--on`;
            case 'flashing':
                return `${baseClass} team-status-card__led-status--on team-status-card__led-status--flashing`;
            default:
                return `${baseClass} team-status-card__led-status--off`;
        }
    }

    renderLivesDots(livesCount) {
        let dots = '';
        for (let i = 0; i < this.maxLives; i++) {
            const lifeClass = i < livesCount ? 
                'team-status-display__life team-status-display__life--active' : 
                'team-status-display__life team-status-display__life--lost';
            dots += `<div class="${lifeClass}"></div>`;
        }
        return dots;
    }

    animateButtonPress(teamId) {
        const card = document.getElementById(`team-card-${teamId}`);
        if (card) {
            card.classList.add('team-status-card--button-pressed');
            setTimeout(() => {
                card.classList.remove('team-status-card--button-pressed');
            }, 300);
        }
    }

    updateActiveTeamsCount() {
        const activeCount = Array.from(this.teams.values()).filter(team => !team.eliminated).length;
        const totalCount = this.teams.size;
        this.activeTeamsElement.textContent = `${activeCount}/${totalCount} teams active`;
    }

    clearAllTeams() {
        this.teams.clear();
        this.gridElement.innerHTML = '';
        this.updateActiveTeamsCount();
    }

    // Public methods for external control
    setMaxLives(maxLives) {
        this.maxLives = maxLives;
        // Re-render all cards to update lives display
        this.teams.forEach((team, teamId) => {
            this.renderTeamCard(teamId);
        });
    }

    getTeamData() {
        return Array.from(this.teams.values());
    }

    destroy() {
        if (window.socketManager) {
            window.socketManager.off('team_status_update');
            window.socketManager.off('lives_changed');
            window.socketManager.off('team_eliminated');
            window.socketManager.off('round_results');
            window.socketManager.off('button_press');
            window.socketManager.off('led_status_update');
            window.socketManager.off('game_started');
            window.socketManager.off('game_ended');
        }
    }
}
