class TeamRegistrationForm {
  constructor() {
    this.element = null;
    this.form = null;
    this.teamNameInput = null;
    this.submitButton = null;
    this.cancelButton = null;
    this.currentCountElement = null;
    this.colorCircle = null;
    this.colorName = null;
    this.inputFeedback = null;
    this.limitReachedSection = null;
    this.pinSelector = null;
    
    this.state = {
      isEditMode: false,
      editingTeamId: null,
      currentTeamCount: 0,
      maxTeams: 8,
      selectedPins: [],
      isValid: false,
      teamNames: new Set(),
      teamColors: [
        { color: 'var(--team-1-red)', name: 'Red' },
        { color: 'var(--team-2-blue)', name: 'Blue' },
        { color: 'var(--team-3-green)', name: 'Green' },
        { color: 'var(--team-4-yellow)', name: 'Yellow' },
        { color: 'var(--team-5-purple)', name: 'Purple' },
        { color: 'var(--team-6-orange)', name: 'Orange' },
        { color: 'var(--team-7-pink)', name: 'Pink' },
        { color: 'var(--team-8-brown)', name: 'Brown' }
      ]
    };
    
    this.init();
  }

  init() {
    this.element = document.querySelector('.team-registration-form');
    if (!this.element) return;
    
    this.form = this.element.querySelector('.registration-form');
    this.teamNameInput = this.element.querySelector('#teamName');
    this.submitButton = this.element.querySelector('button[type="submit"]');
    this.cancelButton = this.element.querySelector('.cancel-btn');
    this.currentCountElement = this.element.querySelector('.current-count');
    this.colorCircle = this.element.querySelector('.color-circle');
    this.colorName = this.element.querySelector('.color-name');
    this.inputFeedback = this.element.querySelector('.input-feedback');
    this.limitReachedSection = this.element.querySelector('.form-limit-reached');
    
    this.initializePinSelector();
    this.setupEventListeners();
    this.updateDisplay();
  }

  initializePinSelector() {
    const container = this.element.querySelector('.gpio-pin-selector-container');
    if (container) {
      // Inject GPIO Pin Selector HTML
      container.innerHTML = `
        <div class="gpio-pin-selector">
          <div class="pin-selector-header">
            <label class="pin-selector-label">GPIO Pin Assignment</label>
            <div class="pin-availability-indicator">
              <span class="available-count">0</span> available pins
            </div>
          </div>
          
          <div class="pin-selection-mode">
            <div class="selection-tabs">
              <button type="button" class="tab-btn active" data-mode="dropdown">
                📋 Dropdown
              </button>
              <button type="button" class="tab-btn" data-mode="visual">
                🔌 Visual Layout
              </button>
            </div>
          </div>
          
          <div class="pin-input-container">
            <div class="dropdown-mode active">
              <select class="pin-dropdown" name="selectedPin">
                <option value="">Select a GPIO pin...</option>
              </select>
              <div class="pin-conflict-warning" style="display: none;">
                ⚠️ This pin is already assigned to another team
              </div>
            </div>
            
            <div class="visual-mode">
              <div class="gpio-layout">
                <div class="gpio-board">
                  <div class="board-header">Raspberry Pi GPIO Layout</div>
                  <div class="pin-grid"></div>
                </div>
              </div>
              <div class="pin-legend">
                <div class="legend-item">
                  <span class="legend-color available"></span>
                  <span>Available</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color used"></span>
                  <span>Used by Other Team</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color selected"></span>
                  <span>Selected for This Team</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color reserved"></span>
                  <span>System Reserved</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="selected-pins-display">
            <div class="selected-pins-header">Selected Pin:</div>
            <div class="selected-pins-list">
              <span class="no-selection">None selected</span>
            </div>
          </div>
        </div>
      `;
      
      // Initialize the pin selector
      this.pinSelector = new GPIOPinSelector('.gpio-pin-selector-container .gpio-pin-selector', {
        allowMultiple: false,
        teamId: this.state.editingTeamId
      });
    }
  }

