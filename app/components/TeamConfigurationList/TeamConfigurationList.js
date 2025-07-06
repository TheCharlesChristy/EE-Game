/**
 * TeamConfigurationList Component
 * 
 * Displays and manages the list of registered teams for the multi-team gaming system.
 * Handles team creation events, team removal, and emits events for team count changes.
 */

class TeamConfigurationList {
  constructor() {
    this.element = null;
    this.teamCountElement = null;
    this.noTeamsMessage = null;
    this.teamsList = null;
    this.editModal = null;
    this.editForm = null;
    this.currentEditingTeam = null;
    // Removed this.availablePins - we'll request from server when needed
    this.availablePinsListenerSet = false;
    
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
    this.editModal = this.element.querySelector('.edit-modal-overlay');
    this.editForm = this.element.querySelector('.edit-team-form');
    
    this.setupEventListeners();
    this.setupModalEventListeners();
    this.updateDisplay();
    // Removed loadAvailablePins() - we'll request pins only when needed
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
    
    // Listen for Socket.IO events
    if (typeof socket !== 'undefined') {
      socket.on('team_created', (teamData) => {
        this.addTeam(teamData);
      });

      socket.on('team_updated', (teamData) => {
        this.updateTeam(teamData);
      });

      socket.on('team_deleted', (data) => {
        this.handleTeamDeleted(data);
      });

      socket.on('team_list_updated', (data) => {
        this.handleTeamListUpdate(data);
      });

      socket.on('teams_list', (data) => {
        this.handleTeamsListUpdate(data);
      });

      socket.on('team_error', (error) => {
        this.handleTeamError(error);
      });

      socket.on('team_status', (status) => {
        this.handleTeamStatus(status);
      });

      socket.on('latch_reset', (data) => {
        this.handleLatchReset(data);
      });

      socket.on('led_state_changed', (data) => {
        this.handleLedStateChanged(data);
      });
    }
  }

  handleTeamListUpdate(data) {
    const teams = data.teams || data;
    if (Array.isArray(teams)) {
      this.teams.clear();
      teams.forEach(teamData => {
        this.addTeam(teamData, false); // Don't emit events for bulk updates
      });
      this.updateDisplay();
      this.emitTeamCountEvent(); // Emit once after all teams are added
    }
  }

  handleTeamsListUpdate(data) {
    const teams = data.teams || data;
    if (Array.isArray(teams)) {
      this.teams.clear();
      teams.forEach(teamData => {
        this.addTeam(teamData, false); // Don't emit events for bulk updates
      });
      this.updateDisplay();
      this.emitTeamCountEvent(); // Emit once after all teams are added
    }
  }

  handleTeamDeleted(data) {
    const teamId = data.team_id || data.teamId;
    if (teamId && this.teams.has(teamId)) {
      this.removeTeam(teamId);
      
      // Show success message briefly
      this.showMessage(`Team deleted successfully`, 'success');
    }
  }

  handleTeamError(error) {
    const message = error.message || error;
    this.showMessage(`Error: ${message}`, 'error');
    console.error('Team operation error:', error);
  }

  handleTeamStatus(status) {
    const teamId = status.team_id;
    const team = this.teams.get(teamId);
    
    if (team) {
      // Update team state with hardware status
      team.latch_state = status.latch_state || false;
      team.led_state = status.led_state || false;
      
      // Update the display to show new states
      this.updateTeamStateDisplay(teamId);
      
      console.log(`Team ${teamId} status updated:`, status);
      this.showMessage(`Team "${team.name}" status updated`, 'success');
    }
  }

  handleLatchReset(data) {
    const teamId = data.team_id;
    const team = this.teams.get(teamId);
    
    if (team) {
      // Update latch state to false (reset)
      team.latch_state = false;
      this.updateTeamStateDisplay(teamId);
      
      console.log(`Latch reset for team ${teamId}`);
      this.showMessage(`Latch reset for team "${team.name}"`, 'success');
    }
  }

  handleLedStateChanged(data) {
    const teamId = data.team_id;
    const ledState = data.led_state;
    const team = this.teams.get(teamId);
    
    if (team) {
      // Update LED state
      team.led_state = ledState;
      this.updateTeamStateDisplay(teamId);
      
      console.log(`LED ${ledState ? 'turned on' : 'turned off'} for team ${teamId}`);
      this.showMessage(`LED ${ledState ? 'turned on' : 'turned off'} for team "${team.name}"`, 'success');
    }
  }

