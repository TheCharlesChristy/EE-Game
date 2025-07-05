class SystemReadinessIndicator {
  constructor() {
    this.element = null;
    this.statusElement = null;
    this.messageElement = null;
    this.checklistItems = null;
    this.blockingIssuesContainer = null;
    this.issuesList = null;
    
    this.state = {
      isReady: false,
      teamCount: 0,
      minTeams: 2,
      hardwareStatusCount: { connected: 0, total: 0 },
      pinAssignmentsValid: true,
      blockingIssues: []
    };
    
    this.init();
  }

  init() {
    this.element = document.querySelector('.system-readiness-indicator');
    if (!this.element) return;
    
    this.statusElement = this.element.querySelector('.status-indicator');
    this.messageElement = this.element.querySelector('.status-message');
    this.checklistItems = this.element.querySelectorAll('.checklist-item');
    this.blockingIssuesContainer = this.element.querySelector('.blocking-issues');
    this.issuesList = this.element.querySelector('.issues-list');
    
    this.setupEventListeners();
    this.updateDisplay();
  }

  setupEventListeners() {
    // Listen for team registration events
    document.addEventListener('team_registered', (event) => {
      this.state.teamCount = event.detail.totalTeams || 0;
      this.updateDisplay();
    });
    
    document.addEventListener('team_removed', (event) => {
      this.state.teamCount = event.detail.totalTeams || 0;
      this.updateDisplay();
    });
    
    // Listen for hardware status changes
    document.addEventListener('hardware_status_changed', (event) => {
      this.state.hardwareStatusCount = event.detail.statusCount || { connected: 0, total: 0 };
      this.updateDisplay();
    });
    
    // Listen for GPIO pin validation changes
    document.addEventListener('pin_availability_changed', (event) => {
      this.state.pinAssignmentsValid = event.detail.allValid || true;
      this.updateDisplay();
    });
  }

  updateDisplay() {
    this.updateChecklist();
    this.updateOverallStatus();
    this.updateBlockingIssues();
    this.emitReadinessEvent();
  }

  updateChecklist() {
    // Update teams requirement
    const teamsItem = this.element.querySelector('[data-requirement="teams"]');
    const teamsStatus = teamsItem.querySelector('.check-status');
    const teamsComplete = this.state.teamCount >= this.state.minTeams;
    
    teamsStatus.textContent = `${this.state.teamCount}/${this.state.minTeams}`;
    teamsItem.classList.toggle('complete', teamsComplete);
    teamsItem.classList.toggle('incomplete', !teamsComplete);
    
    // Update hardware requirement
    const hardwareItem = this.element.querySelector('[data-requirement="hardware"]');
    const hardwareStatus = hardwareItem.querySelector('.check-status');
    const hardwareComplete = this.state.hardwareStatusCount.total > 0 && 
                            this.state.hardwareStatusCount.connected === this.state.hardwareStatusCount.total;
    
    hardwareStatus.textContent = `${this.state.hardwareStatusCount.connected}/${this.state.hardwareStatusCount.total}`;
    hardwareItem.classList.toggle('complete', hardwareComplete);
    hardwareItem.classList.toggle('incomplete', this.state.hardwareStatusCount.total > 0 && !hardwareComplete);
    
    // Update pins requirement
    const pinsItem = this.element.querySelector('[data-requirement="pins"]');
    const pinsStatus = pinsItem.querySelector('.check-status');
    
    pinsStatus.textContent = this.state.pinAssignmentsValid ? 'Valid' : 'Invalid';
    pinsItem.classList.toggle('complete', this.state.pinAssignmentsValid);
    pinsItem.classList.toggle('incomplete', !this.state.pinAssignmentsValid);
  }

  updateOverallStatus() {
    const teamsReady = this.state.teamCount >= this.state.minTeams;
    const hardwareReady = this.state.hardwareStatusCount.total === 0 || 
                         this.state.hardwareStatusCount.connected === this.state.hardwareStatusCount.total;
    const pinsReady = this.state.pinAssignmentsValid;
    
    this.state.isReady = teamsReady && hardwareReady && pinsReady;
    
    // Update visual state
    this.element.classList.remove('ready', 'blocked', 'checking');
    
    if (this.state.isReady) {
      this.element.classList.add('ready');
      this.messageElement.textContent = 'System ready for gameplay!';
    } else {
      this.element.classList.add('blocked');
      this.messageElement.textContent = 'System not ready - see requirements below';
    }
  }

  updateBlockingIssues() {
    this.state.blockingIssues = [];
    
    if (this.state.teamCount < this.state.minTeams) {
      this.state.blockingIssues.push(`Need ${this.state.minTeams - this.state.teamCount} more team(s)`);
    }
    
    if (this.state.hardwareStatusCount.total > 0 && 
        this.state.hardwareStatusCount.connected < this.state.hardwareStatusCount.total) {
      const disconnected = this.state.hardwareStatusCount.total - this.state.hardwareStatusCount.connected;
      this.state.blockingIssues.push(`${disconnected} hardware connection(s) failed`);
    }
    
    if (!this.state.pinAssignmentsValid) {
      this.state.blockingIssues.push('GPIO pin assignments have conflicts');
    }
    
    // Show/hide blocking issues section
    if (this.state.blockingIssues.length > 0) {
      this.blockingIssuesContainer.style.display = 'block';
      this.issuesList.innerHTML = this.state.blockingIssues
        .map(issue => `<li>${issue}</li>`)
        .join('');
    } else {
      this.blockingIssuesContainer.style.display = 'none';
    }
  }

  emitReadinessEvent() {
    const event = new CustomEvent('system_ready_changed', {
      detail: {
        isReady: this.state.isReady,
        teamCount: this.state.teamCount,
        blockingIssues: this.state.blockingIssues,
        requirements: {
          teams: this.state.teamCount >= this.state.minTeams,
          hardware: this.state.hardwareStatusCount.total === 0 || 
                   this.state.hardwareStatusCount.connected === this.state.hardwareStatusCount.total,
          pins: this.state.pinAssignmentsValid
        }
      },
      bubbles: true
    });
    
    this.element.dispatchEvent(event);
  }

  // Public API methods
  setTeamCount(count) {
    this.state.teamCount = count;
    this.updateDisplay();
  }

  setHardwareStatus(connected, total) {
    this.state.hardwareStatusCount = { connected, total };
    this.updateDisplay();
  }

  setPinValidation(isValid) {
    this.state.pinAssignmentsValid = isValid;
    this.updateDisplay();
  }

  getReadinessState() {
    return {
      isReady: this.state.isReady,
      teamCount: this.state.teamCount,
      blockingIssues: [...this.state.blockingIssues]
    };
  }
}
