/**
 * TeamManagementButton Component JavaScript
 * Handles team registration status display and navigation to team management
 */

class TeamManagementButton {
    constructor() {
        this.teamData = {
            count: 0,
            teams: [],
            hardwareStatus: {}
        };
        
        this.summaryVisible = false;
        
        this.init();
    }
    
    /**
     * Initialize the component
     */
    init() {
        this.bindEvents();
        this.updateDisplay();
        
        console.log('TeamManagementButton initialized');
    }
    
    /**
     * Bind event handlers
     */
    bindEvents() {
        // Main button click
        const mainBtn = document.getElementById('teamManagementBtn');
        if (mainBtn) {
            mainBtn.addEventListener('click', () => {
                this.handleMainButtonClick();
            });
        }
        
        // Quick action buttons
        const addTeamBtn = document.getElementById('addTeamBtn');
        if (addTeamBtn) {
            addTeamBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleAddTeamClick();
            });
        }
        
        const testHardwareBtn = document.getElementById('testHardwareBtn');
        if (testHardwareBtn) {
            testHardwareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleTestHardwareClick();
            });
        }
        
        // Listen for homepage status updates
        document.addEventListener('homepage_status_update', (event) => {
            this.handleStatusUpdate(event.detail);
        });
        
        // Listen for team-specific updates
        document.addEventListener('team_registered', (event) => {
            this.handleTeamRegistered(event.detail);
        });
        
        document.addEventListener('team_removed', (event) => {
            this.handleTeamRemoved(event.detail);
        });
        
        document.addEventListener('team_count_changed', (event) => {
            this.handleTeamCountChanged(event.detail);
        });
        
        document.addEventListener('hardware_status_update', (event) => {
            this.handleHardwareUpdate(event.detail);
        });
        
        // Hover effects for showing team summary
        if (mainBtn) {
            mainBtn.addEventListener('mouseenter', () => {
                if (this.teamData.count > 0) {
                    this.showTeamSummary();
                }
            });
            
            mainBtn.addEventListener('mouseleave', () => {
                this.hideTeamSummary();
            });
        }
    }
    
    /**
     * Handle main button click - navigate to team management
     */
    handleMainButtonClick() {
        console.log('Team management button clicked');
        
        // Set loading state
        this.setLoadingState(true);
        
        // Dispatch custom event for navigation
        document.dispatchEvent(new CustomEvent('team_management_requested', {
            detail: {
                source: 'team_management_button',
                current_teams: this.teamData.count
            }
        }));
        
        // Navigate after short delay for visual feedback
        setTimeout(() => {
            this.navigateToTeamManagement();
        }, 300);
    }
    
    /**
     * Handle add team quick action
     */
    handleAddTeamClick() {
        console.log('Quick add team clicked');
        
        // Dispatch event for quick team addition
        document.dispatchEvent(new CustomEvent('quick_add_team_requested', {
            detail: {
                source: 'team_management_button'
            }
        }));
        
        // For now, navigate to team management
        this.navigateToTeamManagement();
    }
    
    /**
     * Handle test hardware quick action
     */
    handleTestHardwareClick() {
        console.log('Test hardware clicked');
        
        // Dispatch event for hardware testing
        document.dispatchEvent(new CustomEvent('hardware_test_requested', {
            detail: {
                source: 'team_management_button',
                test_type: 'quick_test'
            }
        }));
        
        // Show testing feedback
        this.showAlert('info', 'Testing hardware connections...');
        
        // Simulate hardware test (replace with actual implementation)
        setTimeout(() => {
            this.showAlert('success', 'Hardware test completed successfully!');
        }, 2000);
    }
    
    /**
     * Navigate to team management page
     */
    navigateToTeamManagement() {
        // Implement based on your routing system
        window.location.href = '/team-management';
    }
    
    /**
     * Handle status updates from homepage
     */
    handleStatusUpdate(statusData) {
        console.log('TeamManagementButton received status update:', statusData);
        
        if (statusData.teams !== undefined) {
            this.teamData.count = statusData.teams;
        }
        
        if (statusData.hardware) {
            this.teamData.hardwareStatus = statusData.hardware;
        }
        
        this.updateDisplay();
    }
    
    /**
     * Handle team registration event
     */
    handleTeamRegistered(teamData) {
        console.log('Team registered:', teamData);
        
        this.teamData.count = teamData.team_count || this.teamData.count + 1;
        
        // Add team to list if provided
        if (teamData.team_info) {
            this.teamData.teams.push(teamData.team_info);
        }
        
        this.updateDisplay();
        this.showAlert('success', `Team "${teamData.team_name || 'New Team'}" registered successfully!`);
    }
    
    /**
     * Handle team removal event
     */
    handleTeamRemoved(teamData) {
        console.log('Team removed:', teamData);
        
        this.teamData.count = teamData.team_count || Math.max(0, this.teamData.count - 1);
        
        // Remove team from list if provided
        if (teamData.team_id) {
            this.teamData.teams = this.teamData.teams.filter(team => team.id !== teamData.team_id);
        }
        
        this.updateDisplay();
        this.showAlert('info', `Team removed. ${this.teamData.count} teams remaining.`);
    }
    
    /**
     * Handle team count change event
     */
    handleTeamCountChanged(data) {
        this.teamData.count = data.count || data.team_count || 0;
        this.teamData.teams = data.teams || this.teamData.teams;
        
        this.updateDisplay();
    }
    
    /**
     * Handle hardware status update
     */
    handleHardwareUpdate(hardwareData) {
        this.teamData.hardwareStatus = hardwareData;
        this.updateDisplay();
    }
    
    /**
     * Update the component display
     */
    updateDisplay() {
        this.updateButtonContent();
        this.updateTeamCountBadge();
        this.updateStatusIndicator();
        this.updateTeamIndicators();
        this.updateTeamSummaryContent();
    }
    
    /**
     * Update button content based on team count
     */
    updateButtonContent() {
        const description = document.getElementById('teamBtnDescription');
        if (!description) return;
        
        const count = this.teamData.count;
        
        let descriptionText = 'No teams registered';
        
        if (count === 0) {
            descriptionText = 'Click to register teams';
        } else if (count === 1) {
            descriptionText = '1 team registered (need 2+ to play)';
        } else if (count >= 2) {
            descriptionText = `${count} teams ready to play`;
        }
        
        description.textContent = descriptionText;
    }
    
    /**
     * Update team count badge
     */
    updateTeamCountBadge() {
        const badge = document.getElementById('teamCountBadge');
        const badgeNumber = document.getElementById('badgeNumber');
        
        if (!badge || !badgeNumber) return;
        
        const count = this.teamData.count;
        badgeNumber.textContent = count;
        
        // Remove existing classes
        badge.classList.remove('has-teams', 'ready');
        
        // Add appropriate class based on count
        if (count >= 2) {
            badge.classList.add('ready');
        } else if (count > 0) {
            badge.classList.add('has-teams');
        }
    }
    
    /**
     * Update status indicator
     */
    updateStatusIndicator() {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        if (!statusDot || !statusText) return;
        
        const count = this.teamData.count;
        const hardwareOk = this.isHardwareOperational();
        
        // Remove existing status classes
        statusDot.classList.remove('status-operational', 'status-warning', 'status-error', 'status-checking');
        
        let status = 'error';
        let text = 'Setup Required';
        
        if (count >= 2 && hardwareOk) {
            status = 'operational';
            text = 'Ready to Play';
        } else if (count >= 2 && !hardwareOk) {
            status = 'warning';
            text = 'Hardware Issues';
        } else if (count === 1) {
            status = 'warning';
            text = 'Need More Teams';
        } else {
            status = 'error';
            text = 'Setup Required';
        }
        
        statusDot.classList.add(`status-${status}`);
        statusText.textContent = text;
    }
    
    /**
     * Update team status indicators
     */
    updateTeamIndicators() {
        const indicators = document.getElementById('teamStatusIndicators');
        if (!indicators) return;
        
        // Clear existing indicators
        indicators.innerHTML = '';
        
        // Create indicators for each team
        for (let i = 1; i <= Math.min(this.teamData.count, 8); i++) {
            const indicator = document.createElement('div');
            indicator.className = 'team-indicator';
            indicator.title = `Team ${i} hardware status`;
            
            // Check hardware status for this team
            const hardwareStatus = this.getTeamHardwareStatus(i);
            indicator.classList.add(hardwareStatus);
            
            indicators.appendChild(indicator);
        }
    }
    
    /**
     * Update team summary content
     */
    updateTeamSummaryContent() {
        const teamList = document.getElementById('teamList');
        if (!teamList) return;
        
        // Clear existing content
        teamList.innerHTML = '';
        
        // Add team items
        this.teamData.teams.forEach((team, index) => {
            const teamItem = this.createTeamItem(team, index + 1);
            teamList.appendChild(teamItem);
        });
        
        // If we have team count but no detailed team data, create placeholder items
        if (this.teamData.count > this.teamData.teams.length) {
            for (let i = this.teamData.teams.length; i < this.teamData.count; i++) {
                const placeholderTeam = {
                    name: `Team ${i + 1}`,
                    id: i + 1,
                    status: 'unknown'
                };
                const teamItem = this.createTeamItem(placeholderTeam, i + 1);
                teamList.appendChild(teamItem);
            }
        }
    }
    
    /**
     * Create team item element
     */
    createTeamItem(team, teamNumber) {
        const item = document.createElement('div');
        item.className = 'team-item';
        
        const hardwareStatus = this.getTeamHardwareStatus(teamNumber);
        
        item.innerHTML = `
            <div class="team-color team-${teamNumber}"></div>
            <span class="team-name">${team.name || `Team ${teamNumber}`}</span>
            <span class="team-status ${hardwareStatus}">${hardwareStatus}</span>
        `;
        
        return item;
    }
    
    /**
     * Get hardware status for specific team
     */
    getTeamHardwareStatus(teamNumber) {
        const gpioStatus = this.teamData.hardwareStatus?.gpio;
        if (!gpioStatus) return 'unknown';
        
        const pinStatus = gpioStatus[`pin_${teamNumber}`];
        return pinStatus === 'connected' ? 'connected' : 
               pinStatus === 'disconnected' ? 'disconnected' : 'pending';
    }
    
    /**
     * Check if hardware is operational
     */
    isHardwareOperational() {
        const hardwareStatus = this.teamData.hardwareStatus?.status;
        return hardwareStatus === 'operational' || hardwareStatus === 'connected';
    }
    
    /**
     * Show team summary
     */
    showTeamSummary() {
        if (this.summaryVisible || this.teamData.count === 0) return;
        
        const summary = document.getElementById('teamSummary');
        if (summary) {
            summary.style.display = 'block';
            this.summaryVisible = true;
        }
    }
    
    /**
     * Hide team summary
     */
    hideTeamSummary() {
        if (!this.summaryVisible) return;
        
        const summary = document.getElementById('teamSummary');
        if (summary) {
            summary.style.display = 'none';
            this.summaryVisible = false;
        }
    }
    
    /**
     * Set loading state
     */
    setLoadingState(loading) {
        const button = document.getElementById('teamManagementBtn');
        if (!button) return;
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }
    
    /**
     * Show alert message
     */
    showAlert(type, message) {
        const alertsContainer = document.getElementById('teamAlerts');
        if (!alertsContainer) return;
        
        // Remove existing alerts
        alertsContainer.innerHTML = '';
        
        // Create new alert
        const alert = document.createElement('div');
        alert.className = `team-alert alert-${type}`;
        alert.textContent = message;
        alert.setAttribute('role', 'alert');
        
        alertsContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    /**
     * Update button based on system readiness
     */
    updateButtonState(systemReady) {
        const button = document.getElementById('teamManagementBtn');
        if (!button) return;
        
        if (systemReady) {
            button.classList.remove('disabled');
            button.disabled = false;
        } else {
            // Don't disable team management - it's always accessible
            // Just update visual indicators
        }
    }
    
    /**
     * Get team management summary for other components
     */
    getTeamSummary() {
        return {
            count: this.teamData.count,
            teams: this.teamData.teams,
            ready: this.teamData.count >= 2 && this.isHardwareOperational(),
            hardware_status: this.teamData.hardwareStatus
        };
    }
    
    /**
     * Cleanup method
     */
    destroy() {
        // Remove event listeners and cleanup
        this.hideTeamSummary();
    }
}

// Initialize TeamManagementButton when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.teamManagementButton) {
        window.teamManagementButton = new TeamManagementButton();
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TeamManagementButton;
}