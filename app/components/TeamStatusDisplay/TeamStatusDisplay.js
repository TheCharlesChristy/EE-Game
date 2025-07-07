class TeamStatusDisplay {
    constructor() {
        this.container = null;
        this.grid = null;
        this.socket = null;
        this.teams = new Map();
        
        this.init();
    }

    init() {
        this.container = document.querySelector('.team-status-display');
        if (!this.container) {
            console.error('TeamStatusDisplay: Container not found');
            return;
        }

        this.grid = this.container.querySelector('.team-status-display__grid');
        this.setupSocketConnection();
    }

    setupSocketConnection() {
        // Listen for socket connection
        document.addEventListener('socketio_connected', () => {
            this.socket = window.socket;
            this.setupSocketHandlers();
            this.requestTeamData();
        });

        // If socket is already available
        if (window.socket) {
            this.socket = window.socket;
            this.setupSocketHandlers();
            this.requestTeamData();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        console.log('TeamStatusDisplay: Setting up socket handlers');

        // Listen for team data updates
        this.socket.on('reaction/team_data', (data) => {
            console.log('TeamStatusDisplay: Team data received:', data);
            this.updateTeamDisplay(data);
        });

        // Listen for individual team updates
        this.socket.on('reaction/team_update', (data) => {
            console.log('TeamStatusDisplay: Team update received:', data);
            if (data.team_id) {
                this.updateSingleTeam(data.team_id, data);
            }
        });

        // Request team data when game starts
        this.socket.on('game_started', () => {
            console.log('TeamStatusDisplay: Game started, requesting team data');
            this.requestTeamData();
        });
    }

    requestTeamData() {
        console.log('TeamStatusDisplay: Requesting team data from server');
        if (this.socket) {
            this.socket.emit('reaction/get_team_data', {});
            console.log('TeamStatusDisplay: Team data request sent');
        } else {
            console.error('TeamStatusDisplay: Socket not available for team data request');
        }
    }

    updateTeamDisplay(teamData) {
        if (!this.grid || !teamData) return;

        // Clear existing teams
        this.grid.innerHTML = '';
        this.teams.clear();

        // Create team elements for each team in the data
        Object.entries(teamData).forEach(([teamId, teamInfo]) => {
            this.createTeamElement(teamId, teamInfo);
        });
    }

    createTeamElement(teamId, teamInfo) {
        const teamElement = document.createElement('div');
        teamElement.className = 'team-status-display__team';
        teamElement.setAttribute('data-team', teamId);
        teamElement.setAttribute('data-status', teamInfo.status || 'active');
        teamElement.setAttribute('role', 'gridcell');

        // Create team header
        const header = document.createElement('div');
        header.className = 'team-status-display__team-header';

        const name = document.createElement('h3');
        name.className = 'team-status-display__team-name';
        name.textContent = teamInfo.name || `Team ${teamId}`;

        const status = document.createElement('span');
        status.className = 'team-status-display__team-status';
        status.textContent = this.getStatusText(teamInfo.status);

        header.appendChild(name);
        header.appendChild(status);

        // Create lives display
        const livesContainer = document.createElement('div');
        livesContainer.className = 'team-status-display__lives';
        livesContainer.setAttribute('role', 'img');
        livesContainer.setAttribute('aria-label', `${teamInfo.lives || 0} lives remaining`);

        // Add life indicators (assuming max 3 lives)
        const maxLives = 3;
        const currentLives = teamInfo.lives || 0;
        
        for (let i = 0; i < maxLives; i++) {
            const life = document.createElement('span');
            life.className = 'team-status-display__life';
            
            if (i < currentLives) {
                life.classList.add('team-status-display__life--active');
            } else {
                life.classList.add('team-status-display__life--lost');
            }
            
            life.textContent = '●';
            livesContainer.appendChild(life);
        }

        teamElement.appendChild(header);
        teamElement.appendChild(livesContainer);

        this.grid.appendChild(teamElement);
        this.teams.set(teamId, { element: teamElement, data: teamInfo });
    }

    updateSingleTeam(teamId, updateData) {
        const teamData = this.teams.get(teamId);
        if (!teamData) return;

        const { element, data } = teamData;

        // Update status
        if (updateData.status) {
            data.status = updateData.status;
            element.setAttribute('data-status', updateData.status);
            
            const statusElement = element.querySelector('.team-status-display__team-status');
            if (statusElement) {
                statusElement.textContent = this.getStatusText(updateData.status);
            }
        }

        // Update lives
        if (updateData.lives !== undefined) {
            data.lives = updateData.lives;
            
            const livesContainer = element.querySelector('.team-status-display__lives');
            if (livesContainer) {
                livesContainer.setAttribute('aria-label', `${updateData.lives} lives remaining`);
                
                // Update life indicators
                const lifeElements = livesContainer.querySelectorAll('.team-status-display__life');
                lifeElements.forEach((life, index) => {
                    life.classList.remove('team-status-display__life--active', 'team-status-display__life--lost');
                    
                    if (index < updateData.lives) {
                        life.classList.add('team-status-display__life--active');
                    } else {
                        life.classList.add('team-status-display__life--lost');
                    }
                });
            }
        }

        // Update the stored data
        this.teams.set(teamId, { element, data });
    }

    getStatusText(status) {
        switch (status) {
            case 'active':
                return 'Active';
            case 'eliminated':
                return 'Eliminated';
            case 'winner':
                return 'Winner';
            case 'inactive':
                return 'Inactive';
            default:
                return 'Unknown';
        }
    }

    getTeamData(teamId) {
        const teamData = this.teams.get(teamId);
        return teamData ? teamData.data : null;
    }

    getAllTeamsData() {
        const allData = {};
        this.teams.forEach((value, key) => {
            allData[key] = value.data;
        });
        return allData;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.teamStatusDisplay = new TeamStatusDisplay();
    });
} else {
    window.teamStatusDisplay = new TeamStatusDisplay();
}