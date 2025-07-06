class LEDStatusIndicator {
    constructor() {
        this.element = null;
        this.gridElement = null;
        this.connectionIndicator = null;
        this.connectionText = null;
        this.testAllBtn = null;
        this.resetLedsBtn = null;
        
        this.ledStatuses = new Map();
        this.hardwareStatus = 'disconnected';
        this.gpioConnections = {};
        
        this.init();
    }

    init() {
        this.element = document.getElementById('ledStatusIndicator');
        this.gridElement = document.getElementById('ledGrid');
        this.connectionIndicator = document.getElementById('connectionIndicator');
        this.connectionText = document.getElementById('connectionText');
        this.testAllBtn = document.getElementById('testAllBtn');
        this.resetLedsBtn = document.getElementById('resetLedsBtn');
        
        if (!this.element) {
            console.error('LEDStatusIndicator: Element not found');
            return;
        }

        this.setupEventListeners();
        this.updateConnectionStatus();
        this.loadInitialStatus();
    }

    setupEventListeners() {
        // Button event listeners
        if (this.testAllBtn) {
            this.testAllBtn.addEventListener('click', () => this.handleTestAllLEDs());
        }
        
        if (this.resetLedsBtn) {
            this.resetLedsBtn.addEventListener('click', () => this.handleResetLEDs());
        }

        // WebSocket event listeners
        if (window.socketManager) {
            window.socketManager.on('led_status_update', (data) => {
                this.handleLEDStatusUpdate(data);
            });

            window.socketManager.on('hardware_status_change', (data) => {
                this.handleHardwareStatusChange(data);
            });

            window.socketManager.on('gpio_status_update', (data) => {
                this.handleGPIOStatusUpdate(data);
            });

            window.socketManager.on('led_test_response', (data) => {
                this.handleLEDTestResponse(data);
            });

            window.socketManager.on('system_status_update', (data) => {
                this.handleSystemStatusUpdate(data);
            });
        }
    }

    loadInitialStatus() {
        // Request current LED and hardware status
        if (window.socketManager) {
            window.socketManager.emit('request_led_status');
            window.socketManager.emit('request_hardware_status');
        }
    }

    handleLEDStatusUpdate(data) {
        if (data.teams) {
            // Multiple team LED statuses
            data.teams.forEach(teamStatus => {
                this.updateLEDStatus(teamStatus.team_id, teamStatus.led_status, teamStatus);
            });
        } else if (data.team_id !== undefined) {
            // Single team LED status
            this.updateLEDStatus(data.team_id, data.led_status, data);
        }
    }

    handleHardwareStatusChange(data) {
        this.hardwareStatus = data.status || 'disconnected';
        if (data.gpio) {
            this.gpioConnections = data.gpio;
        }
        this.updateConnectionStatus();
        this.updateAllCards();
    }

    handleGPIOStatusUpdate(data) {
        this.gpioConnections = data.gpio || data;
        this.updateAllCards();
    }

    handleLEDTestResponse(data) {
        if (data.status === 'success') {
            const card = document.getElementById(`led-card-${data.team_id}`);
            if (card) {
                card.classList.add('led-status-card--testing');
                setTimeout(() => {
                    card.classList.remove('led-status-card--testing');
                }, data.duration_ms || 1000);
            }
        }
    }

    handleSystemStatusUpdate(data) {
        if (data.hardware) {
            this.hardwareStatus = data.hardware.status || 'disconnected';
            this.gpioConnections = data.hardware.gpio_connections || {};
            this.updateConnectionStatus();
        }
    }

    updateLEDStatus(teamId, status, additionalData = {}) {
        const ledData = {
            team_id: teamId,
            status: status,
            team_name: additionalData.team_name,
            gpio_pin: additionalData.gpio_pin,
            connection_status: additionalData.connection_status || 'unknown',
            last_updated: Date.now(),
            ...additionalData
        };

        this.ledStatuses.set(teamId, ledData);
        this.renderLEDCard(teamId);
    }

    renderLEDCard(teamId) {
        const ledData = this.ledStatuses.get(teamId);
        if (!ledData) return;

        let card = document.getElementById(`led-card-${teamId}`);
        if (!card) {
            card = document.createElement('div');
            card.id = `led-card-${teamId}`;
            card.className = 'led-status-card';
            this.gridElement.appendChild(card);
        }

        // Update card classes
        card.className = `led-status-card led-status-card--team-${teamId}`;
        if (ledData.connection_status === 'connected') {
            card.classList.add('led-status-card--connected');
        } else {
            card.classList.add('led-status-card--disconnected');
        }

        // Determine LED status class
        const ledStatusClass = this.getLEDStatusClass(ledData.status);
        const statusText = this.getStatusText(ledData.status);

        card.innerHTML = `
            <div class="led-status-card__header">
                <h5 class="led-status-card__team-name">
                    ${ledData.team_name || `Team ${teamId}`}
                </h5>
                <span class="led-status-card__team-id">ID: ${teamId}</span>
            </div>
            
            <div class="led-status-card__led-container">
                <div class="led-status-indicator__led ${ledStatusClass}"></div>
            </div>
            
            <div class="led-status-card__status led-status-card__status--${ledData.status}">
                ${statusText}
            </div>
            
            <div class="led-status-card__gpio-info">
                GPIO Pin: <span class="led-status-card__gpio-pin">${ledData.gpio_pin || 'N/A'}</span>
            </div>
            
            <button class="led-status-card__test-button" 
                    onclick="ledStatusIndicator.testLED(${teamId})"
                    ${this.hardwareStatus !== 'connected' ? 'disabled' : ''}>
                Test LED
            </button>
        `;
    }

    getLEDStatusClass(status) {
        switch (status) {
            case 'on':
                return 'led-status-indicator__led--on';
            case 'off':
                return 'led-status-indicator__led--off';
            case 'flashing':
                return 'led-status-indicator__led--flashing';
            case 'error':
                return 'led-status-indicator__led--error';
            case 'warning':
                return 'led-status-indicator__led--warning';
            default:
                return 'led-status-indicator__led--off';
        }
    }

    getStatusText(status) {
        switch (status) {
            case 'on':
                return 'ON';
            case 'off':
                return 'OFF';
            case 'flashing':
                return 'FLASHING';
            case 'error':
                return 'ERROR';
            case 'warning':
                return 'WARNING';
            default:
                return 'UNKNOWN';
        }
    }

    updateConnectionStatus() {
        // Update connection indicator
        this.connectionIndicator.className = 'led-status-indicator__connection-indicator';
        
        switch (this.hardwareStatus) {
            case 'connected':
                this.connectionIndicator.classList.add('led-status-indicator__connection-indicator--connected');
                this.connectionText.textContent = 'Connected';
                break;
            case 'partial':
                this.connectionIndicator.classList.add('led-status-indicator__connection-indicator--partial');
                this.connectionText.textContent = 'Partial';
                break;
            case 'connecting':
                this.connectionIndicator.classList.add('led-status-indicator__connection-indicator--connecting');
                this.connectionText.textContent = 'Connecting';
                break;
            default:
                this.connectionIndicator.classList.add('led-status-indicator__connection-indicator--disconnected');
                this.connectionText.textContent = 'Disconnected';
        }

        // Update button states
        const isConnected = this.hardwareStatus === 'connected';
        if (this.testAllBtn) {
            this.testAllBtn.disabled = !isConnected;
        }
        if (this.resetLedsBtn) {
            this.resetLedsBtn.disabled = !isConnected;
        }
    }

    updateAllCards() {
        this.ledStatuses.forEach((ledData, teamId) => {
            this.renderLEDCard(teamId);
        });
    }

    handleTestAllLEDs() {
        if (this.hardwareStatus !== 'connected') {
            alert('Hardware not connected. Cannot test LEDs.');
            return;
        }

        // Disable button temporarily
        this.testAllBtn.disabled = true;
        this.testAllBtn.textContent = 'Testing...';

        // Send test command
        this.sendCommand('test_all_leds', {
            duration_ms: 1000
        });

        // Re-enable button after test duration
        setTimeout(() => {
            this.testAllBtn.disabled = false;
            this.testAllBtn.textContent = 'Test All LEDs';
        }, 2000);
    }

    handleResetLEDs() {
        if (this.hardwareStatus !== 'connected') {
            alert('Hardware not connected. Cannot reset LEDs.');
            return;
        }

        this.sendCommand('reset_all_leds');
    }

    testLED(teamId) {
        if (this.hardwareStatus !== 'connected') {
            alert('Hardware not connected. Cannot test LED.');
            return;
        }

        this.sendCommand('led_test_request', {
            team_id: teamId,
            duration_ms: 1000
        });
    }

    sendCommand(command, data = {}) {
        if (window.socketManager) {
            window.socketManager.emit(command, {
                timestamp: Date.now(),
                ...data
            });
        } else {
            console.error('SocketManager not available');
        }
    }

    // Public methods for external control
    addTeam(teamId, teamName, gpioPin) {
        this.updateLEDStatus(teamId, 'off', {
            team_name: teamName,
            gpio_pin: gpioPin,
            connection_status: 'connected'
        });
    }

    removeTeam(teamId) {
        this.ledStatuses.delete(teamId);
        const card = document.getElementById(`led-card-${teamId}`);
        if (card) {
            card.remove();
        }
    }

    setLEDState(teamId, state) {
        const ledData = this.ledStatuses.get(teamId);
        if (ledData) {
            this.updateLEDStatus(teamId, state, ledData);
        }
    }

    setAllLEDsState(state) {
        this.ledStatuses.forEach((ledData, teamId) => {
            this.updateLEDStatus(teamId, state, ledData);
        });
    }

    getHardwareStatus() {
        return {
            status: this.hardwareStatus,
            connections: this.gpioConnections,
            teamCount: this.ledStatuses.size
        };
    }

    getLEDStatuses() {
        return Array.from(this.ledStatuses.values());
    }

    clearAll() {
        this.ledStatuses.clear();
        this.gridElement.innerHTML = '';
    }

    destroy() {
        if (window.socketManager) {
            window.socketManager.off('led_status_update');
            window.socketManager.off('hardware_status_change');
            window.socketManager.off('gpio_status_update');
            window.socketManager.off('led_test_response');
            window.socketManager.off('system_status_update');
        }
    }
}

// Make instance available globally for inline event handlers
let ledStatusIndicator;
