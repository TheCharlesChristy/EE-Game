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
    this.availablePins = [];
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
    this.loadAvailablePins();
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
    
    // Populate pin selectors with available options
    this.updatePinSelectors();
    
    if (pin1Select) pin1Select.value = team.latch_pin || '';
    if (pin2Select) pin2Select.value = team.led_pin || '';
    if (pin3Select) pin3Select.value = team.reset_pin || '';
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
    
    // Pin validation
    const pinSelects = this.editForm.querySelectorAll('select[name^="pin"]');
    pinSelects.forEach(select => {
      select.addEventListener('change', () => this.validatePins());
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
    
    const pins = [pin1, pin2, pin3];
    const uniquePins = new Set(pins);
    
    if (uniquePins.size !== pins.length) {
      feedback.textContent = 'Each pin must be unique';
      feedback.className = 'input-feedback error';
      return false;
    }
    
    // Check if pins are available (excluding current team's pins)
    const currentTeamPins = [
      this.currentEditingTeam.latch_pin,
      this.currentEditingTeam.led_pin,
      this.currentEditingTeam.reset_pin
    ].filter(pin => pin);
    
    const unavailablePins = pins.filter(pin => {
      return !this.availablePins.includes(parseInt(pin)) && 
             !currentTeamPins.includes(parseInt(pin));
    });
    
    if (unavailablePins.length > 0) {
      feedback.textContent = `Pins ${unavailablePins.join(', ')} are not available`;
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

  loadAvailablePins() {
    // Start with a comprehensive fallback pin list
    this.availablePins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27];
    
    // Request available pins from backend
    if (typeof socket !== 'undefined') {
      socket.emit('get_available_pins');
      
      // Set up listener for available pins (only once)
      if (!this.availablePinsListenerSet) {
        socket.on('available_pins', (data) => {
          // Handle both formats: array directly or wrapped in object
          if (Array.isArray(data)) {
            this.availablePins = data;
          } else if (data && Array.isArray(data.pins)) {
            this.availablePins = data.pins;
          } else {
            console.warn('Unexpected available_pins data format:', data);
          }
          
          console.log('Received available pins:', this.availablePins);
          this.updatePinSelectors();
        });
        this.availablePinsListenerSet = true;
      }
    }
    
    // Always update pin selectors with fallback list initially
    this.updatePinSelectors();
  }

  updatePinSelectors() {
    if (!this.editForm) return;
    
    const pinSelects = this.editForm.querySelectorAll('select[name^="pin"]');
    
    pinSelects.forEach(select => {
      const currentValue = select.value;
      select.innerHTML = '<option value="">Select Pin</option>';
      
      // Get currently used pins (excluding current team being edited)
      const usedPins = new Set();
      this.teams.forEach(team => {
        if (team.id !== (this.currentEditingTeam?.id)) {
          if (team.latch_pin) usedPins.add(team.latch_pin);
          if (team.led_pin) usedPins.add(team.led_pin);
          if (team.reset_pin) usedPins.add(team.reset_pin);
        }
      });
      
      // Create a comprehensive set of all pins to show
      const pinsToShow = new Set();
      
      // Add all available pins from the system
      this.availablePins.forEach(pin => pinsToShow.add(pin));
      
      // Add current team's pins to ensure they appear
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
        
        // Mark used pins (but allow current team's pins)
        const isUsedByOtherTeam = usedPins.has(pin);
        const isCurrentTeamPin = this.currentEditingTeam && 
          [this.currentEditingTeam.latch_pin, this.currentEditingTeam.led_pin, this.currentEditingTeam.reset_pin].includes(pin);
        
        if (isUsedByOtherTeam && !isCurrentTeamPin) {
          option.textContent = `GPIO ${pin} (In Use)`;
          option.disabled = true;
        } else {
          option.textContent = `GPIO ${pin}`;
        }
        
        select.appendChild(option);
      });
      
      // Restore previous value if it exists
      if (currentValue && select.querySelector(`option[value="${currentValue}"]`)) {
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
