class HardwareTestPanel {
  constructor() {
    this.element = null;
    this.testStatusElement = null;
    this.testAllButton = null;
    this.noTeamsMessage = null;
    this.teamsTestList = null;
    this.reconnectButton = null;
    this.statusDot = null;
    this.statusText = null;
    this.resultsStats = null;
    
    this.teams = new Map();
    this.testResults = new Map();
    this.activeTests = new Set();
    this.websocket = null;
    
    this.state = {
      isConnected: false,
      isConnecting: false,
      testInProgress: false,
      stats: {
        passed: 0,
        failed: 0,
        pending: 0
      }
    };
    
    this.init();
  }

  init() {
    this.element = document.querySelector('.hardware-test-panel');
    if (!this.element) return;
    
    this.testStatusElement = this.element.querySelector('.test-status');
    this.testAllButton = this.element.querySelector('.test-all-btn');
    this.noTeamsMessage = this.element.querySelector('.no-teams-testing');
    this.teamsTestList = this.element.querySelector('.teams-test-list');
    this.reconnectButton = this.element.querySelector('.reconnect-btn');
    this.statusDot = this.element.querySelector('.status-dot');
    this.statusText = this.element.querySelector('.status-text');
    this.resultsStats = this.element.querySelector('.results-stats');
    
    this.setupEventListeners();
    this.initializeWebSocket();
    this.updateDisplay();
  }

  setupEventListeners() {
    // Test all button
    this.testAllButton.addEventListener('click', () => {
      this.testAllTeams();
    });
    
    // Reconnect button
    this.reconnectButton.addEventListener('click', () => {
      this.reconnectWebSocket();
    });
    
    // Listen for team events
    document.addEventListener('team_registered', (event) => {
      this.addTeam(event.detail);
    });
    
    document.addEventListener('team_removed', (event) => {
      this.removeTeam(event.detail.teamId);
    });
    
    document.addEventListener('team_updated', (event) => {
      this.updateTeam(event.detail);
    });
    
    // Listen for team count changes
    document.addEventListener('team_count_changed', (event) => {
      this.syncTeams(event.detail.teams);
    });
  }

  initializeWebSocket() {
    this.state.isConnecting = true;
    this.updateConnectionStatus();
    
    try {
      // Use the team-management namespace as specified
      this.websocket = new WebSocket(`ws://${window.location.host}/team-management`);
      
      this.websocket.onopen = () => {
        this.state.isConnected = true;
        this.state.isConnecting = false;
        this.updateConnectionStatus();
        console.log('Hardware test WebSocket connected');
      };
      
      this.websocket.onmessage = (event) => {
        this.handleWebSocketMessage(event);
      };
      
      this.websocket.onclose = () => {
        this.state.isConnected = false;
        this.state.isConnecting = false;
        this.updateConnectionStatus();
        console.log('Hardware test WebSocket disconnected');
        
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          if (!this.state.isConnected) {
            this.reconnectWebSocket();
          }
        }, 3000);
      };
      
