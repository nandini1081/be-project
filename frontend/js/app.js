
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
    initThemeToggle();
    initializeNavigation();
    loadSavedState();
    
    // Check API health
    checkAPIHealth();
});

const THEME_STORAGE_KEY = 'theme';

function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function setTheme(theme) {
    const next = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(THEME_STORAGE_KEY, next);
    syncThemeToggleUI(next);
}

function syncThemeToggleUI(theme) {
    const btn = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-toggle-icon');
    const label = document.getElementById('theme-toggle-label');
    if (!btn || !icon) return;
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
        btn.setAttribute('aria-label', 'Switch to light theme');
        if (label) label.textContent = 'Light';
    } else {
        icon.className = 'fas fa-moon';
        btn.setAttribute('aria-label', 'Switch to dark theme');
        if (label) label.textContent = 'Dark';
    }
}

function initThemeToggle() {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    const initial = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(initial);

    const btn = document.getElementById('theme-toggle');
    if (btn) {
        btn.addEventListener('click', () => {
            setTheme(getCurrentTheme() === 'dark' ? 'light' : 'dark');
        });
    }
}

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

    if (pageName === 'dashboard') {
    console.log("Navigated to dashboard");

    const input = document.getElementById('dashboard-candidate-id');

    if (input && input.value.trim()) {

            // 🔥 CRITICAL FIX
            requestAnimationFrame(() => {
                loadDashboard();
            });

        } else {
            console.warn("No candidate ID entered for dashboard");
        }
    }
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
        const result = await api.healthCheck();
        console.log('✅ API is healthy', result);
    } catch (error) {
        console.error('❌ API health check failed:', error.message, error);
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
    const colors = ['#0d9488', '#6366f1', '#059669', '#d97706', '#dc2626', '#8b5cf6'];
    return colors[Math.floor(Math.random() * colors.length)];
}
