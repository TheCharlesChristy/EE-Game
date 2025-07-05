class NavigationControls {
  constructor() {
    this.element = null;
    this.backButton = null;
    this.proceedButton = null;
    this.modal = null;
    this.modalOverlay = null;
    this.modalCancel = null;
    this.modalDiscard = null;
    this.modalSave = null;
    
    this.state = {
      isReady: false,
      hasUnsavedChanges: false,
      pendingNavigation: null
    };
    
    this.init();
  }

  init() {
    this.element = document.querySelector('.navigation-controls');
    if (!this.element) return;
    
    this.backButton = this.element.querySelector('.nav-back');
    this.proceedButton = this.element.querySelector('.nav-proceed');
    this.modal = this.element.querySelector('.unsaved-changes-modal');
    this.modalOverlay = this.element.querySelector('.modal-overlay');
    this.modalCancel = this.element.querySelector('.modal-cancel');
    this.modalDiscard = this.element.querySelector('.modal-discard');
    this.modalSave = this.element.querySelector('.modal-save');
    
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Navigation button clicks
    this.backButton.addEventListener('click', () => {
      this.handleNavigation('back');
    });
    
    this.proceedButton.addEventListener('click', () => {
      this.handleNavigation('proceed');
    });
    
    // System readiness updates
    document.addEventListener('system_ready_changed', (event) => {
      this.state.isReady = event.detail.isReady;
      this.updateProceedButton();
    });
    
    // Track unsaved changes (listen for form changes, team modifications, etc.)
    document.addEventListener('team_configuration_changed', (event) => {
      this.state.hasUnsavedChanges = event.detail.hasUnsavedChanges;
    });
    
    // Modal event listeners
    this.modalCancel.addEventListener('click', () => {
      this.hideModal();
    });
    
    this.modalDiscard.addEventListener('click', () => {
      this.hideModal();
      this.proceedWithNavigation();
    });
    
    this.modalSave.addEventListener('click', () => {
      this.saveAndNavigate();
    });
    
    // Modal overlay click to close
    this.modalOverlay.addEventListener('click', () => {
      this.hideModal();
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && this.modal.style.display !== 'none') {
        this.hideModal();
      }
    });
  }

  updateProceedButton() {
    this.proceedButton.disabled = !this.state.isReady;
    
    if (this.state.isReady) {
      this.proceedButton.classList.add('ready');
      this.proceedButton.textContent = 'Proceed to Games →';
    } else {
      this.proceedButton.classList.remove('ready');
      this.proceedButton.textContent = 'System Not Ready';
    }
  }

  handleNavigation(direction) {
    this.state.pendingNavigation = direction;
    
    // If there are unsaved changes, show confirmation modal
    if (this.state.hasUnsavedChanges) {
      this.showModal();
      return;
    }
    
    // If system is not ready and trying to proceed, don't allow
    if (direction === 'proceed' && !this.state.isReady) {
      this.showSystemNotReadyFeedback();
      return;
    }
    
    // Proceed with navigation
    this.proceedWithNavigation();
  }

  showModal() {
    this.modal.style.display = 'flex';
    this.modalCancel.focus();
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
  }

  hideModal() {
    this.modal.style.display = 'none';
    this.state.pendingNavigation = null;
    
    // Restore body scroll
    document.body.style.overflow = '';
  }

  saveAndNavigate() {
    // Emit save request event
    const saveEvent = new CustomEvent('save_team_configurations', {
      detail: {
        callback: () => {
          this.state.hasUnsavedChanges = false;
          this.hideModal();
          this.proceedWithNavigation();
        }
      },
      bubbles: true
    });
    
    this.element.dispatchEvent(saveEvent);
  }

  proceedWithNavigation() {
    if (!this.state.pendingNavigation) return;
    
    const direction = this.state.pendingNavigation;
    this.state.pendingNavigation = null;
    
    // Emit navigation event
    const navigationEvent = new CustomEvent('navigation_requested', {
      detail: {
        direction: direction,
        destination: direction === 'back' ? 'main-menu' : 'game-selection'
      },
      bubbles: true
    });
    
    this.element.dispatchEvent(navigationEvent);
  }

  showSystemNotReadyFeedback() {
    // Add visual feedback when trying to proceed while system not ready
    this.proceedButton.style.animation = 'shake 0.5s ease-in-out';
    
    setTimeout(() => {
      this.proceedButton.style.animation = '';
    }, 500);
    
    // Show tooltip or notification about what's needed
    const readinessIndicator = document.querySelector('.system-readiness-indicator');
    if (readinessIndicator) {
      readinessIndicator.scrollIntoView({ behavior: 'smooth', block: 'center' });
      readinessIndicator.style.animation = 'highlight 1s ease-in-out';
      
      setTimeout(() => {
        readinessIndicator.style.animation = '';
      }, 1000);
    }
  }

  // Public API methods
  setReadiness(isReady) {
    this.state.isReady = isReady;
    this.updateProceedButton();
  }

  setUnsavedChanges(hasChanges) {
    this.state.hasUnsavedChanges = hasChanges;
  }

  getNavigationState() {
    return {
      isReady: this.state.isReady,
      hasUnsavedChanges: this.state.hasUnsavedChanges,
      canProceed: this.state.isReady
    };
  }
}

// Add shake animation to CSS if not already present
const style = document.createElement('style');
style.textContent = `
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@keyframes highlight {
  0%, 100% { background-color: transparent; }
  50% { background-color: rgba(66, 153, 225, 0.1); }
}
`;
document.head.appendChild(style);