  setupEventListeners() {
    // Form submission
    this.form.addEventListener('submit', (event) => {
      event.preventDefault();
      this.handleSubmit();
    });
    
    // Team name input validation
    this.teamNameInput.addEventListener('input', () => {
      this.validateTeamName();
      this.updateSubmitButton();
    });
    
    this.teamNameInput.addEventListener('blur', () => {
      this.validateTeamName();
    });
    
    // Cancel button
    this.cancelButton.addEventListener('click', () => {
      this.cancelEdit();
    });
    
    // Pin selection events
    document.addEventListener('pin_selected', (event) => {
      this.state.selectedPins = event.detail.selectedPins;
      this.updateSubmitButton();
    });
    
    // Team count updates
    document.addEventListener('team_count_changed', (event) => {
      this.state.currentTeamCount = event.detail.count;
      this.state.teamNames = new Set(event.detail.teams.map(team => team.name.toLowerCase()));
      this.updateDisplay();
      this.updateTeamColor();
    });
    
    // Edit team requests
    document.addEventListener('edit_team_requested', (event) => {
      this.editTeam(event.detail.team);
    });
  }

  validateTeamName() {
    const name = this.teamNameInput.value.trim();
    let isValid = true;
    let message = '';
    
    // Clear previous validation state
    this.teamNameInput.classList.remove('valid', 'invalid');
    this.inputFeedback.classList.remove('success', 'error');
    
    if (name === '') {
      message = '';
      isValid = false;
    } else if (name.length < 2) {
      message = 'Team name must be at least 2 characters long';
      isValid = false;
    } else if (name.length > 50) {
      message = 'Team name must be less than 50 characters';
      isValid = false;
    } else if (!/^[a-zA-Z0-9\s\-_]+$/.test(name)) {
      message = 'Team name can only contain letters, numbers, spaces, hyphens, and underscores';
      isValid = false;
    } else if (this.state.teamNames.has(name.toLowerCase()) && 
               (!this.state.isEditMode || this.getEditingTeamName() !== name)) {
      message = 'This team name is already taken';
      isValid = false;
    } else {
      message = 'Team name looks good!';
      isValid = true;
    }
    
    // Update UI
    if (name !== '') {
      this.teamNameInput.classList.add(isValid ? 'valid' : 'invalid');
      this.inputFeedback.classList.add(isValid ? 'success' : 'error');
    }
    
    this.inputFeedback.textContent = message;
    this.state.isValid = isValid && name !== '';
    
    return isValid;
  }

  updateSubmitButton() {
    const nameValid = this.validateTeamName();
    const pinValid = this.state.selectedPins.length > 0;
    const canSubmit = nameValid && pinValid;
    
    this.submitButton.disabled = !canSubmit;
    this.submitButton.textContent = this.state.isEditMode ? 'Update Team' : 'Add Team';
    
    if (canSubmit) {
      this.form.classList.add('valid');
    } else {
      this.form.classList.remove('valid');
    }
  }

  updateDisplay() {
    // Update team count
    this.currentCountElement.textContent = this.state.currentTeamCount;
    
    // Update count styling
    this.currentCountElement.classList.remove('warning', 'limit');
    if (this.state.currentTeamCount >= this.state.maxTeams - 1) {
      this.currentCountElement.classList.add('warning');
    }
    if (this.state.currentTeamCount >= this.state.maxTeams) {
      this.currentCountElement.classList.add('limit');
    }
    
    // Show/hide form based on team limit
    const isAtLimit = this.state.currentTeamCount >= this.state.maxTeams && !this.state.isEditMode;
    this.form.style.display = isAtLimit ? 'none' : 'block';
    this.limitReachedSection.style.display = isAtLimit ? 'block' : 'none';
  }

