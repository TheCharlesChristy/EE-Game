class TeamManagementPage {
  constructor() {
    this.systemReadinessIndicator = null;
    this.teamRegistrationForm = null;
    this.teamConfigurationList = null;
    this.hardwareTestPanel = null;
    this.navigationControls = null;
    
    this.state = {
      isInitialized: false,
      hasUnsavedChanges: false,
      teams: new Map(),
      websocketConnections: new Set()
    };
    
    this.init();
  }

  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        this.initializeComponents();
      });
    } else {
      this.initializeComponents();
    }
  }

  initializeComponents() {
    try {
      // Initialize all component instances
      this.systemReadinessIndicator = new SystemReadinessIndicator();
      this.teamRegistrationForm = new TeamRegistrationForm();
      this.teamConfigurationList = new TeamConfigurationList();
      this.hardwareTestPanel = new HardwareTestPanel();
      this.navigationControls = new NavigationControls();
      
      this.setupEventListeners();
      this.setupWebSocketConnections();
      this.loadExistingData();
      
      this.state.isInitialized = true;
      console.log('Team Management Page initialized successfully');
      
    } catch (error) {
      console.error('Error initializing Team Management Page:', error);
      this.showErrorMessage('Failed to initialize page components');
    }
  }

  setupEventListeners() {
    // Team registration events
    document.addEventListener('team_registered', (event) => {
      this.handleTeamRegistered(event.detail);
    });
    
    document.addEventListener('team_removed', (event) => {
      this.handleTeamRemoved(event.detail);
    });
    
    document.addEventListener('team_updated', (event) => {
      this.handleTeamUpdated(event.detail);
    });
    
    // Navigation events
    document.addEventListener('navigation_requested', (event) => {
      this.handleNavigationRequest(event.detail);
    });
    
    document.addEventListener('save_team_configurations', (event) => {
      this.handleSaveRequest(event.detail);
    });
    
    // Hardware testing events
    document.addEventListener('circuit_test_result', (event) => {
      this.handleCircuitTestResult(event.detail);
    });
    
    // Pin management events
    document.addEventListener('pin_selected', (event) => {
      this.handlePinSelection(event.detail);
    });
    
    // System readiness events
    document.addEventListener('system_ready_changed', (event) => {
      this.handleSystemReadinessChanged(event.detail);
    });
    
    // Window events
    window.addEventListener('beforeunload', (event) => {
      this.handlePageUnload(event);
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (event) => {
      this.handleKeyboardShortcuts(event);
    });
  }

  setupWebSocketConnections() {
    // The HardwareTestPanel will handle its own WebSocket connection
    // We just need to track it for cleanup
    if (this.hardwareTestPanel) {
      this.state.websocketConnections.add('hardware-test');
    }
  }

  loadExistingData() {
    // Load any existing team configurations from localStorage or API
    try {
      const savedTeams = localStorage.getItem('teamConfigurations');
      if (savedTeams) {
        const teams = JSON.parse(savedTeams);
        teams.forEach(team => {
          this.state.teams.set(team.id, team);
          
          // Emit team registration event to update components
          const event = new CustomEvent('team_registered', {
            detail: team
          });
          document.dispatchEvent(event);
        });
      }
    } catch (error) {
      console.error('Error loading existing team data:', error);
    }
  }

  handleTeamRegistered(teamData) {
    this.state.teams.set(teamData.id, teamData);
    this.state.hasUnsavedChanges = true;
    this.saveTeamConfigurations();
    
    console.log('Team registered:', teamData.name);
    
    // Update navigation controls about unsaved changes
    this.updateUnsavedChangesState();
  }

  handleTeamRemoved(teamData) {
    this.state.teams.delete(teamData.teamId);
    this.state.hasUnsavedChanges = true;
    this.saveTeamConfigurations();
    
    console.log('Team removed:', teamData.teamId);
    
    // Update navigation controls about unsaved changes
    this.updateUnsavedChangesState();
  }

  handleTeamUpdated(teamData) {
    this.state.teams.set(teamData.id, teamData);
    this.state.hasUnsavedChanges = true;
    this.saveTeamConfigurations();
    
    console.log('Team updated:', teamData.name);
    
    // Update navigation controls about unsaved changes
    this.updateUnsavedChangesState();
  }

  handleNavigationRequest(navigationData) {
    const { direction, destination } = navigationData;
    
    console.log(`Navigation requested: ${direction} to ${destination}`);
    
    // Perform the actual navigation
    if (direction === 'back') {
      this.navigateToMainMenu();
    } else if (direction === 'proceed') {
      this.navigateToGameSelection();
    }
  }

  handleSaveRequest(saveData) {
    this.saveTeamConfigurations()
      .then(() => {
        this.state.hasUnsavedChanges = false;
        this.updateUnsavedChangesState();
        
        if (saveData.callback) {
          saveData.callback();
        }
      })
      .catch(error => {
        console.error('Error saving team configurations:', error);
        this.showErrorMessage('Failed to save team configurations');
      });
  }

  handleCircuitTestResult(testResult) {
    const { teamId, success, details } = testResult;
    console.log(`Circuit test result for team ${teamId}: ${success ? 'PASSED' : 'FAILED'}`);
    
    if (details) {
      console.log('Test details:', details);
    }
  }

  handlePinSelection(pinData) {
    const { teamId, selectedPins, isValid } = pinData;
    console.log(`Pin selection for team ${teamId}:`, selectedPins, 'Valid:', isValid);
  }

  handleSystemReadinessChanged(readinessData) {
    const { isReady, teamCount, blockingIssues } = readinessData;
    console.log('System readiness changed:', { isReady, teamCount, blockingIssues });
    
    // Update navigation controls
    if (this.navigationControls) {
      this.navigationControls.setReadiness(isReady);
    }
  }

  handlePageUnload(event) {
    if (this.state.hasUnsavedChanges) {
      const message = 'You have unsaved team configurations. Are you sure you want to leave?';
      event.returnValue = message;
      return message;
    }
    
    // Clean up WebSocket connections
    this.cleanup();
  }

  handleKeyboardShortcuts(event) {
    // Ctrl+S to save
    if (event.ctrlKey && event.key === 's') {
      event.preventDefault();
      this.saveTeamConfigurations();
    }
    
    // Escape to cancel edit mode
    if (event.key === 'Escape') {
      if (this.teamRegistrationForm && this.teamRegistrationForm.isEditMode()) {
        this.teamRegistrationForm.cancelEdit();
      }
    }
  }

  updateUnsavedChangesState() {
    if (this.navigationControls) {
      this.navigationControls.setUnsavedChanges(this.state.hasUnsavedChanges);
    }
    
    // Emit event for other components
    const event = new CustomEvent('team_configuration_changed', {
      detail: {
        hasUnsavedChanges: this.state.hasUnsavedChanges
      }
    });
    document.dispatchEvent(event);
  }

  async saveTeamConfigurations() {
    try {
      const teams = Array.from(this.state.teams.values());
      
      // Save to localStorage (temporary solution)
      localStorage.setItem('teamConfigurations', JSON.stringify(teams));
      
      // In a real implementation, this would save to the backend API
      // await this.apiClient.saveTeamConfigurations(teams);
      
      console.log('Team configurations saved successfully');
      this.state.hasUnsavedChanges = false;
      
      return true;
    } catch (error) {
      console.error('Error saving team configurations:', error);
      throw error;
    }
  }

  navigateToMainMenu() {
    console.log('Navigating to main menu...');
    
    // In a real implementation, this would use the router
    // For now, we'll just reload to the home page
    window.location.href = '/';
  }

  navigateToGameSelection() {
    console.log('Navigating to game selection...');
    
    // In a real implementation, this would navigate to the games page
    // For now, we'll show a placeholder
    alert('Navigation to Game Selection page would happen here');
  }

  showErrorMessage(message) {
    // Create a simple error notification
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--error-red);
      color: white;
      padding: var(--space-md);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      z-index: 10000;
      max-width: 300px;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove notification after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 5000);
  }

  cleanup() {
    // Clean up WebSocket connections
    if (this.hardwareTestPanel && this.hardwareTestPanel.destroy) {
      this.hardwareTestPanel.destroy();
    }
    
    console.log('Team Management Page cleanup completed');
  }

  // Public API methods
  getPageState() {
    return {
      isInitialized: this.state.isInitialized,
      hasUnsavedChanges: this.state.hasUnsavedChanges,
      teamCount: this.state.teams.size,
      teams: Array.from(this.state.teams.values())
    };
  }

  getSystemReadiness() {
    if (this.systemReadinessIndicator) {
      return this.systemReadinessIndicator.getReadinessState();
    }
    return null;
  }

  getHardwareTestResults() {
    if (this.hardwareTestPanel) {
      return this.hardwareTestPanel.getTestResults();
    }
    return [];
  }
}

// Initialize the page when script loads
const teamManagementPage = new TeamManagementPage();
