/**
 * PageHeader Component JavaScript
 * Handles header functionality, system time display, and navigation
 */

class PageHeader {
    constructor() {
        this.timeUpdateInterval = null;
        this.currentPage = 'home';
        
        this.init();
    }
    
    init() {
        this.startTimeUpdates();
        this.bindEvents();
        this.updateBreadcrumb();
        
        console.log('PageHeader initialized');
    }
    
    /**
     * Start updating system time display
     */
    startTimeUpdates() {
        const timeElement = document.getElementById('timeValue');
        
        if (!timeElement) return;
        
        const updateTime = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timeElement.textContent = timeString;
        };
        
        // Update immediately
        updateTime();
        
        // Update every second
        this.timeUpdateInterval = setInterval(updateTime, 1000);
    }
    
    /**
     * Bind event handlers
     */
    bindEvents() {
        // Settings button
        const settingsBtn = document.querySelector('.settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.handleSettingsClick();
            });
        }
        
        // Help button
        const helpBtn = document.querySelector('.help-btn');
        if (helpBtn) {
            helpBtn.addEventListener('click', () => {
                this.handleHelpClick();
            });
        }
        
        // Listen for page navigation events
        document.addEventListener('page_changed', (event) => {
            this.updateBreadcrumb(event.detail.page);
        });
        
        // Brand logo click - return to home
        const brandTitle = document.querySelector('.brand-title');
        if (brandTitle) {
            brandTitle.style.cursor = 'pointer';
            brandTitle.addEventListener('click', () => {
                this.navigateToHome();
            });
        }
    }
    
    /**
     * Handle settings button click
     */
    handleSettingsClick() {
        // Dispatch event for settings access
        document.dispatchEvent(new CustomEvent('settings_requested', {
            detail: { source: 'header' }
        }));
        
        // Navigate to settings (implement based on routing system)
        this.navigateToSettings();
    }
    
    /**
     * Handle help button click
     */
    handleHelpClick() {
        // Dispatch event for help access
        document.dispatchEvent(new CustomEvent('help_requested', {
            detail: { source: 'header' }
        }));
        
        // Show help modal or navigate to help page
        this.showHelpModal();
    }
    
    /**
     * Navigate to home page
     */
    navigateToHome() {
        if (window.location.pathname !== '/') {
            window.location.href = '/';
        }
    }
    
    /**
     * Navigate to settings page
     */
    navigateToSettings() {
        // Implement based on your routing system
        window.location.href = '/settings';
    }
    
    /**
     * Show help modal
     */
    showHelpModal() {
        // Create and show help modal
        const modal = this.createHelpModal();
        document.body.appendChild(modal);
        
        // Focus management for accessibility
        modal.querySelector('.modal-close').focus();
    }
    
    /**
     * Create help modal element
     */
    createHelpModal() {
        const modal = document.createElement('div');
        modal.className = 'help-modal modal-overlay';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'help-modal-title');
        modal.setAttribute('aria-modal', 'true');
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="help-modal-title">System Help</h2>
                    <button class="modal-close" aria-label="Close help modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="help-section">
                        <h3>Keyboard Shortcuts</h3>
                        <ul>
                            <li><kbd>Ctrl + 1</kbd> - Start Reaction Timer Game</li>
                            <li><kbd>Ctrl + 2</kbd> - Start Wheel Game</li>
                            <li><kbd>Ctrl + 3</kbd> - Start Quiz Game</li>
                            <li><kbd>Ctrl + T</kbd> - Team Management</li>
                            <li><kbd>F5</kbd> - Refresh System Status</li>
                            <li><kbd>Esc</kbd> - Clear selections</li>
                        </ul>
                    </div>
                    <div class="help-section">
                        <h3>System Information</h3>
                        <p>Multi-Team Gaming System v1.0 MVP</p>
                        <p>Supports up to 8 teams with hardware button integration</p>
                        <p>Games: Reaction Timer, Wheel Game, Quiz Game</p>
                    </div>
                    <div class="help-section">
                        <h3>Getting Started</h3>
                        <ol>
                            <li>Register teams using the Team Management button</li>
                            <li>Ensure hardware connections are active (green status)</li>
                            <li>Select a game from the main navigation grid</li>
                            <li>Follow game-specific instructions</li>
                        </ol>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary modal-close">Got it!</button>
                </div>
            </div>
        `;
        
        // Add event listeners
        modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') || 
                e.target.classList.contains('modal-close')) {
                this.closeModal(modal);
            }
        });
        
        // Handle escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        return modal;
    }
    
    /**
     * Close modal
     */
    closeModal(modal) {
        modal.remove();
        
        // Return focus to help button
        const helpBtn = document.querySelector('.help-btn');
        if (helpBtn) {
            helpBtn.focus();
        }
    }
    
    /**
     * Update breadcrumb navigation
     */
    updateBreadcrumb(page = null) {
        if (page) {
            this.currentPage = page;
        }
        
        const breadcrumb = document.querySelector('.breadcrumb');
        if (!breadcrumb) return;
        
        // Define page hierarchy and titles
        const pageConfig = {
            'home': { title: 'Game Selection', path: '/' },
            'reaction-timer': { title: 'Reaction Timer', path: '/reaction-timer' },
            'wheel-game': { title: 'Wheel Game', path: '/wheel-game' },
            'quiz-game': { title: 'Quiz Game', path: '/quiz-game' },
            'team-management': { title: 'Team Management', path: '/team-management' },
            'settings': { title: 'Settings', path: '/settings' }
        };
        
        const currentConfig = pageConfig[this.currentPage] || pageConfig.home;
        
        // Update active breadcrumb item
        const activeItem = breadcrumb.querySelector('.breadcrumb-item.active');
        if (activeItem) {
            activeItem.textContent = currentConfig.title;
        }
    }
    
    /**
     * Update header based on system status
     */
    updateSystemStatus(status) {
        // Update visual indicators based on system health
        const header = document.querySelector('.page-header');
        if (!header) return;
        
        // Remove existing status classes
        header.classList.remove('status-connected', 'status-disconnected', 'status-error');
        
        // Add current status class
        if (status.connection === 'connected') {
            header.classList.add('status-connected');
        } else if (status.connection === 'error') {
            header.classList.add('status-error');
        } else {
            header.classList.add('status-disconnected');
        }
        
        // Update settings button state based on connection
        const settingsBtn = document.querySelector('.settings-btn');
        if (settingsBtn) {
            if (status.connection !== 'connected') {
                settingsBtn.disabled = true;
                settingsBtn.title = 'Settings unavailable - No server connection';
            } else {
                settingsBtn.disabled = false;
                settingsBtn.title = 'Access system settings';
            }
        }
    }
    
    /**
     * Cleanup method
     */
    destroy() {
        if (this.timeUpdateInterval) {
            clearInterval(this.timeUpdateInterval);
        }
        
        // Remove event listeners
        document.removeEventListener('page_changed', this.updateBreadcrumb);
    }
}

// Initialize PageHeader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.pageHeader) {
        window.pageHeader = new PageHeader();
    }
});

// Listen for homepage status updates
document.addEventListener('homepage_status_update', (event) => {
    if (window.pageHeader) {
        window.pageHeader.updateSystemStatus(event.detail);
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PageHeader;
}