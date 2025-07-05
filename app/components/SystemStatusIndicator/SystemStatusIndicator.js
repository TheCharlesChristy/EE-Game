/**
 * SystemStatusIndicator Component JavaScript
 * Monitors and displays real-time system health, hardware status, and connectivity
 */

class SystemStatusIndicator {
    constructor() {
        this.statusData = {
            system: { status: 'unknown', uptime: 0 },
            hardware: { status: 'unknown', gpio: {} },
            network: { status: 'unknown', latency: null, reconnectAttempts: 0 },
            teams: { count: 0, registered: [] },
            games: { 'reaction-timer': 'unknown', 'wheel-game': 'unknown', 'quiz-game': 'unknown' }
        };
        
        this.updateInterval = null;
        this.latencyCheckInterval = null;
        this.detailsVisible = false;
        
        this.init();
    }
    
    /**
     * Initialize the component
     */
    init() {
        this.bindEvents();
        this.setupPeriodicUpdates();
        this.initializeGPIOGrid();
        this.updateDisplay();
        
        console.log('SystemStatusIndicator initialized');
    }
    
    /**
     * Bind event handlers
     */
    bindEvents() {
        // Details toggle
        const detailsToggle = document.getElementById('detailsToggle');
        if (detailsToggle) {
            detailsToggle.addEventListener('click', () => {
                this.toggleDetails();
            });
        }
        
        // Listen for homepage status updates
        document.addEventListener('homepage_status_update', (event) => {
            this.handleStatusUpdate(event.detail);
        });
        
        // Listen for system status updates
        document.addEventListener('system_status_changed', (event) => {
            this.handleStatusUpdate(event.detail);
        });
        
        // Listen for hardware status updates
        document.addEventListener('hardware_status_update', (event) => {
            this.handleHardwareUpdate(event.detail);
        });
        
        // Listen for network status changes
        document.addEventListener('network_status_change', (event) => {
            this.handleNetworkUpdate(event.detail);
        });
        
        // Listen for team updates
        document.addEventListener('team_count_changed', (event) => {
            this.handleTeamUpdate(event.detail);
        });
    }
    
