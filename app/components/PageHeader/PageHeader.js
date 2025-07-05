function handle_header_click() {
    // If the user is on any page other than the TeamManagement page take them to the TeamManagement page
    if (window.location.pathname !== '/team-management') {
        console.log('Navigating to Team Management page');
        window.location.href = '/team-management';
    } else {
        // If they are already on the TeamManagement page take them to the home page
        console.log('Navigating to Home page');
        window.location.href = '/';
    }
}

// When the page loads change the header button text based on the current page
window.addEventListener('DOMContentLoaded', () => {
    const headerButton = document.getElementById('header_button');
    if (window.location.pathname === '/team-management') {
        headerButton.textContent = 'Back to Home';
    } else {
        headerButton.textContent = 'Manage Teams';
    }
});