class RoundProgressIndicator {
    constructor() {
        this.element = null;
        this.currentRoundElement = null;
        this.totalRoundsElement = null;
        this.phaseIndicator = null;
        this.phaseText = null;
        this.progressFill = null;
        this.progressText = null;
        this.timeLimitElement = null;
        this.remainingTeamsElement = null;
        this.roundTimerElement = null;
        this.statusMessage = null;
        
        this.currentRound = 0;
        this.totalRounds = 20;
        this.currentPhase = 'waiting';
        this.timeLimit = 200;
        this.remainingTeams = 0;
        this.roundStartTime = null;
        this.roundTimer = null;
        
        this.init();
    }

    init() {
        this.element = document.getElementById('roundProgressIndicator');
        this.currentRoundElement = document.getElementById('currentRound');
        this.totalRoundsElement = document.getElementById('totalRounds');
        this.phaseIndicator = document.getElementById('phaseIndicator');
        this.phaseText = document.getElementById('phaseText');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.timeLimitElement = document.getElementById('timeLimit');
        this.remainingTeamsElement = document.getElementById('remainingTeams');
        this.roundTimerElement = document.getElementById('roundTimer');
        this.statusMessage = document.getElementById('statusMessage');
        
        if (!this.element) {
            console.error('RoundProgressIndicator: Element not found');
            return;
        }

        this.setupEventListeners();
        this.updateDisplay();
    }

    setupEventListeners() {
        // WebSocket event listeners
        if (window.socketManager) {
            window.socketManager.on('round_progress_update', (data) => {
                this.handleRoundProgressUpdate(data);
            });

            window.socketManager.on('timing_config_update', (data) => {
                this.handleTimingConfigUpdate(data);
            });

            window.socketManager.on('game_phase_change', (data) => {
                this.handleGamePhaseChange(data);
            });

            window.socketManager.on('round_started', (data) => {
                this.handleRoundStarted(data);
            });

            window.socketManager.on('round_complete', (data) => {
                this.handleRoundComplete(data);
            });

            window.socketManager.on('game_started', (data) => {
                this.handleGameStarted(data);
            });

            window.socketManager.on('game_ended', (data) => {
                this.handleGameEnded(data);
            });

            window.socketManager.on('team_status_update', (data) => {
                this.handleTeamStatusUpdate(data);
            });
        }
    }

    handleRoundProgressUpdate(data) {
        if (data.round !== undefined) {
            this.setCurrentRound(data.round);
        }
        if (data.total_rounds !== undefined) {
            this.setTotalRounds(data.total_rounds);
        }
        if (data.remaining_teams !== undefined) {
            this.setRemainingTeams(data.remaining_teams);
        }
        if (data.phase !== undefined) {
            this.setPhase(data.phase);
        }
        if (data.time_limit_ms !== undefined) {
            this.setTimeLimit(data.time_limit_ms);
        }
        if (data.message) {
            this.setStatusMessage(data.message, data.message_type || 'info');
        }
    }

    handleTimingConfigUpdate(data) {
        if (data.time_limit_ms !== undefined) {
            this.setTimeLimit(data.time_limit_ms);
        }
        if (data.max_rounds !== undefined) {
            this.setTotalRounds(data.max_rounds);
        }
    }

    handleGamePhaseChange(data) {
        this.setPhase(data.phase);
        if (data.message) {
            this.setStatusMessage(data.message, data.message_type || 'info');
        }
    }

    handleRoundStarted(data) {
        if (data.round !== undefined) {
            this.setCurrentRound(data.round);
        }
        if (data.time_limit_ms !== undefined) {
            this.setTimeLimit(data.time_limit_ms);
        }
        if (data.active_teams !== undefined) {
            this.setRemainingTeams(data.active_teams.length);
        }
        
        this.setPhase('preparing');
        this.setStatusMessage(`Round ${data.round} starting...`, 'info');
        this.startRoundTimer();
    }

    handleRoundComplete(data) {
        this.setPhase('complete');
        this.stopRoundTimer();
        
        if (data.eliminated_teams && data.eliminated_teams.length > 0) {
            this.setStatusMessage(`Round complete - ${data.eliminated_teams.length} team(s) eliminated`, 'warning');
        } else {
            this.setStatusMessage('Round complete - All teams advanced', 'success');
        }
    }

    handleGameStarted(data) {
        this.setCurrentRound(0);
        this.setPhase('waiting');
        this.setStatusMessage('Game started - Preparing first round...', 'info');
        this.updateProgress();
    }

    handleGameEnded(data) {
        this.setPhase('complete');
        this.stopRoundTimer();
        
        if (data.winner) {
            this.setStatusMessage(`Game complete - Winner: ${data.winner.team_name || 'Team ' + data.winner.team_id}`, 'success');
        } else {
            this.setStatusMessage('Game complete', 'info');
        }
        
        // Set progress to 100%
        this.progressFill.style.width = '100%';
        this.progressFill.classList.add('round-progress-indicator__progress-fill--complete');
        this.progressText.textContent = '100%';
    }