    /**
     * Setup periodic status updates
     */
    setupPeriodicUpdates() {
        // Update display every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateDisplay();
            this.checkLatency();
        }, 5000);
        
        // Check network latency every 10 seconds
        this.latencyCheckInterval = setInterval(() => {
            this.measureLatency();
        }, 10000);
    }
    
    /**
     * Initialize GPIO status grid
     */
    initializeGPIOGrid() {
        const gpioGrid = document.getElementById('gpioGrid');
        if (!gpioGrid) return;
        
        // Create GPIO pin status indicators for 8 teams
        for (let i = 1; i <= 8; i++) {
            const pinElement = document.createElement('div');
            pinElement.className = 'gpio-pin unused';
            pinElement.id = `gpio-pin-${i}`;
            pinElement.innerHTML = `
                <div class="pin-label">Pin ${i}</div>
                <div class="pin-status">--</div>
            `;
            pinElement.title = `GPIO Pin ${i} - Team ${i} hardware connection`;
            gpioGrid.appendChild(pinElement);
        }
    }
    
    /**
     * Handle status updates from the homepage
     */
    handleStatusUpdate(statusData) {
        console.log('SystemStatusIndicator received status update:', statusData);
        
        // Update internal status data
        Object.assign(this.statusData, statusData);
        
        // Update display
        this.updateDisplay();
        
        // Check for alerts
        this.checkForAlerts(statusData);
    }
    
    /**
     * Handle hardware-specific updates
     */
    handleHardwareUpdate(hardwareData) {
        this.statusData.hardware = { ...this.statusData.hardware, ...hardwareData };
        this.updateHardwareDisplay();
        this.updateGPIODisplay();
    }
    
    /**
     * Handle network-specific updates
     */
    handleNetworkUpdate(networkData) {
        this.statusData.network = { ...this.statusData.network, ...networkData };
        this.updateNetworkDisplay();
    }
    
    /**
     * Handle team-specific updates
     */
    handleTeamUpdate(teamData) {
        this.statusData.teams = { ...this.statusData.teams, ...teamData };
        this.updateTeamDisplay();
    }
    
    /**
     * Update the main display
     */
    updateDisplay() {
        this.updateSystemHealth();
        this.updateHardwareDisplay();
        this.updateNetworkDisplay();
        this.updateTeamDisplay();
        this.updateGameAvailability();
        this.updateDetailedInfo();
    }
    
    /**
     * Update overall system health indicator
     */
    updateSystemHealth() {
        const healthIcon = document.getElementById('systemHealthIcon');
        const healthText = document.getElementById('systemHealthText');
        const systemHealthItem = document.querySelector('.system-health');
        
        if (!healthIcon || !healthText || !systemHealthItem) return;
        
        // Determine overall system status
        let overallStatus = 'operational';
        let statusText = 'All systems operational';
        
        if (this.statusData.network.status === 'error' || 
            this.statusData.hardware.status === 'error') {
            overallStatus = 'error';
            statusText = 'System errors detected';
        } else if (this.statusData.network.status === 'warning' || 
                   this.statusData.hardware.status === 'warning' ||
                   this.statusData.teams.count < 2) {
            overallStatus = 'warning';
            statusText = 'System warnings present';
        } else if (this.statusData.network.status === 'unknown' || 
                   this.statusData.hardware.status === 'unknown') {
            overallStatus = 'checking';
            statusText = 'Checking system status...';
        }
        
        // Update display
        this.updateStatusItem(systemHealthItem, overallStatus);
        healthText.textContent = statusText;
        
        // Update icon symbol based on status
        const iconSymbol = healthIcon.querySelector('.icon-symbol');
        if (iconSymbol) {
            iconSymbol.textContent = overallStatus === 'operational' ? '✓' : 
                                   overallStatus === 'error' ? '✗' : 
                                   overallStatus === 'warning' ? '⚠' : '●';
        }
    }
    
    /**
     * Update hardware status display
     */
    updateHardwareDisplay() {
        const hardwareText = document.getElementById('hardwareStatusText');
        const hardwareItem = document.querySelector('.hardware-status');
        const gpioStatus = document.getElementById('gpioStatus');
        const gpioCount = document.getElementById('gpioCount');
        
        if (!hardwareText || !hardwareItem) return;
        
        const status = this.statusData.hardware.status || 'unknown';
        let statusText = 'Hardware status unknown';
        
        switch (status) {
            case 'operational':
                statusText = 'Hardware connected';
                break;
            case 'error':
                statusText = 'Hardware connection failed';
                break;
            case 'warning':
                statusText = 'Hardware issues detected';
                break;
            case 'checking':
                statusText = 'Checking hardware...';
                break;
        }
        
        this.updateStatusItem(hardwareItem, status);
        hardwareText.textContent = statusText;
        
        // Update GPIO count
        if (gpioStatus && gpioCount) {
            const connectedPins = Object.values(this.statusData.hardware.gpio || {})
                .filter(pin => pin === 'connected').length;
            gpioCount.textContent = connectedPins;
            gpioStatus.style.display = connectedPins > 0 ? 'block' : 'none';
        }
    }
    
    /**
     * Update network status display
     */
    updateNetworkDisplay() {
        const networkText = document.getElementById('networkStatusText');
        const networkItem = document.querySelector('.network-status');
        const connectionDetail = document.getElementById('connectionDetail');
        const latencyValue = document.getElementById('latencyValue');
        
        if (!networkText || !networkItem) return;
        
        const status = this.statusData.network.status || 'unknown';
        let statusText = 'Connection status unknown';
        
        switch (status) {
            case 'connected':
                statusText = 'Connected to server';
                break;
            case 'disconnected':
                statusText = 'Disconnected from server';
                break;
            case 'error':
                statusText = 'Connection error';
                break;
            case 'connecting':
                statusText = 'Connecting to server...';
                break;
        }
        
        this.updateStatusItem(networkItem, status === 'connected' ? 'operational' : 
                            status === 'connecting' ? 'checking' : 'error');
        networkText.textContent = statusText;
        
        // Update latency display
        if (connectionDetail && latencyValue) {
            if (this.statusData.network.latency !== null) {
                latencyValue.textContent = this.statusData.network.latency;
                connectionDetail.style.display = 'block';
            } else {
                connectionDetail.style.display = 'none';
            }
        }
    }
    
    /**
     * Update team status display
     */
    updateTeamDisplay() {
        const teamText = document.getElementById('teamStatusText');
        const teamItem = document.querySelector('.team-status');
        const teamDetail = document.getElementById('teamDetail');
        const teamCount = document.getElementById('teamCount');
        
        if (!teamText || !teamItem) return;
        
        const count = this.statusData.teams.count || 0;
        let status = 'error';
        let statusText = 'No teams registered';
        
        if (count >= 2) {
            status = 'operational';
            statusText = `${count} teams ready to play`;
        } else if (count === 1) {
            status = 'warning';
            statusText = '1 team registered (need 2+)';
        }
        
        this.updateStatusItem(teamItem, status);
        teamText.textContent = statusText;
        
        // Update team detail
        if (teamDetail && teamCount) {
            teamCount.textContent = count;
            teamDetail.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    /**
     * Update game availability display
     */
    updateGameAvailability() {
        const gameStatuses = document.querySelectorAll('.game-status');
        
        gameStatuses.forEach(statusEl => {
            const game = statusEl.getAttribute('data-game');
            const gameStatus = this.statusData.games[game] || 'unknown';
            
            // Remove existing status classes
            statusEl.classList.remove('available', 'unavailable', 'checking');
            
            let statusText = 'Unknown';
            let statusClass = 'checking';
            
            // Determine game availability based on overall system status
            const systemReady = this.statusData.network.status === 'connected' &&
                              this.statusData.hardware.status === 'operational' &&
                              this.statusData.teams.count >= 2;
            
            if (systemReady) {
                statusText = 'Available';
                statusClass = 'available';
            } else {
                statusText = 'Unavailable';
                statusClass = 'unavailable';
            }
            
            statusEl.textContent = statusText;
            statusEl.classList.add(statusClass);
        });
    }
    
    /**
     * Update detailed information section
     */
    updateDetailedInfo() {
        // Update system information
        const systemUptime = document.getElementById('systemUptime');
        const lastUpdate = document.getElementById('lastUpdate');
        const reconnectAttempts = document.getElementById('reconnectAttempts');
        const detailNetworkStatus = document.getElementById('detailNetworkStatus');
        
        if (systemUptime) {
            const uptime = this.formatUptime(this.statusData.system.uptime || 0);
            systemUptime.textContent = uptime;
        }
        
        if (lastUpdate) {
            lastUpdate.textContent = new Date().toLocaleTimeString();
        }
        
        if (reconnectAttempts) {
            reconnectAttempts.textContent = this.statusData.network.reconnectAttempts || 0;
        }
        
        if (detailNetworkStatus) {
            detailNetworkStatus.textContent = this.statusData.network.status || 'Unknown';
        }
        
        // Update GPIO grid
        this.updateGPIODisplay();
    }
    
    /**
     * Update GPIO pin display
     */
    updateGPIODisplay() {
        for (let i = 1; i <= 8; i++) {
            const pinElement = document.getElementById(`gpio-pin-${i}`);
            if (!pinElement) continue;
            
            const pinStatus = this.statusData.hardware.gpio?.[`pin_${i}`] || 'unused';
            const statusText = pinElement.querySelector('.pin-status');
            
            // Remove existing status classes
            pinElement.classList.remove('connected', 'disconnected', 'unused');
            
            // Add new status class and update text
            pinElement.classList.add(pinStatus);
            if (statusText) {
                statusText.textContent = pinStatus === 'connected' ? '✓' : 
                                       pinStatus === 'disconnected' ? '✗' : '--';
            }
        }
    }
    
    /**
     * Update status item with new status
     */
    updateStatusItem(item, status) {
        // Remove existing status classes
        item.classList.remove('status-operational', 'status-warning', 'status-error', 'status-unknown', 'status-checking');
        
        // Add new status class
        item.classList.add(`status-${status}`);
    }
    
    /**
     * Toggle details section visibility
     */
    toggleDetails() {
        this.detailsVisible = !this.detailsVisible;
        
        const detailsContent = document.getElementById('detailsContent');
        const detailsToggle = document.getElementById('detailsToggle');
        const toggleText = detailsToggle?.querySelector('.toggle-text');
        
        if (detailsContent) {
            if (this.detailsVisible) {
                detailsContent.classList.add('show');
                detailsContent.style.display = 'block';
            } else {
                detailsContent.classList.remove('show');
                detailsContent.style.display = 'none';
            }
        }
        
        if (detailsToggle) {
            detailsToggle.setAttribute('aria-expanded', this.detailsVisible.toString());
        }
        
        if (toggleText) {
            toggleText.textContent = this.detailsVisible ? 'Hide Details' : 'Show Details';
        }
    }
    
    /**
     * Check for system alerts
     */
    checkForAlerts(statusData) {
        const alerts = [];
        
        // Check for hardware issues
        if (statusData.hardware === 'error') {
            alerts.push({
                type: 'error',
                message: 'Hardware connection failed. Check GPIO connections.'
            });
        }
        
        // Check for network issues
        if (statusData.connection === 'error') {
            alerts.push({
                type: 'error',
                message: 'Lost connection to server. Attempting to reconnect...'
            });
        }
        
        // Check for insufficient teams
        if (statusData.teams < 2) {
            alerts.push({
                type: 'warning',
                message: 'At least 2 teams required to start games.'
            });
        }
        
        // Display alerts
        this.displayAlerts(alerts);
    }
    
    /**
     * Display alerts
     */
    displayAlerts(alerts) {
        const alertsContainer = document.getElementById('statusAlerts');
        if (!alertsContainer) return;
        
        // Clear existing alerts
        alertsContainer.innerHTML = '';
        
        // Add new alerts
        alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `status-alert alert-${alert.type}`;
            alertElement.textContent = alert.message;
            alertElement.setAttribute('role', 'alert');
            alertsContainer.appendChild(alertElement);
        });
    }
    
    /**
     * Measure network latency
     */
    measureLatency() {
        if (window.homePage?.socket?.connected) {
            const startTime = Date.now();
            
            window.homePage.socket.emit('ping', { timestamp: startTime });
            
            window.homePage.socket.once('pong', (data) => {
                const latency = Date.now() - data.timestamp;
                this.statusData.network.latency = latency;
                this.updateNetworkDisplay();
            });
        }
    }
    
    /**
     * Check latency status
     */
    checkLatency() {
        const latency = this.statusData.network.latency;
        if (latency !== null) {
            // Update network status based on latency
            if (latency > 1000) {
                this.statusData.network.status = 'warning';
            } else if (this.statusData.network.status !== 'connected') {
                this.statusData.network.status = 'connected';
            }
        }
    }
    
    /**
     * Format uptime in human-readable format
     */
    formatUptime(seconds) {
        if (seconds === 0) return 'Just started';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    /**
     * Cleanup method
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.latencyCheckInterval) {
            clearInterval(this.latencyCheckInterval);
        }
    }
}

// Initialize SystemStatusIndicator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.systemStatusIndicator) {
        window.systemStatusIndicator = new SystemStatusIndicator();
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemStatusIndicator;
}