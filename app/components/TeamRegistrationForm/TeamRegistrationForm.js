/**
 * TeamRegistrationForm Component
 * 
 * Handles team registration and editing functionality for the multi-team gaming system.
 * Provides form validation, GPIO pin selection, team color assignment, and real-time
 * communication with the backend via Socket.IO.
 */

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
    
    // Pin selection elements
    this.latchPinDropdown = null;
    this.ledPinDropdown = null;
    this.resetPinDropdown = null;
    this.availableCountElement = null;
    
    this.state = {
      currentTeamCount: 0,
      maxTeams: 8,
      selectedPins: {
        latch_pin: null,
        led_pin: null,
        reset_pin: null
      },
      availablePins: [],
      usedPins: new Set(),
      isValid: false,
      teamNames: new Set(),
      isConnected: false,
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
    
    // Pin selection elements
    this.latchPinDropdown = this.element.querySelector('#latchPin');
    this.ledPinDropdown = this.element.querySelector('#ledPin');
    this.resetPinDropdown = this.element.querySelector('#resetPin');
    this.availableCountElement = this.element.querySelector('.available-count');
    
    this.setupEventListeners();
    this.requestAvailablePins();
    this.updateDisplay();
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
    
    // Pin selection dropdowns
    this.latchPinDropdown.addEventListener('change', (event) => {
      this.handlePinSelection('latch_pin', event.target.value);
    });
    
    this.ledPinDropdown.addEventListener('change', (event) => {
      this.handlePinSelection('led_pin', event.target.value);
    });
    
    this.resetPinDropdown.addEventListener('change', (event) => {
      this.handlePinSelection('reset_pin', event.target.value);
    });
    
    // Listen for team count updates from TeamConfigurationList
    document.addEventListener('team_count_changed', (event) => {
      this.handleTeamCountUpdate(event.detail);
    });

    // Listen for socket connection status
    document.addEventListener('socketio_connected', (event) => {
      this.state.isConnected = true;
      this.requestAvailablePins();
      this.updateSubmitButton();
    });

    // Socket.IO event listeners
    if (typeof socket !== 'undefined') {
      socket.on('team_created', (data) => {
        this.handleTeamCreated(data);
      });

      socket.on('team_updated', (data) => {
        this.handleTeamUpdated(data);
      });

      socket.on('team_error', (error) => {
        this.handleTeamError(error);
      });

      socket.on('teams_list', (teams) => {
        this.handleTeamsListUpdate(teams);
      });

      socket.on('available_pins', (pins) => {
        this.handleAvailablePins(pins);
      });
    }
  }

  requestAvailablePins() {
    if (typeof socket !== 'undefined' && this.state.isConnected) {
      socket.emit('get_available_pins');
    }
  }

  handleAvailablePins(data) {
    const pins = data.pins || data; // Handle both {pins: []} and [] formats
    this.state.availablePins = Array.isArray(pins) ? pins : [];
    this.updatePinDropdowns();
    this.updateAvailableCount();
  }

  updatePinDropdowns() {
    const dropdowns = [this.latchPinDropdown, this.ledPinDropdown, this.resetPinDropdown];
    const pinTypes = ['latch_pin', 'led_pin', 'reset_pin'];
    
    dropdowns.forEach((dropdown, index) => {
      if (!dropdown) return;
      
      const currentValue = dropdown.value;
      const pinType = pinTypes[index];
      
      // Clear existing options except the first one
      dropdown.innerHTML = `<option value="">Select ${pinType.replace('_', ' ')}...</option>`;
      
      this.state.availablePins.forEach(pin => {
        const option = document.createElement('option');
        option.value = pin;
        option.textContent = `GPIO ${pin}`;
        
        // Check if pin is used by another assignment in this form or by other teams
        const isUsedByOtherAssignment = Object.entries(this.state.selectedPins)
          .some(([type, selectedPin]) => type !== pinType && selectedPin == pin);
        const isUsedByOtherTeam = this.state.usedPins.has(pin);
        
        if (isUsedByOtherAssignment || isUsedByOtherTeam) {
          option.disabled = true;
          option.textContent += ' (Used)';
        }
        
        dropdown.appendChild(option);
      });
      
      // Restore previous value if still valid
      if (currentValue && this.state.availablePins.includes(parseInt(currentValue))) {
        dropdown.value = currentValue;
      }
    });
  }

  handlePinSelection(pinType, pinValue) {
    const previousPin = this.state.selectedPins[pinType];
    this.state.selectedPins[pinType] = pinValue ? parseInt(pinValue) : null;
    
    // Update pin dropdowns to reflect availability changes
    this.updatePinDropdowns();
    this.updateSelectedPinsDisplay();
    this.validatePinSelection();
    this.updateSubmitButton();
  }

  validatePinSelection() {
    const conflictWarnings = this.element.querySelectorAll('.pin-conflict-warning');
    conflictWarnings.forEach(warning => warning.style.display = 'none');
    
    // Check for conflicts within this form
    const selectedPins = Object.values(this.state.selectedPins).filter(pin => pin !== null);
    const uniquePins = new Set(selectedPins);
    
    if (selectedPins.length !== uniquePins.size) {
      // Show conflict warnings
      conflictWarnings.forEach(warning => warning.style.display = 'block');
      return false;
    }
    
    return true;
  }

  updateSelectedPinsDisplay() {
    const pinTypes = ['latch_pin', 'led_pin', 'reset_pin'];
    const displayNames = ['Latch', 'LED', 'Reset'];
    
    pinTypes.forEach((pinType, index) => {
      const pinValue = this.state.selectedPins[pinType];
      const valueElement = this.element.querySelectorAll('.pin-value')[index];
      
      if (valueElement) {
        if (pinValue) {
          valueElement.textContent = `GPIO ${pinValue}`;
          valueElement.classList.remove('no-selection');
        } else {
          valueElement.textContent = 'None';
          valueElement.classList.add('no-selection');
        }
      }
    });
  }

  updateAvailableCount() {
    if (this.availableCountElement) {
      this.availableCountElement.textContent = this.state.availablePins.length;
    }
  }

  validateTeamName() {
    const name = this.teamNameInput.value.trim();
    let isValid = true;
    let message = '';

    // Reset visual state
    this.teamNameInput.classList.remove('valid', 'invalid');
    this.inputFeedback.classList.remove('success', 'error');

    if (name === '') {
      // Empty input - neutral state
      this.inputFeedback.textContent = '';
      this.state.isValid = false;
      return;
    }

    if (name.length < 2) {
      isValid = false;
      message = 'Team name must be at least 2 characters long';
    } else if (name.length > 50) {
      isValid = false;
      message = 'Team name cannot exceed 50 characters';
    } else if (!/^[a-zA-Z0-9\s\-_]+$/.test(name)) {
      isValid = false;
      message = 'Team name can only contain letters, numbers, spaces, hyphens, and underscores';
    } else if (this.state.teamNames.has(name.toLowerCase())) {
      isValid = false;
      message = 'A team with this name already exists';
    }

    // Update visual feedback
    if (isValid) {
      this.teamNameInput.classList.add('valid');
      this.inputFeedback.classList.add('success');
      this.inputFeedback.textContent = '✓ Team name is available';
    } else {
      this.teamNameInput.classList.add('invalid');
      this.inputFeedback.classList.add('error');
      this.inputFeedback.textContent = message;
    }

    this.state.isValid = isValid;
    return isValid;
  }

  updateSubmitButton() {
    const hasValidName = this.state.isValid && this.teamNameInput.value.trim().length > 0;
    const hasAllPins = Object.values(this.state.selectedPins).every(pin => pin !== null);
    const isConnected = this.state.isConnected;
    const pinSelectionValid = this.validatePinSelection();
    
    const canSubmit = hasValidName && hasAllPins && isConnected && pinSelectionValid;
    
    this.submitButton.disabled = !canSubmit;
    
    if (canSubmit) {
      this.form.classList.add('valid');
    } else {
      this.form.classList.remove('valid');
    }
  }

  updateDisplay() {
    // Update team count display
    this.currentCountElement.textContent = this.state.currentTeamCount;
    
    // Update count styling based on limits
    this.currentCountElement.classList.remove('warning', 'limit');
    if (this.state.currentTeamCount >= this.state.maxTeams - 1) {
      this.currentCountElement.classList.add('warning');
    }
    if (this.state.currentTeamCount >= this.state.maxTeams) {
      this.currentCountElement.classList.add('limit');
    }
    
    // Show/hide form based on team limit
    const isAtLimit = this.state.currentTeamCount >= this.state.maxTeams;
    this.form.style.display = isAtLimit ? 'none' : 'block';
    this.limitReachedSection.style.display = isAtLimit ? 'block' : 'none';
    
    // Update team color preview
    this.updateTeamColor();
  }

  updateTeamColor() {
    const teamIndex = this.state.currentTeamCount;
    
    const colorInfo = this.state.teamColors[teamIndex % this.state.teamColors.length];
    
    this.colorCircle.style.backgroundColor = colorInfo.color;
    this.colorName.textContent = colorInfo.name;
  }

  handleSubmit() {
    if (!this.state.isValid || !Object.values(this.state.selectedPins).every(pin => pin !== null)) return;
    
    this.form.classList.add('loading');
    this.submitButton.disabled = true;
    
    const teamData = {
      team_id: this.generateTeamId(),
      name: this.teamNameInput.value.trim(),
      team_color: this.colorCircle.style.backgroundColor || this.state.teamColors[0].color,
      latch_pin: this.state.selectedPins.latch_pin,
      reset_pin: this.state.selectedPins.reset_pin,
      led_pin: this.state.selectedPins.led_pin
    };
    
    // Emit create team event
    if (typeof socket !== 'undefined') {
      socket.emit('create_team', teamData);
    } else {
      // Fallback for testing without socket connection
      console.warn('Socket.IO not available, simulating team creation');
      setTimeout(() => {
        this.handleTeamCreated(teamData);
      }, 1000);
    }
  }

  handleTeamCreated(teamData) {
    this.form.classList.remove('loading');
    this.resetForm();
    
    // Emit success event for other components
    const event = new CustomEvent('team_registered', {
      detail: teamData,
      bubbles: true
    });
    this.element.dispatchEvent(event);
    
    // Show success feedback briefly
    this.showSuccessMessage(`Team "${teamData.name}" created successfully!`);
    
    // Refresh available pins
    this.requestAvailablePins();
  }

  handleTeamUpdated(teamData) {
    this.form.classList.remove('loading');
    this.exitEditMode();
    
    // Emit update event for other components
    const event = new CustomEvent('team_updated', {
      detail: teamData,
      bubbles: true
    });
    this.element.dispatchEvent(event);
    
    this.showSuccessMessage(`Team "${teamData.name}" updated successfully!`);
    
    // Refresh available pins
    this.requestAvailablePins();
  }

  handleTeamError(error) {
    this.form.classList.remove('loading');
    this.submitButton.disabled = false;
    
    // Show error feedback
    this.inputFeedback.classList.remove('success');
    this.inputFeedback.classList.add('error');
    this.inputFeedback.textContent = error;
  }

  handleTeamsListUpdate(teams) {
    // Ensure teams is an array
    if (!Array.isArray(teams)) {
      console.warn('Teams list is not an array:', teams);
      return;
    }
    
    // Update internal state based on current teams
    this.state.teamNames.clear();
    this.state.usedPins.clear();
    
    teams.forEach(team => {
      if (team && team.name) {
        this.state.teamNames.add(team.name.toLowerCase());
      }
      
      // Track used pins (excluding current team if in edit mode)
      if (team && team.id !== this.state.editingTeamId) {
        if (team.latch_pin) this.state.usedPins.add(team.latch_pin);
        if (team.led_pin) this.state.usedPins.add(team.led_pin);
        if (team.reset_pin) this.state.usedPins.add(team.reset_pin);
      }
    });
    
    // Update pin dropdowns and validate
    this.updatePinDropdowns();
    
    // Re-validate current input
    if (this.teamNameInput.value.trim()) {
      this.validateTeamName();
      this.updateSubmitButton();
    }
  }

  handleTeamCountUpdate(countData) {
    this.state.currentTeamCount = countData.count;
    
    // Extract team names from the teams data if available
    if (countData.teams && Array.isArray(countData.teams)) {
      this.state.teamNames = new Set(
        countData.teams.map(team => team.name.toLowerCase())
      );
      
      // Re-validate current input after updating team names
      if (this.teamNameInput && this.teamNameInput.value.trim()) {
        this.validateTeamName();
        this.updateSubmitButton();
      }
    }
    
    this.updateDisplay();
  }

  resetForm() {
    this.teamNameInput.value = '';
    this.state.selectedPins = {
      latch_pin: null,
      led_pin: null,
      reset_pin: null
    };
    
    // Reset pin selection UI
    this.latchPinDropdown.value = '';
    this.ledPinDropdown.value = '';
    this.resetPinDropdown.value = '';
    this.updateSelectedPinsDisplay();
    
    // Clear validation states
    this.teamNameInput.classList.remove('valid', 'invalid');
    this.inputFeedback.textContent = '';
    this.inputFeedback.classList.remove('success', 'error');
    this.form.classList.remove('valid', 'loading');
    this.submitButton.disabled = true;
    
    this.updateTeamColor();
  }

  showSuccessMessage(message) {
    // Temporarily show success message
    const originalMessage = this.inputFeedback.textContent;
    const originalClasses = this.inputFeedback.className;
    
    this.inputFeedback.className = 'input-feedback success';
    this.inputFeedback.textContent = message;
    
    setTimeout(() => {
      this.inputFeedback.className = originalClasses;
      this.inputFeedback.textContent = originalMessage;
    }, 3000);
  }

  generateTeamId() {
    return 'team_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  getEditingTeamIndex() {
    // This would need to be implemented to get the team's original color index
    // For now, return current count as fallback
    return this.state.currentTeamCount;
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
      selectedPins: {...this.state.selectedPins},
      isValid: this.state.isValid
    };
  }

  getCurrentTeamCount() {
    return this.state.currentTeamCount;
  }

  clearForm() {
    this.resetForm();
  }
}

const teamRegistrationForm = new TeamRegistrationForm();