  updateTeamStateDisplay(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return;
    
    const teamElement = document.querySelector(`[data-team-id="${teamId}"]`);
    if (!teamElement) return;
    
    // Find or create hardware state display
    let stateDisplay = teamElement.querySelector('.hardware-state');
    if (!stateDisplay) {
      stateDisplay = document.createElement('div');
      stateDisplay.className = 'hardware-state';
      
      const teamDetails = teamElement.querySelector('.team-details');
      if (teamDetails) {
        teamDetails.appendChild(stateDisplay);
      }
    }
    
    // Update state display
    stateDisplay.innerHTML = `
      <span class="state-item latch-state ${team.latch_state ? 'active' : 'inactive'}">
        🔒 Latch: ${team.latch_state ? 'Latched' : 'Open'}
      </span>
      <span class="state-item led-state ${team.led_state ? 'active' : 'inactive'}">
        💡 LED: ${team.led_state ? 'On' : 'Off'}
      </span>
    `;
  }

  showMessage(message, type = 'info') {
    // Create a temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `team-message team-message-${type}`;
    messageEl.textContent = message;
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 4px;
      color: white;
      font-weight: 500;
      z-index: 1000;
      transition: opacity 0.3s ease;
    `;
    
    if (type === 'success') {
      messageEl.style.backgroundColor = 'var(--secondary-green)';
    } else if (type === 'error') {
      messageEl.style.backgroundColor = 'var(--error-red)';
    } else {
      messageEl.style.backgroundColor = 'var(--primary-medium-blue)';
    }
    
    document.body.appendChild(messageEl);
    
    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.style.opacity = '0';
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 3000);
  }

  addTeam(teamData, emitEvent = true) {
    if (!teamData || !teamData.team_id) return;

    const team = {
      id: teamData.team_id,
      name: teamData.name,
      latch_pin: teamData.latch_pin,
      led_pin: teamData.led_pin,
      reset_pin: teamData.reset_pin,
      color: teamData.team_color || this.getTeamColor(this.teams.size),
      status: 'disconnected',
      testing: false,
      latch_state: teamData.latch_state || false,
      led_state: teamData.led_state || false,
      ...teamData
    };
    
    this.teams.set(team.id, team);
    this.updateDisplay();
    
    if (emitEvent) {
      this.emitTeamCountEvent();
    }
  }

  removeTeam(teamId) {
    if (this.teams.has(teamId)) {
      this.teams.delete(teamId);
      this.updateDisplay();
      this.emitTeamCountEvent();
    }
  }

  updateTeam(teamData) {
    if (this.teams.has(teamData.team_id || teamData.id)) {
      const teamId = teamData.team_id || teamData.id;
      const existingTeam = this.teams.get(teamId);
      this.teams.set(teamId, { ...existingTeam, ...teamData });
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
    
    const pins = [];
    if (team.latch_pin) pins.push(`Latch: ${team.latch_pin}`);
    if (team.led_pin) pins.push(`LED: ${team.led_pin}`);
    if (team.reset_pin) pins.push(`Reset: ${team.reset_pin}`);
    const pinText = pins.length > 0 ? pins.join(', ') : 'None';
    
    teamItem.innerHTML = `
      <div class="team-color-indicator" style="background-color: ${team.color}"></div>
      <div class="team-info">
        <div class="team-name">${this.escapeHtml(team.name)}</div>
        <div class="team-details">
          <div class="team-pins">Pins: ${pinText}</div>
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
        <button type="button" class="action-btn update-state" title="Update State" data-action="update-state">
          🔄
        </button>
        <button type="button" class="action-btn reset-latch" title="Reset Latch" data-action="reset-latch">
          🔓
        </button>
        <button type="button" class="action-btn toggle-led" title="Toggle LED" data-action="toggle-led">
          💡
        </button>
      </div>
    `;
    
    // Add event listeners to action buttons
    const editBtn = teamItem.querySelector('[data-action="edit"]');
    const deleteBtn = teamItem.querySelector('[data-action="delete"]');
    const updateStateBtn = teamItem.querySelector('[data-action="update-state"]');
    const resetLatchBtn = teamItem.querySelector('[data-action="reset-latch"]');
    const toggleLedBtn = teamItem.querySelector('[data-action="toggle-led"]');
    
    editBtn.addEventListener('click', () => this.editTeam(team.id));
    deleteBtn.addEventListener('click', () => this.confirmDeleteTeam(team.id));
    updateStateBtn.addEventListener('click', () => this.updateTeamState(team.id));
    resetLatchBtn.addEventListener('click', () => this.resetTeamLatch(team.id));
    toggleLedBtn.addEventListener('click', () => this.toggleTeamLed(team.id));
    
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
    const team = this.teams.get(teamId);
    if (!team) return;
    
    this.currentEditingTeam = { ...team }; // Store a copy
    this.populateEditForm(team);
    this.showEditModal();
  }

  showEditModal() {
    if (this.editModal) {
      this.editModal.style.display = 'flex';
      // Focus on the team name input
      const nameInput = this.editForm.querySelector('#edit-team-name');
      if (nameInput) {
        setTimeout(() => nameInput.focus(), 100);
      }
    }
  }

  hideEditModal() {
    if (this.editModal) {
      this.editModal.style.display = 'none';
      this.currentEditingTeam = null;
      this.clearEditForm();
    }
  }

  populateEditForm(team) {
    if (!this.editForm) return;
    
    // Populate form fields
    const nameInput = this.editForm.querySelector('#edit-team-name');
    const colorInput = this.editForm.querySelector('#edit-team-color');
    const colorPreview = this.editForm.querySelector('.color-preview');
    const pin1Select = this.editForm.querySelector('select[name="pin1"]');
    const pin2Select = this.editForm.querySelector('select[name="pin2"]');
    const pin3Select = this.editForm.querySelector('select[name="pin3"]');
    
    if (nameInput) nameInput.value = team.name || '';
    if (colorInput) colorInput.value = this.convertTeamColorToHex(team.color);
    if (colorPreview) colorPreview.style.backgroundColor = team.color;
    
    // Request fresh pins from server and then populate selectors
    this.requestAvailablePins((availablePins) => {
      this.updatePinSelectors(availablePins);
      
      // Set the team's current pins after selectors are populated
      if (pin1Select) pin1Select.value = team.latch_pin || '';
      if (pin2Select) pin2Select.value = team.led_pin || '';
      if (pin3Select) pin3Select.value = team.reset_pin || '';
    });
  }

  convertTeamColorToHex(cssColor) {
    // Convert CSS variable colors to hex values for color input
    const colorMap = {
      'var(--team-1-red)': '#E53E3E',
      'var(--team-2-blue)': '#3182CE',
      'var(--team-3-green)': '#38A169',
      'var(--team-4-yellow)': '#D69E2E',
      'var(--team-5-purple)': '#805AD5',
      'var(--team-6-orange)': '#DD6B20',
      'var(--team-7-pink)': '#D53F8C',
      'var(--team-8-brown)': '#A0522D'
    };
    
    return colorMap[cssColor] || cssColor;
  }

  clearEditForm() {
    if (!this.editForm) return;
    
    this.editForm.reset();
    const feedback = this.editForm.querySelectorAll('.input-feedback');
    feedback.forEach(el => el.textContent = '');
  }

  setupModalEventListeners() {
    if (!this.editModal || !this.editForm) return;
    
    // Close modal buttons
    const closeBtn = this.editModal.querySelector('.close-modal-btn');
    const cancelBtn = this.editModal.querySelector('.cancel-btn');
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideEditModal());
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.hideEditModal());
    }
    
    // Close modal when clicking overlay
    this.editModal.addEventListener('click', (e) => {
      if (e.target === this.editModal) {
        this.hideEditModal();
      }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.editModal.style.display === 'flex') {
        this.hideEditModal();
      }
    });
    
    // Form submission
    this.editForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleEditFormSubmit();
    });
    
    // Real-time validation
    const nameInput = this.editForm.querySelector('#edit-team-name');
    const colorInput = this.editForm.querySelector('#edit-team-color');
    const colorPreview = this.editForm.querySelector('.color-preview');
    
    if (nameInput) {
      nameInput.addEventListener('input', () => this.validateTeamName());
    }
    
    if (colorInput && colorPreview) {
      colorInput.addEventListener('input', (e) => {
        colorPreview.style.backgroundColor = e.target.value;
      });
    }
    
    // Pin validation and real-time updates
    const pinSelects = this.editForm.querySelectorAll('select[name^="pin"]');
    pinSelects.forEach(select => {
      select.addEventListener('change', () => {
        this.validatePins();
        // Request fresh pins and update all selectors to reflect new availability
        setTimeout(() => this.updatePinSelectors(), 100);
      });
    });
  }

  validateTeamName() {
    const nameInput = this.editForm.querySelector('#edit-team-name');
    const feedback = this.editForm.querySelector('#edit-name-feedback');
    
    if (!nameInput || !feedback) return false;
    
    const name = nameInput.value.trim();
    
    if (!name) {
      feedback.textContent = 'Team name is required';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    if (name.length > 30) {
      feedback.textContent = 'Team name must be 30 characters or less';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    // Check for duplicate names (excluding current team)
    const isDuplicate = Array.from(this.teams.values()).some(team => 
      team.name.toLowerCase() === name.toLowerCase() && 
      team.id !== this.currentEditingTeam.id
    );
    
    if (isDuplicate) {
      feedback.textContent = 'Team name already exists';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    feedback.textContent = '✓ Valid team name';
    feedback.className = 'input-feedback success';
    return true;
  }

  validatePins() {
    const pin1Select = this.editForm.querySelector('select[name="pin1"]');
    const pin2Select = this.editForm.querySelector('select[name="pin2"]');
    const pin3Select = this.editForm.querySelector('select[name="pin3"]');
    const feedback = this.editForm.querySelector('#edit-pins-feedback');
    
    if (!pin1Select || !pin2Select || !pin3Select || !feedback) return false;
    
    const pin1 = pin1Select.value;
    const pin2 = pin2Select.value;
    const pin3 = pin3Select.value;
    
    if (!pin1 || !pin2 || !pin3) {
      feedback.textContent = 'All three pins must be selected';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    const selectedPins = [parseInt(pin1), parseInt(pin2), parseInt(pin3)];
    const uniquePins = new Set(selectedPins);
    
    if (uniquePins.size !== selectedPins.length) {
      feedback.textContent = 'Each pin must be unique';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    // Get pins currently used by OTHER teams (excluding the team being edited)
    const usedByOtherTeams = new Set();
    this.teams.forEach(team => {
      if (team.id !== (this.currentEditingTeam?.id)) {
        if (team.latch_pin) usedByOtherTeams.add(team.latch_pin);
        if (team.led_pin) usedByOtherTeams.add(team.led_pin);
        if (team.reset_pin) usedByOtherTeams.add(team.reset_pin);
      }
    });
    
    // Check if any selected pins are already used by other teams
    const conflictingPins = selectedPins.filter(pin => usedByOtherTeams.has(pin));
    
    if (conflictingPins.length > 0) {
      feedback.textContent = `Pins ${conflictingPins.join(', ')} are already in use by other teams`;
      feedback.className = 'input-feedback error';
      return false;
    }
    
    feedback.textContent = '✓ Valid pin configuration';
    feedback.className = 'input-feedback success';
    return true;
  }

  handleEditFormSubmit() {
    const isNameValid = this.validateTeamName();
    const arePinsValid = this.validatePins();
    
    if (!isNameValid || !arePinsValid) {
      return;
    }
    
    const formData = new FormData(this.editForm);
    const updatedTeam = {
      team_id: this.currentEditingTeam.id,
      name: formData.get('teamName').trim(),
      team_color: formData.get('teamColor'),
      latch_pin: parseInt(formData.get('pin1')),
      led_pin: parseInt(formData.get('pin2')),
      reset_pin: parseInt(formData.get('pin3'))
    };
    
    // Send update to backend
    if (typeof socket !== 'undefined') {
      socket.emit('update_team', updatedTeam);
      this.hideEditModal();
    } else {
      // Fallback for testing
      this.updateTeam(updatedTeam);
      this.hideEditModal();
    }
  }

  requestAvailablePins(callback) {
    // Always request fresh pins from the server - no caching
    if (typeof socket !== 'undefined') {
      // Remove any existing listener to avoid duplicates
      socket.off('available_pins');
      
      // Set up one-time listener for this request
      socket.once('available_pins', (data) => {
        let availablePins = [];
        
        // Handle both formats: array directly or wrapped in object
        if (Array.isArray(data)) {
          availablePins = data;
        } else if (data && Array.isArray(data.pins)) {
          availablePins = data.pins;
        } else {
          console.warn('Unexpected available_pins data format, using fallback:', data);
          // Fallback to comprehensive pin range
          availablePins = [];
          for (let pin = 2; pin <= 27; pin++) {
            availablePins.push(pin);
          }
        }
        
        console.log('Received fresh available pins from server:', availablePins);
        
        // Call the callback with the fresh pins
        if (callback) {
          callback(availablePins);
        }
      });
      
      // Request fresh pins from server
      socket.emit('get_available_pins');
    } else {
      // Fallback for when socket is not available
      console.warn('Socket.IO not available, using fallback pin range');
      const fallbackPins = [];
      for (let pin = 2; pin <= 27; pin++) {
        fallbackPins.push(pin);
      }
      
      if (callback) {
        callback(fallbackPins);
      }
    }
  }

  updatePinSelectors(availablePins = null) {
    if (!this.editForm) return;
    
    // If no pins provided, request them fresh from server
    if (!availablePins) {
      this.requestAvailablePins((pins) => {
        this.updatePinSelectors(pins);
      });
      return;
    }
    
    const pinSelects = this.editForm.querySelectorAll('select[name^="pin"]');
    
    // Get currently selected pins in the form to avoid conflicts
    const currentlySelectedPins = new Set();
    pinSelects.forEach(select => {
      if (select.value) {
        currentlySelectedPins.add(parseInt(select.value));
      }
    });
    
    pinSelects.forEach(select => {
      const currentValue = select.value;
      select.innerHTML = '<option value="">Select Pin</option>';
      
      // Get pins currently used by OTHER teams (excluding current team being edited)
      const usedByOtherTeams = new Set();
      this.teams.forEach(team => {
        if (team.id !== (this.currentEditingTeam?.id)) {
          if (team.latch_pin) usedByOtherTeams.add(team.latch_pin);
          if (team.led_pin) usedByOtherTeams.add(team.led_pin);
          if (team.reset_pin) usedByOtherTeams.add(team.reset_pin);
        }
      });
      
      // Create a comprehensive set of all pins to show
      const pinsToShow = new Set();
      
      // Add all available pins from the server
      availablePins.forEach(pin => pinsToShow.add(pin));
      
      // Add current team's original pins to ensure they appear
      if (this.currentEditingTeam) {
        if (this.currentEditingTeam.latch_pin) pinsToShow.add(this.currentEditingTeam.latch_pin);
        if (this.currentEditingTeam.led_pin) pinsToShow.add(this.currentEditingTeam.led_pin);
        if (this.currentEditingTeam.reset_pin) pinsToShow.add(this.currentEditingTeam.reset_pin);
      }
      
      // If we don't have many pins, add a comprehensive range as fallback
      if (pinsToShow.size < 10) {
        console.warn('Limited pins available, adding fallback range');
        for (let pin = 2; pin <= 27; pin++) {
          pinsToShow.add(pin);
        }
      }
      
      // Sort pins numerically for better UX
      const sortedPins = Array.from(pinsToShow).sort((a, b) => a - b);
      
      console.log('Pins to show in selector:', sortedPins);
      
      // Add options for each pin
      sortedPins.forEach(pin => {
        const option = document.createElement('option');
        option.value = pin;
        
        // Check different types of conflicts
        const isUsedByOtherTeam = usedByOtherTeams.has(pin);
        const isSelectedInForm = currentlySelectedPins.has(pin) && parseInt(currentValue) !== pin;
        const isCurrentTeamOriginalPin = this.currentEditingTeam && 
          [this.currentEditingTeam.latch_pin, this.currentEditingTeam.led_pin, this.currentEditingTeam.reset_pin].includes(pin);
        
        if (isUsedByOtherTeam) {
          option.textContent = `GPIO ${pin} (Used by another team)`;
          option.disabled = true;
        } else if (isSelectedInForm) {
          option.textContent = `GPIO ${pin} (Selected in form)`;
          option.disabled = true;
        } else {
          option.textContent = `GPIO ${pin}`;
        }
        
        select.appendChild(option);
      });
      
      // Restore previous value if it exists and is not disabled
      if (currentValue && select.querySelector(`option[value="${currentValue}"]:not([disabled])`)) {
        select.value = currentValue;
      }
    });
  }

  confirmDeleteTeam(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return;
    
    const confirmed = confirm(`Are you sure you want to remove team "${team.name}"?`);
    if (confirmed) {
      // Send delete request to backend via Socket.IO
      if (typeof socket !== 'undefined') {
        socket.emit('delete_team', { team_id: teamId });
      } else {
        // Fallback for when socket is not available (testing)
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
  }

  updateTeamState(teamId) {
    if (typeof socket !== 'undefined') {
      socket.emit('get_team_status', { team_id: teamId });
    } else {
      console.warn('Socket.IO not available for updating team state');
    }
  }

  resetTeamLatch(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return;
    
    if (typeof socket !== 'undefined') {
      socket.emit('reset_latch', { team_id: teamId });
      
      // Update the team state after reset
      setTimeout(() => {
        this.updateTeamState(teamId);
      }, 500); // Give the hardware time to respond
    } else {
      console.warn('Socket.IO not available for resetting latch');
    }
  }

  toggleTeamLed(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return;
    
    if (typeof socket !== 'undefined') {
      socket.emit('toggle_led', { team_id: teamId });
      
      // Update the team state after toggle
      setTimeout(() => {
        this.updateTeamState(teamId);
      }, 500); // Give the hardware time to respond
    } else {
      console.warn('Socket.IO not available for toggling LED');
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

// Initialize the component
const teamConfigurationList = new TeamConfigurationList();
