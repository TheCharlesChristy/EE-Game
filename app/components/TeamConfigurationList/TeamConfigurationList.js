class TeamConfigurationList {
  constructor() {
    this.element = null;
    this.teamCountElement = null;
    this.noTeamsMessage = null;
    this.teamsList = null;
    
    this.teams = new Map();
    this.teamColors = [
      'var(--team-1-red)',
      'var(--team-2-blue)', 
      'var(--team-3-green)',
      'var(--team-4-yellow)',
      'var(--team-5-purple)',
      'var(--team-6-orange)',
      'var(--team-7-pink)',
      'var(--team-8-brown)'
    ];
    
    this.init();
  }

  init() {
    this.element = document.querySelector('.team-configuration-list');
    if (!this.element) return;
    
    this.teamCountElement = this.element.querySelector('.team-count');
    this.noTeamsMessage = this.element.querySelector('.no-teams-message');
    this.teamsList = this.element.querySelector('.teams-list');
    
    this.setupEventListeners();
    this.updateDisplay();
  }

  setupEventListeners() {
    // Listen for team registration/removal events
    document.addEventListener('team_registered', (event) => {
      this.addTeam(event.detail);
    });
    
    document.addEventListener('team_removed', (event) => {
      this.removeTeam(event.detail.teamId);
    });
    
    document.addEventListener('team_updated', (event) => {
      this.updateTeam(event.detail);
    });
    
    // Listen for hardware status updates
    document.addEventListener('hardware_status_changed', (event) => {
      this.updateHardwareStatus(event.detail);
    });
    
    document.addEventListener('circuit_test_result', (event) => {
      this.updateTeamTestStatus(event.detail);
    });
  }

  addTeam(teamData) {
    const team = {
      id: teamData.id || this.generateTeamId(),
      name: teamData.name,
      pins: teamData.pins || [],
      color: this.getTeamColor(this.teams.size),
      status: 'disconnected',
      testing: false,
      ...teamData
    };
    
    this.teams.set(team.id, team);
    this.updateDisplay();
    this.emitTeamCountEvent();
  }

  removeTeam(teamId) {
    if (this.teams.has(teamId)) {
      this.teams.delete(teamId);
      this.updateDisplay();
      this.emitTeamCountEvent();
    }
  }

  updateTeam(teamData) {
    if (this.teams.has(teamData.id)) {
      const existingTeam = this.teams.get(teamData.id);
      this.teams.set(teamData.id, { ...existingTeam, ...teamData });
      this.updateDisplay();
    }
  }

  updateHardwareStatus(statusData) {
    // Update team statuses based on hardware status
    for (const [teamId, team] of this.teams) {
      if (team.pins && team.pins.length > 0) {
        const allConnected = team.pins.every(pin => 
          statusData.pinStatuses && statusData.pinStatuses[pin] === 'connected'
        );
        team.status = allConnected ? 'connected' : 'disconnected';
      }
    }
    this.updateDisplay();
  }

  updateTeamTestStatus(testResult) {
    const team = this.teams.get(testResult.teamId);
    if (team) {
      team.testing = false;
      team.lastTestResult = testResult;
      team.status = testResult.success ? 'connected' : 'disconnected';
      this.updateDisplay();
    }
  }

  updateDisplay() {
    this.updateTeamCount();
    this.updateTeamsList();
  }

  updateTeamCount() {
    const count = this.teams.size;
    this.teamCountElement.textContent = `${count} team${count !== 1 ? 's' : ''}`;
  }

  updateTeamsList() {
    if (this.teams.size === 0) {
      this.noTeamsMessage.style.display = 'block';
      this.teamsList.style.display = 'none';
      return;
    }
    
    this.noTeamsMessage.style.display = 'none';
    this.teamsList.style.display = 'block';
    
    // Clear existing items
    this.teamsList.innerHTML = '';
    
    // Add team items
    Array.from(this.teams.values())
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach(team => {
        const teamElement = this.createTeamElement(team);
        this.teamsList.appendChild(teamElement);
      });
  }

  createTeamElement(team) {
    const teamItem = document.createElement('div');
    teamItem.className = 'team-item';
    teamItem.dataset.teamId = team.id;
    
    teamItem.innerHTML = `
      <div class="team-color-indicator" style="background-color: ${team.color}"></div>
      <div class="team-info">
        <div class="team-name">${this.escapeHtml(team.name)}</div>
        <div class="team-details">
          <div class="team-pin">Pin: ${team.pins.join(', ') || 'None'}</div>
          <div class="team-status">
            <span class="status-indicator ${team.status}"></span>
            <span>${this.getStatusText(team)}</span>
          </div>
        </div>
      </div>
      <div class="team-actions">
        <button type="button" class="action-btn edit" title="Edit Team" data-action="edit">
          ✏️
        </button>
        <button type="button" class="action-btn delete" title="Remove Team" data-action="delete">
          🗑️
        </button>
      </div>
    `;
    
    // Add event listeners to action buttons
    const editBtn = teamItem.querySelector('[data-action="edit"]');
    const deleteBtn = teamItem.querySelector('[data-action="delete"]');
    
    editBtn.addEventListener('click', () => this.editTeam(team.id));
    deleteBtn.addEventListener('click', () => this.confirmDeleteTeam(team.id));
    
    return teamItem;
  }

  getStatusText(team) {
    if (team.testing) return 'Testing...';
    
    switch (team.status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  }

  editTeam(teamId) {
    const event = new CustomEvent('edit_team_requested', {
      detail: {
        teamId: teamId,
        team: this.teams.get(teamId)
      },
      bubbles: true
    });
    this.element.dispatchEvent(event);
  }

  confirmDeleteTeam(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return;
    
    const confirmed = confirm(`Are you sure you want to remove team "${team.name}"?`);
    if (confirmed) {
      this.removeTeam(teamId);
      
      // Emit removal event
      const event = new CustomEvent('team_removed', {
        detail: {
          teamId: teamId,
          totalTeams: this.teams.size
        },
        bubbles: true
      });
      this.element.dispatchEvent(event);
    }
  }

  emitTeamCountEvent() {
    const event = new CustomEvent('team_count_changed', {
      detail: {
        count: this.teams.size,
        teams: Array.from(this.teams.values())
      },
      bubbles: true
    });
    this.element.dispatchEvent(event);
  }

  getTeamColor(index) {
    return this.teamColors[index % this.teamColors.length];
  }

  generateTeamId() {
    return 'team_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API methods
  getTeams() {
    return Array.from(this.teams.values());
  }

  getTeamCount() {
    return this.teams.size;
  }

  getTeam(teamId) {
    return this.teams.get(teamId);
  }

  setTeamTesting(teamId, testing = true) {
    const team = this.teams.get(teamId);
    if (team) {
      team.testing = testing;
      this.updateDisplay();
    }
  }

  clearAllTeams() {
    this.teams.clear();
    this.updateDisplay();
    this.emitTeamCountEvent();
  }
}