      this.websocket.onerror = (error) => {
        console.error('Hardware test WebSocket error:', error);
        this.state.isConnected = false;
        this.state.isConnecting = false;
        this.updateConnectionStatus();
      };
      
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      this.state.isConnecting = false;
      this.updateConnectionStatus();
    }
  }

  handleWebSocketMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'gpio_status_update':
          this.handleGPIOStatusUpdate(data);
          break;
        case 'circuit_test_result':
          this.handleCircuitTestResult(data);
          break;
        case 'hardware_health_changed':
          this.handleHardwareHealthChanged(data);
          break;
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  handleGPIOStatusUpdate(data) {
    const { pinId, status, teamId } = data;
    
    if (teamId && this.teams.has(teamId)) {
      const team = this.teams.get(teamId);
      team.pinStatus = status;
      this.updateTeamTestDisplay(teamId);
    }
    
    this.emitHardwareStatusEvent();
  }

  handleCircuitTestResult(data) {
    const { teamId, success, details } = data;
    
    if (this.teams.has(teamId)) {
      this.testResults.set(teamId, {
        success,
        details,
        timestamp: Date.now()
      });
      
      this.activeTests.delete(teamId);
      this.updateTeamTestDisplay(teamId);
      this.updateTestStats();
      this.updateTestStatus();
      
      // Emit circuit test result event
      const event = new CustomEvent('circuit_test_result', {
        detail: data,
        bubbles: true
      });
      this.element.dispatchEvent(event);
    }
  }

  handleHardwareHealthChanged(data) {
    const { overallStatus, pinStatuses } = data;
    
    // Update team statuses based on pin health
    for (const [teamId, team] of this.teams) {
      if (team.pins && team.pins.length > 0) {
        const teamPinStatuses = team.pins.map(pin => pinStatuses[pin] || 'unknown');
        team.hardwareHealth = teamPinStatuses.every(status => status === 'connected') ? 'healthy' : 'unhealthy';
        this.updateTeamTestDisplay(teamId);
      }
    }
    
    this.emitHardwareStatusEvent();
  }

  addTeam(teamData) {
    const team = {
      id: teamData.id,
      name: teamData.name,
      pins: teamData.pins || [],
      color: teamData.color,
      pinStatus: 'unknown',
      hardwareHealth: 'unknown'
    };
    
    this.teams.set(team.id, team);
    this.updateDisplay();
  }

  removeTeam(teamId) {
    this.teams.delete(teamId);
    this.testResults.delete(teamId);
    this.activeTests.delete(teamId);
    this.updateDisplay();
    this.updateTestStats();
  }

  updateTeam(teamData) {
    if (this.teams.has(teamData.id)) {
      const existingTeam = this.teams.get(teamData.id);
      this.teams.set(teamData.id, { ...existingTeam, ...teamData });
      this.updateTeamTestDisplay(teamData.id);
    }
  }

  syncTeams(teamsArray) {
    // Clear existing teams and add new ones
    this.teams.clear();
    this.testResults.clear();
    this.activeTests.clear();
    
    teamsArray.forEach(team => {
      this.addTeam(team);
    });
  }

  updateDisplay() {
    if (this.teams.size === 0) {
      this.noTeamsMessage.style.display = 'block';
      this.teamsTestList.style.display = 'none';
      this.testAllButton.disabled = true;
    } else {
      this.noTeamsMessage.style.display = 'none';
      this.teamsTestList.style.display = 'block';
      this.testAllButton.disabled = !this.state.isConnected || this.state.testInProgress;
      this.updateTeamsTestList();
    }
    
    this.updateTestStats();
    this.updateTestStatus();
  }

  updateTeamsTestList() {
    this.teamsTestList.innerHTML = '';
    
    Array.from(this.teams.values()).forEach(team => {
      const teamElement = this.createTeamTestElement(team);
      this.teamsTestList.appendChild(teamElement);
    });
  }

  createTeamTestElement(team) {
    const isTestingThisTeam = this.activeTests.has(team.id);
    const testResult = this.testResults.get(team.id);
    
    let statusClass = '';
    let statusIndicator = '?';
    let resultMessage = '';
    
    if (isTestingThisTeam) {
      statusClass = 'testing';
      statusIndicator = '⟳';
    } else if (testResult) {
      statusClass = testResult.success ? 'passed' : 'failed';
      statusIndicator = testResult.success ? '✓' : '✗';
      resultMessage = testResult.details || (testResult.success ? 'Circuit test passed' : 'Circuit test failed');
    }
    
    const teamItem = document.createElement('div');
    teamItem.className = `team-test-item ${statusClass}`;
    teamItem.dataset.teamId = team.id;
    
    teamItem.innerHTML = `
      <div class="team-test-info">
        <div class="team-test-name">
          <div class="team-color-dot" style="background-color: ${team.color}"></div>
          ${this.escapeHtml(team.name)}
        </div>
        <div class="team-test-details">
          Pin: ${team.pins.join(', ') || 'None'} | Status: ${team.pinStatus || 'Unknown'}
        </div>
        <div class="test-result-message ${testResult ? (testResult.success ? 'success' : 'error') : ''}">
          ${resultMessage}
        </div>
      </div>
      <div class="test-actions">
        <div class="test-status-indicator ${statusClass}">
          ${statusIndicator}
        </div>
        <button type="button" class="btn btn-primary test-btn ${isTestingThisTeam ? 'testing' : ''}" 
                ${!this.state.isConnected || isTestingThisTeam ? 'disabled' : ''}>
          ${isTestingThisTeam ? 'Testing...' : 'Test Circuit'}
        </button>
      </div>
    `;
    
    // Add test button event listener
    const testButton = teamItem.querySelector('.test-btn');
    testButton.addEventListener('click', () => {
      this.testTeamCircuit(team.id);
    });
    
    return teamItem;
  }

  updateTeamTestDisplay(teamId) {
    const teamElement = this.teamsTestList.querySelector(`[data-team-id="${teamId}"]`);
    if (teamElement && this.teams.has(teamId)) {
      const team = this.teams.get(teamId);
      const newElement = this.createTeamTestElement(team);
      teamElement.replaceWith(newElement);
    }
  }

  testTeamCircuit(teamId) {
    if (!this.state.isConnected || this.activeTests.has(teamId)) return;
    
    const team = this.teams.get(teamId);
    if (!team || !team.pins || team.pins.length === 0) return;
    
    this.activeTests.add(teamId);
    this.updateTeamTestDisplay(teamId);
    this.updateTestStatus();
    
    // Send test command via WebSocket
    const testCommand = {
      type: 'test_team_circuit',
      teamId: teamId,
      pinConfig: team.pins
    };
    
    this.websocket.send(JSON.stringify(testCommand));
    
    // Set timeout for test
    setTimeout(() => {
      if (this.activeTests.has(teamId)) {
        this.activeTests.delete(teamId);
        this.testResults.set(teamId, {
          success: false,
          details: 'Test timeout - no response from hardware',
          timestamp: Date.now()
        });
        this.updateTeamTestDisplay(teamId);
        this.updateTestStats();
        this.updateTestStatus();
      }
    }, 10000); // 10 second timeout
  }

  testAllTeams() {
    if (!this.state.isConnected || this.state.testInProgress) return;
    
    this.state.testInProgress = true;
    this.testAllButton.disabled = true;
    
    // Clear previous results
    this.testResults.clear();
    
    // Start testing all teams
    for (const teamId of this.teams.keys()) {
      this.testTeamCircuit(teamId);
    }
    
    // Monitor for completion
    this.checkTestCompletion();
  }

  checkTestCompletion() {
    if (this.activeTests.size === 0) {
      this.state.testInProgress = false;
      this.testAllButton.disabled = !this.state.isConnected;
      this.updateTestStatus();
      return;
    }
    
    // Check again in 1 second
    setTimeout(() => {
      this.checkTestCompletion();
    }, 1000);
  }

  updateTestStats() {
    const stats = { passed: 0, failed: 0, pending: 0 };
    
    for (const team of this.teams.values()) {
      const result = this.testResults.get(team.id);
      
      if (this.activeTests.has(team.id)) {
        stats.pending++;
      } else if (result) {
        if (result.success) {
          stats.passed++;
        } else {
          stats.failed++;
        }
      }
    }
    
    this.state.stats = stats;
    
    // Update stats display
    const passedElement = this.resultsStats.querySelector('.stat.passed');
    const failedElement = this.resultsStats.querySelector('.stat.failed');
    const pendingElement = this.resultsStats.querySelector('.stat.pending');
    
    if (passedElement) passedElement.textContent = `${stats.passed} Passed`;
    if (failedElement) failedElement.textContent = `${stats.failed} Failed`;
    if (pendingElement) pendingElement.textContent = `${stats.pending} Pending`;
  }

  updateTestStatus() {
    let statusText = 'Ready to test';
    let statusClass = '';
    
    if (this.activeTests.size > 0) {
      statusText = `Testing ${this.activeTests.size} team(s)...`;
      statusClass = 'testing';
    } else if (this.testResults.size > 0) {
      const hasFailures = Array.from(this.testResults.values()).some(result => !result.success);
      statusText = hasFailures ? 'Tests completed with issues' : 'All tests passed';
      statusClass = hasFailures ? 'error' : 'complete';
    }
    
    this.testStatusElement.textContent = statusText;
    this.testStatusElement.className = `test-status ${statusClass}`;
  }

  updateConnectionStatus() {
    let statusText = 'Hardware connection: Disconnected';
    let dotClass = 'disconnected';
    
    if (this.state.isConnecting) {
      statusText = 'Hardware connection: Connecting...';
      dotClass = 'connecting';
    } else if (this.state.isConnected) {
      statusText = 'Hardware connection: Connected';
      dotClass = 'connected';
    }
    
    this.statusText.textContent = statusText;
    this.statusDot.className = `status-dot ${dotClass}`;
    
    // Show/hide reconnect button
    this.reconnectButton.style.display = this.state.isConnected ? 'none' : 'inline-flex';
    
    // Update test buttons
    this.testAllButton.disabled = !this.state.isConnected || this.state.testInProgress || this.teams.size === 0;
  }

  reconnectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
    }
    this.initializeWebSocket();
  }

  emitHardwareStatusEvent() {
    const connectedCount = Array.from(this.teams.values())
      .filter(team => team.pinStatus === 'connected').length;
    
    const event = new CustomEvent('hardware_status_changed', {
      detail: {
        statusCount: {
          connected: connectedCount,
          total: this.teams.size
        },
        teams: Array.from(this.teams.values())
      },
      bubbles: true
    });
    
    this.element.dispatchEvent(event);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API methods
  getTestResults() {
    return Array.from(this.testResults.entries()).map(([teamId, result]) => ({
      teamId,
      ...result
    }));
  }

  getConnectionStatus() {
    return {
      isConnected: this.state.isConnected,
      isConnecting: this.state.isConnecting
    };
  }

  getTestStats() {
    return { ...this.state.stats };
  }

  // Cleanup method
  destroy() {
    if (this.websocket) {
      this.websocket.close();
    }
  }
}
