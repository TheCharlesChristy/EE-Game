class GPIOPinSelector {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.element = null;
    this.dropdown = null;
    this.visualGrid = null;
    this.conflictWarning = null;
    this.selectedPinsList = null;
    this.availableCountElement = null;
    
    this.options = {
      allowMultiple: false,
      teamId: null,
      ...options
    };
    
    this.state = {
      selectedPins: [],
      availablePins: [],
      usedPins: new Map(), // pin -> teamId
      reservedPins: [1, 2, 6, 9, 14, 20, 25, 30, 34, 39], // System reserved pins
      currentMode: 'dropdown'
    };
    
    // Standard GPIO pins available for teams (excluding power, ground, reserved)
    this.gpioLayout = [
      { pin: 3, label: 'GPIO 2' },
      { pin: 5, label: 'GPIO 3' },
      { pin: 7, label: 'GPIO 4' },
      { pin: 8, label: 'GPIO 14' },
      { pin: 10, label: 'GPIO 15' },
      { pin: 11, label: 'GPIO 17' },
      { pin: 12, label: 'GPIO 18' },
      { pin: 13, label: 'GPIO 27' },
      { pin: 15, label: 'GPIO 22' },
      { pin: 16, label: 'GPIO 23' },
      { pin: 18, label: 'GPIO 24' },
      { pin: 19, label: 'GPIO 10' },
      { pin: 21, label: 'GPIO 9' },
      { pin: 22, label: 'GPIO 25' },
      { pin: 23, label: 'GPIO 11' },
      { pin: 24, label: 'GPIO 8' },
      { pin: 26, label: 'GPIO 7' },
      { pin: 29, label: 'GPIO 5' },
      { pin: 31, label: 'GPIO 6' },
      { pin: 32, label: 'GPIO 12' },
      { pin: 33, label: 'GPIO 13' },
      { pin: 35, label: 'GPIO 19' },
      { pin: 36, label: 'GPIO 16' },
      { pin: 37, label: 'GPIO 26' },
      { pin: 38, label: 'GPIO 20' },
      { pin: 40, label: 'GPIO 21' }
    ];
    
    this.init();
  }

  init() {
    this.element = document.querySelector(this.containerId);
    if (!this.element) return;
    
    this.dropdown = this.element.querySelector('.pin-dropdown');
    this.conflictWarning = this.element.querySelector('.pin-conflict-warning');
    this.selectedPinsList = this.element.querySelector('.selected-pins-list');
    this.availableCountElement = this.element.querySelector('.available-count');
    
    this.setupEventListeners();
    this.generateVisualLayout();
    this.updateAvailablePins();
    this.updateDropdown();
    this.updateDisplay();
  }

  setupEventListeners() {
    // Mode switching
    const tabButtons = this.element.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        this.switchMode(mode);
      });
    });
    
    // Dropdown selection
    this.dropdown.addEventListener('change', (event) => {
      const pinNumber = parseInt(event.target.value);
      if (pinNumber) {
        this.selectPin(pinNumber);
      }
    });
    
    // Listen for pin availability updates from other components
    document.addEventListener('pin_assignment_changed', (event) => {
      this.updatePinAvailability(event.detail);
    });
    
    // Listen for team removal events to free up pins
    document.addEventListener('team_removed', (event) => {
      this.freePinsForTeam(event.detail.teamId);
    });
  }

  switchMode(mode) {
    this.state.currentMode = mode;
    
    // Update tab buttons
    const tabButtons = this.element.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    // Update mode containers
    const dropdownMode = this.element.querySelector('.dropdown-mode');
    const visualMode = this.element.querySelector('.visual-mode');
    
    dropdownMode.classList.toggle('active', mode === 'dropdown');
    visualMode.classList.toggle('active', mode === 'visual');
  }

  generateVisualLayout() {
    const pinGrid = this.element.querySelector('.pin-grid');
    if (!pinGrid) return;
    
    pinGrid.innerHTML = '';
    
    // Create a 2-column layout representing GPIO pins
    for (let i = 0; i < 40; i += 2) {
      const leftPin = i + 1;
      const rightPin = i + 2;
      
      // Create pin buttons
      const leftPinBtn = this.createPinButton(leftPin);
      const rightPinBtn = this.createPinButton(rightPin);
      
      pinGrid.appendChild(leftPinBtn);
      pinGrid.appendChild(rightPinBtn);
    }
    
    this.visualGrid = pinGrid;
  }

  createPinButton(pinNumber) {
    const button = document.createElement('button');
    button.className = 'gpio-pin';
    button.dataset.pin = pinNumber;
    button.textContent = pinNumber;
    button.type = 'button';
    
    const gpioInfo = this.gpioLayout.find(p => p.pin === pinNumber);
    if (gpioInfo) {
      button.title = `Pin ${pinNumber} - ${gpioInfo.label}`;
    } else {
      button.title = `Pin ${pinNumber}`;
    }
    
    button.addEventListener('click', () => {
      if (!button.classList.contains('used') && !button.classList.contains('reserved')) {
        this.selectPin(pinNumber);
      }
    });
    
    return button;
  }

  updateAvailablePins() {
    this.state.availablePins = this.gpioLayout
      .map(gpio => gpio.pin)
      .filter(pin => 
        !this.state.reservedPins.includes(pin) &&
        !this.state.usedPins.has(pin)
      );
    
    this.availableCountElement.textContent = this.state.availablePins.length;
  }

  updateDropdown() {
    // Clear existing options except the first one
    this.dropdown.innerHTML = '<option value="">Select a GPIO pin...</option>';
    
    // Add available pins
    this.state.availablePins.forEach(pin => {
      const gpioInfo = this.gpioLayout.find(p => p.pin === pin);
      const option = document.createElement('option');
      option.value = pin;
      option.textContent = `Pin ${pin}${gpioInfo ? ` - ${gpioInfo.label}` : ''}`;
      this.dropdown.appendChild(option);
    });
    
    // Update dropdown value to match current selection
    if (this.state.selectedPins.length > 0) {
      this.dropdown.value = this.state.selectedPins[0];
    }
  }

  updateVisualPins() {
    if (!this.visualGrid) return;
    
    const pinButtons = this.visualGrid.querySelectorAll('.gpio-pin');
    pinButtons.forEach(button => {
      const pin = parseInt(button.dataset.pin);
      
      // Reset classes
      button.classList.remove('available', 'used', 'selected', 'reserved');
      
      if (this.state.reservedPins.includes(pin)) {
        button.classList.add('reserved');
      } else if (this.state.selectedPins.includes(pin)) {
        button.classList.add('selected');
      } else if (this.state.usedPins.has(pin)) {
        button.classList.add('used');
        const teamId = this.state.usedPins.get(pin);
        button.title += ` (Used by ${teamId})`;
      } else if (this.state.availablePins.includes(pin)) {
        button.classList.add('available');
      }
    });
  }

  selectPin(pinNumber) {
    if (this.state.reservedPins.includes(pinNumber)) return;
    if (this.state.usedPins.has(pinNumber) && this.state.usedPins.get(pinNumber) !== this.options.teamId) return;
    
    if (!this.options.allowMultiple) {
      // Single pin selection - clear previous selection
      this.state.selectedPins = [pinNumber];
    } else {
      // Multiple pin selection
      const index = this.state.selectedPins.indexOf(pinNumber);
      if (index > -1) {
        this.state.selectedPins.splice(index, 1);
      } else {
        this.state.selectedPins.push(pinNumber);
      }
    }
    
    this.updateDisplay();
    this.emitSelectionEvent();
  }

  updateDisplay() {
    this.updateConflictWarning();
    this.updateSelectedPinsDisplay();
    this.updateVisualPins();
    
    // Update dropdown selection
    if (this.state.selectedPins.length > 0) {
      this.dropdown.value = this.state.selectedPins[0];
    } else {
      this.dropdown.value = '';
    }
  }

  updateConflictWarning() {
    const hasConflict = this.state.selectedPins.some(pin => 
      this.state.usedPins.has(pin) && this.state.usedPins.get(pin) !== this.options.teamId
    );
    
    this.conflictWarning.style.display = hasConflict ? 'block' : 'none';
    this.dropdown.classList.toggle('conflict', hasConflict);
  }

  updateSelectedPinsDisplay() {
    if (this.state.selectedPins.length === 0) {
      this.selectedPinsList.innerHTML = '<span class="no-selection">None selected</span>';
      return;
    }
    
    this.selectedPinsList.innerHTML = this.state.selectedPins
      .map(pin => {
        const gpioInfo = this.gpioLayout.find(p => p.pin === pin);
        return `
          <span class="selected-pin-tag">
            Pin ${pin}${gpioInfo ? ` (${gpioInfo.label})` : ''}
            <button type="button" class="pin-remove-btn" data-pin="${pin}">×</button>
          </span>
        `;
      })
      .join(' ');
    
    // Add remove button event listeners
    this.selectedPinsList.querySelectorAll('.pin-remove-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const pin = parseInt(btn.dataset.pin);
        this.removePin(pin);
      });
    });
  }

  removePin(pinNumber) {
    const index = this.state.selectedPins.indexOf(pinNumber);
    if (index > -1) {
      this.state.selectedPins.splice(index, 1);
      this.updateDisplay();
      this.emitSelectionEvent();
    }
  }

  updatePinAvailability(availabilityData) {
    this.state.usedPins = new Map(availabilityData.usedPins || []);
    this.updateAvailablePins();
    this.updateDropdown();
    this.updateDisplay();
  }

  freePinsForTeam(teamId) {
    for (const [pin, assignedTeamId] of this.state.usedPins) {
      if (assignedTeamId === teamId) {
        this.state.usedPins.delete(pin);
      }
    }
    this.updateAvailablePins();
    this.updateDropdown();
    this.updateDisplay();
    this.emitAvailabilityEvent();
  }

  emitSelectionEvent() {
    const event = new CustomEvent('pin_selected', {
      detail: {
        teamId: this.options.teamId,
        selectedPins: [...this.state.selectedPins],
        isValid: this.isSelectionValid()
      },
      bubbles: true
    });
    this.element.dispatchEvent(event);
  }

  emitAvailabilityEvent() {
    const event = new CustomEvent('pin_availability_changed', {
      detail: {
        availablePins: [...this.state.availablePins],
        usedPins: Array.from(this.state.usedPins.entries()),
        allValid: this.validateAllPins()
      },
      bubbles: true
    });
    this.element.dispatchEvent(event);
  }

  isSelectionValid() {
    return this.state.selectedPins.length > 0 && 
           !this.state.selectedPins.some(pin => 
             this.state.usedPins.has(pin) && this.state.usedPins.get(pin) !== this.options.teamId
           );
  }

  validateAllPins() {
    // Check if all current pin assignments are valid (no conflicts)
    return true; // Simplified for now
  }

  // Public API methods
  setSelectedPins(pins) {
    this.state.selectedPins = Array.isArray(pins) ? [...pins] : [pins];
    this.updateDisplay();
  }

  getSelectedPins() {
    return [...this.state.selectedPins];
  }

  setTeamId(teamId) {
    this.options.teamId = teamId;
  }

  reservePin(pin, teamId) {
    this.state.usedPins.set(pin, teamId);
    this.updateAvailablePins();
    this.updateDropdown();
    this.updateDisplay();
    this.emitAvailabilityEvent();
  }

  releasePin(pin) {
    this.state.usedPins.delete(pin);
    this.updateAvailablePins();
    this.updateDropdown();
    this.updateDisplay();
    this.emitAvailabilityEvent();
  }

  clear() {
    this.state.selectedPins = [];
    this.updateDisplay();
    this.emitSelectionEvent();
  }
}
