const appContent = document.getElementById('app-content');
const logoutLink = document.getElementById('logout-link');

// Simple hash-based router
async function loadView(viewName) {
    // Default view if hash is empty or just '#'
    if (!viewName || viewName === '#') {
        viewName = 'map'; // Default to map view
    } else {
        viewName = viewName.substring(1); // Remove '#'
    }

    // Map view names to file paths
    const viewFiles = {
        'login': 'views/login.html',
        'register': 'views/register.html', // Add later
        'map': 'views/map.html',           // Add later
        'submit': 'views/submit.html',     // Add later
        'profile': 'views/profile.html'    // Add later
    };

    const filePath = viewFiles[viewName];

    if (!filePath) {
        appContent.innerHTML = '<p class="text-danger">Error: View not found.</p>';
        console.error(`View '${viewName}' not found in viewFiles mapping.`);
        return;
    }

    try {
        const response = await fetch(filePath);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${filePath}: ${response.statusText}`);
        }
        const html = await response.text();
        appContent.innerHTML = html;

        // Execute view-specific initialization if needed
        if (viewName === 'login' && typeof initLoginView === 'function') {
            initLoginView();
        }
        // Add other view initializations here (e.g., initMapView, initSubmitView)

    } catch (error) {
        appContent.innerHTML = `<p class="text-danger">Error loading view: ${error.message}</p>`;
        console.error('Error loading view:', error);
    }
}

// Function to update UI based on login status
function updateLoginStatus() {
    const token = localStorage.getItem('accessToken');
    if (token) {
        logoutLink.style.display = 'block';
        // Potentially hide login/register links if desired
    } else {
        logoutLink.style.display = 'none';
    }
}

// Initial load and hash change listener
window.addEventListener('hashchange', () => loadView(window.location.hash));
window.addEventListener('load', () => {
    loadView(window.location.hash || '#map'); // Load default view or current hash
    updateLoginStatus(); // Check login status on load
});

// Logout function (called from nav link)
function logout() {
    localStorage.removeItem('accessToken');
    updateLoginStatus();
    // Redirect to login page or map page after logout
    window.location.hash = '#login';
}