    handleTeamStatusUpdate(data) {
        if (data.teams) {
            const activeTeams = data.teams.filter(team => !team.eliminated).length;
            this.setRemainingTeams(activeTeams);
        }
    }

    setCurrentRound(round) {
        if (this.currentRound !== round) {
            this.currentRound = round;
            this.currentRoundElement.textContent = round;
            this.currentRoundElement.classList.add('round-progress-indicator__current-round--updating');
            setTimeout(() => {
                this.currentRoundElement.classList.remove('round-progress-indicator__current-round--updating');
            }, 500);
            this.updateProgress();
        }
    }

    setTotalRounds(total) {
        this.totalRounds = total;
        this.totalRoundsElement.textContent = total;
        this.updateProgress();
    }

    setPhase(phase) {
        this.currentPhase = phase;
        
        // Update phase indicator
        this.phaseIndicator.className = 'round-progress-indicator__phase-indicator';
        this.phaseIndicator.classList.add(`round-progress-indicator__phase-indicator--${phase}`);
        
        // Update phase text
        const phaseTexts = {
            waiting: 'Waiting',
            preparing: 'Preparing',
            active: 'Active',
            complete: 'Complete'
        };
        this.phaseText.textContent = phaseTexts[phase] || phase;
    }

    setTimeLimit(timeLimitMs) {
        this.timeLimit = timeLimitMs;
        this.timeLimitElement.textContent = `${timeLimitMs}ms`;
        
        // Apply warning/danger styles based on time limit
        this.timeLimitElement.className = 'round-progress-indicator__timing-value';
        if (timeLimitMs <= 100) {
            this.timeLimitElement.classList.add('round-progress-indicator__timing-value--danger');
        } else if (timeLimitMs <= 150) {
            this.timeLimitElement.classList.add('round-progress-indicator__timing-value--warning');
        }
    }

    setRemainingTeams(count) {
        this.remainingTeams = count;
        this.remainingTeamsElement.textContent = count;
        
        // Apply warning styles if teams are getting low
        this.remainingTeamsElement.className = 'round-progress-indicator__timing-value';
        if (count <= 2) {
            this.remainingTeamsElement.classList.add('round-progress-indicator__timing-value--danger');
        } else if (count <= 4) {
            this.remainingTeamsElement.classList.add('round-progress-indicator__timing-value--warning');
        }
    }

    setStatusMessage(message, type = 'info') {
        this.statusMessage.textContent = message;
        this.statusMessage.className = 'round-progress-indicator__status-message';
        this.statusMessage.classList.add(`round-progress-indicator__status-message--${type}`);
    }

    updateProgress() {
        if (this.totalRounds > 0) {
            const percentage = Math.round((this.currentRound / this.totalRounds) * 100);
            this.progressFill.style.width = `${percentage}%`;
            this.progressText.textContent = `${percentage}%`;
        }
    }

    startRoundTimer() {
        this.roundStartTime = Date.now();
        this.roundTimer = setInterval(() => {
            this.updateRoundTimer();
        }, 100);
    }

    stopRoundTimer() {
        if (this.roundTimer) {
            clearInterval(this.roundTimer);
            this.roundTimer = null;
        }
    }

    updateRoundTimer() {
        if (this.roundStartTime) {
            const elapsed = Date.now() - this.roundStartTime;
            const seconds = (elapsed / 1000).toFixed(1);
            this.roundTimerElement.textContent = `${seconds}s`;
            
            // Add countdown animation every second
            if (elapsed % 1000 < 100) {
                this.roundTimerElement.classList.add('round-progress-indicator__timing-value--countdown');
                setTimeout(() => {
                    this.roundTimerElement.classList.remove('round-progress-indicator__timing-value--countdown');
                }, 500);
            }
        }
    }

    updateDisplay() {
        this.setCurrentRound(this.currentRound);
        this.setTotalRounds(this.totalRounds);
        this.setPhase(this.currentPhase);
        this.setTimeLimit(this.timeLimit);
        this.setRemainingTeams(this.remainingTeams);
        this.updateProgress();
    }

    // Public methods for external control
    reset() {
        this.setCurrentRound(0);
        this.setPhase('waiting');
        this.setStatusMessage('Ready to start game...', 'info');
        this.stopRoundTimer();
        this.roundTimerElement.textContent = '—';
        this.progressFill.style.width = '0%';
        this.progressFill.classList.remove('round-progress-indicator__progress-fill--complete', 'round-progress-indicator__progress-fill--danger');
        this.progressText.textContent = '0%';
    }

    getProgress() {
        return {
            currentRound: this.currentRound,
            totalRounds: this.totalRounds,
            phase: this.currentPhase,
            timeLimit: this.timeLimit,
            remainingTeams: this.remainingTeams
        };
    }

    destroy() {
        this.stopRoundTimer();
        
        if (window.socketManager) {
            window.socketManager.off('round_progress_update');
            window.socketManager.off('timing_config_update');
            window.socketManager.off('game_phase_change');
            window.socketManager.off('round_started');
            window.socketManager.off('round_complete');
            window.socketManager.off('game_started');
            window.socketManager.off('game_ended');
            window.socketManager.off('team_status_update');
        }
    }
}