  updateTeamColor() {
    const teamIndex = this.state.isEditMode ? 
      this.getEditingTeamIndex() : 
      this.state.currentTeamCount;
    
    const colorInfo = this.state.teamColors[teamIndex % this.state.teamColors.length];
    
    this.colorCircle.style.backgroundColor = colorInfo.color;
    this.colorName.textContent = colorInfo.name;
  }

  handleSubmit() {
    if (!this.state.isValid || this.state.selectedPins.length === 0) return;
    
    this.form.classList.add('loading');
    this.submitButton.disabled = true;
    
    const teamData = {
      id: this.state.editingTeamId || this.generateTeamId(),
      name: this.teamNameInput.value.trim(),
      pins: [...this.state.selectedPins],
      color: this.colorCircle.style.backgroundColor || this.state.teamColors[0].color,
      colorName: this.colorName.textContent
    };
    
    // Simulate API call delay
    setTimeout(() => {
      this.form.classList.remove('loading');
      
      if (this.state.isEditMode) {
        this.handleTeamUpdate(teamData);
      } else {
        this.handleTeamRegistration(teamData);
      }
      
      this.resetForm();
    }, 500);
  }

  handleTeamRegistration(teamData) {
    const event = new CustomEvent('team_registered', {
      detail: {
        ...teamData,
        totalTeams: this.state.currentTeamCount + 1
      },
      bubbles: true
    });
    
    this.element.dispatchEvent(event);
    
    // Reserve the pin
    if (this.pinSelector) {
      this.pinSelector.reservePin(teamData.pins[0], teamData.id);
    }
  }

  handleTeamUpdate(teamData) {
    const event = new CustomEvent('team_updated', {
      detail: teamData,
      bubbles: true
    });
    
    this.element.dispatchEvent(event);
    
    // Update pin reservation
    if (this.pinSelector) {
      this.pinSelector.reservePin(teamData.pins[0], teamData.id);
    }
  }

  editTeam(team) {
    this.state.isEditMode = true;
    this.state.editingTeamId = team.id;
    
    // Populate form with team data
    this.teamNameInput.value = team.name;
    this.state.selectedPins = team.pins ? [...team.pins] : [];
    
    // Update pin selector
    if (this.pinSelector) {
      this.pinSelector.setTeamId(team.id);
      this.pinSelector.setSelectedPins(this.state.selectedPins);
    }
    
    // Update UI
    this.element.classList.add('edit-mode');
    this.updateTeamColor();
    this.updateSubmitButton();
    this.validateTeamName();
    
    // Scroll to form
    this.element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  cancelEdit() {
    this.resetForm();
    this.element.classList.remove('edit-mode');
  }

  resetForm() {
    this.state.isEditMode = false;
    this.state.editingTeamId = null;
    this.state.selectedPins = [];
    
    this.form.reset();
    this.teamNameInput.classList.remove('valid', 'invalid');
    this.inputFeedback.textContent = '';
    this.inputFeedback.classList.remove('success', 'error');
    this.form.classList.remove('valid', 'loading');
    this.submitButton.disabled = true;
    this.element.classList.remove('edit-mode');
    
    if (this.pinSelector) {
      this.pinSelector.clear();
      this.pinSelector.setTeamId(null);
    }
    
    this.updateTeamColor();
  }

  generateTeamId() {
    return 'team_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  getEditingTeamName() {
    // This would need to be implemented to get the original team name
    return '';
  }

  getEditingTeamIndex() {
    // This would need to be implemented to get the team's color index
    return 0;
  }

  // Public API methods
  setMaxTeams(maxTeams) {
    this.state.maxTeams = maxTeams;
    this.element.querySelector('.max-count').textContent = maxTeams;
    this.updateDisplay();
  }

  getFormData() {
    return {
      teamName: this.teamNameInput.value.trim(),
      selectedPins: [...this.state.selectedPins],
      isValid: this.state.isValid
    };
  }

  isEditMode() {
    return this.state.isEditMode;
  }

  getCurrentTeamCount() {
    return this.state.currentTeamCount;
  }
}
