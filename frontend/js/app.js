
/**
 * Main Application Logic
 */

const appState = {
    user: null,
    isAuthenticated: false,
    hasProfile: false,
    currentPage: 'home'
};

function purgeLegacyLocalStorage() {
    try {
        const saved = localStorage.getItem('appState');
        if (!saved) return;
        const state = JSON.parse(saved);
        if ('currentCandidateId' in state || 'user' in state || 'hasProfile' in state) {
            localStorage.setItem('appState', JSON.stringify({
                currentPage: state.currentPage || 'home'
            }));
        }
    } catch (error) {
        localStorage.removeItem('appState');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    initThemeToggle();
    initializeNavigation();
    purgeLegacyLocalStorage();
    loadSavedState();
    await initAuth();
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
    const protectedPages = ['upload', 'interview', 'dashboard'];
    if (protectedPages.includes(pageName) && !requireAuth(pageName)) {
        return;
    }
    if (pageName === 'interview' && !requireProfile(pageName)) {
        return;
    }

    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageName) {
            link.classList.add('active');
        }
    });

    appState.currentPage = pageName;
    saveState();

    if (pageName === 'upload' && typeof syncUploadPageForUser === 'function') {
        syncUploadPageForUser();
    } else if (pageName === 'dashboard' && typeof syncDashboardForUser === 'function') {
        syncDashboardForUser();
    }
}

function saveState() {
    localStorage.setItem('appState', JSON.stringify({
        currentPage: appState.currentPage
    }));
}

function loadSavedState() {
    const saved = localStorage.getItem('appState');
    if (!saved) return;
    try {
        const state = JSON.parse(saved);
        if (state.currentPage) {
            appState.currentPage = state.currentPage;
        }
    } catch (error) {
        console.warn('Could not restore app state', error);
    }
}

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

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

async function checkAPIHealth() {
    try {
        const result = await api.healthCheck();
        console.log('API is healthy', result);
    } catch (error) {
        console.error('API health check failed:', error.message);
        showToast('Cannot connect to backend. Make sure the server is running.', 'error');
    }
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getRandomColor() {
    const colors = ['#0d9488', '#6366f1', '#059669', '#d97706', '#dc2626', '#8b5cf6'];
    return colors[Math.floor(Math.random() * colors.length)];
}
