/**
 * Authentication UI and session handling
 */

let trackedUserId = null;

async function initAuth() {
    try {
        const result = await api.getMe();
        if (result.authenticated && result.user) {
            setAuthenticatedUser(result.user);
        } else {
            setAuthenticatedUser(null);
        }
    } catch (error) {
        console.warn('Auth check failed:', error);
        setAuthenticatedUser(null);
    }
    updateAuthUI();
}

function clearUserScopedUI() {
    if (typeof resetUploadUI === 'function') {
        resetUploadUI();
    }
    if (typeof resetDashboardUI === 'function') {
        resetDashboardUI();
    }
    if (typeof resetInterviewUI === 'function') {
        resetInterviewUI();
    }
}

async function syncVisiblePagesForUser() {
    const page = appState.currentPage;
    if (page === 'upload' && typeof syncUploadPageForUser === 'function') {
        await syncUploadPageForUser();
    } else if (page === 'dashboard' && typeof syncDashboardForUser === 'function') {
        await syncDashboardForUser();
    }
}

function setAuthenticatedUser(user) {
    const nextUserId = user?.user_id ?? null;

    if (nextUserId !== trackedUserId) {
        clearUserScopedUI();
        trackedUserId = nextUserId;
    }

    appState.user = user || null;
    appState.isAuthenticated = Boolean(user);
    appState.hasProfile = Boolean(user?.has_profile);
    saveState();

    if (!user) {
        trackedUserId = null;
        return;
    }

    syncVisiblePagesForUser();
}

function updateAuthUI() {
    const loggedInNav = document.getElementById('auth-logged-in');
    const loggedOutNav = document.getElementById('auth-logged-out');
    const userEmailEl = document.getElementById('auth-user-email');

    if (appState.isAuthenticated && appState.user) {
        if (loggedInNav) loggedInNav.style.display = 'flex';
        if (loggedOutNav) loggedOutNav.style.display = 'none';
        if (userEmailEl) userEmailEl.textContent = appState.user.email;
    } else {
        if (loggedInNav) loggedInNav.style.display = 'none';
        if (loggedOutNav) loggedOutNav.style.display = 'flex';
        if (userEmailEl) userEmailEl.textContent = '';
    }
}

function showAuthModal(mode = 'login') {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    switchAuthTab(mode);
    clearAuthErrors();
}

function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
    clearAuthErrors();
}

function switchAuthTab(mode) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.getElementById('auth-tab-login');
    const registerTab = document.getElementById('auth-tab-register');

    const isLogin = mode === 'login';
    if (loginForm) loginForm.style.display = isLogin ? 'block' : 'none';
    if (registerForm) registerForm.style.display = isLogin ? 'none' : 'block';
    if (loginTab) loginTab.classList.toggle('active', isLogin);
    if (registerTab) registerTab.classList.toggle('active', !isLogin);
}

function clearAuthErrors() {
    ['login-error', 'register-error'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.style.display = 'none';
            el.textContent = '';
        }
    });
}

function showAuthError(elementId, message) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.style.display = 'block';
}

function requireAuth(pageName) {
    if (appState.isAuthenticated) {
        return true;
    }
    showToast('Please log in to continue', 'error');
    showAuthModal('login');
    return false;
}

function requireProfile(pageName) {
    if (!requireAuth(pageName)) {
        return false;
    }
    if (appState.hasProfile) {
        return true;
    }
    showToast('Upload your resume first to use this feature', 'error');
    navigateTo('upload');
    return false;
}

async function submitLogin(event) {
    event.preventDefault();
    clearAuthErrors();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        showLoading(true);
        const result = await api.login(email, password);
        setAuthenticatedUser(result.user);
        updateAuthUI();
        hideAuthModal();
        showToast('Welcome back!', 'success');
    } catch (error) {
        showAuthError('login-error', error.message);
    } finally {
        showLoading(false);
    }
}

async function submitRegister(event) {
    event.preventDefault();
    clearAuthErrors();

    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const confirm = document.getElementById('register-password-confirm').value;

    if (password !== confirm) {
        showAuthError('register-error', 'Passwords do not match');
        return;
    }

    try {
        showLoading(true);
        const result = await api.register(email, password);
        setAuthenticatedUser(result.user);
        updateAuthUI();
        hideAuthModal();
        showToast('Account created successfully!', 'success');
    } catch (error) {
        showAuthError('register-error', error.message);
    } finally {
        showLoading(false);
    }
}

async function logoutUser() {
    try {
        await api.logout();
    } catch (error) {
        console.warn('Logout error:', error);
    }

    setAuthenticatedUser(null);
    updateAuthUI();
    showToast('Logged out', 'info');
    navigateTo('home');
}
