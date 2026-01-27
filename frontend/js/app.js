
/**
 * Main Application Logic
 */

// Global state
const appState = {
    currentCandidateId: null,
    currentPage: 'home'
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    loadSavedState();
    
    // Check API health
    checkAPIHealth();
});

/**
 * Navigation handling
 */
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            navigateTo(page);
        });
    });
}

function navigateTo(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show target page
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageName) {
            link.classList.add('active');
        }
    });
    
    // Update state
    appState.currentPage = pageName;
    saveState();
}

/**
 * State management
 */
function saveState() {
    localStorage.setItem('appState', JSON.stringify(appState));
}

function loadSavedState() {
    const saved = localStorage.getItem('appState');
    if (saved) {
        const state = JSON.parse(saved);
        appState.currentCandidateId = state.currentCandidateId;
        
        // Restore candidate ID in inputs
        if (appState.currentCandidateId) {
            const inputs = document.querySelectorAll('#candidate-id-input, #dashboard-candidate-id');
            inputs.forEach(input => input.value = appState.currentCandidateId);
        }
    }
}

/**
 * Toast notifications
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 
                 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Loading overlay
 */
function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

/**
 * Check API health
 */
async function checkAPIHealth() {
    try {
        await api.healthCheck();
        console.log('✅ API is healthy');
    } catch (error) {
        console.error('❌ API health check failed:', error);
        showToast('Cannot connect to backend. Make sure the server is running.', 'error');
    }
}

/**
 * Format date
 */
function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Generate random color
 */
function getRandomColor() {
    const colors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
    return colors[Math.floor(Math.random() * colors.length)];
}
