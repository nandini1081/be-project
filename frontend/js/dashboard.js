/**
 * Dashboard Logic - Person B (Performance Tracking)
 */

function resetDashboardUI() {
    displayStats({
        total_interviews: 0,
        avg_total_score: 0,
        trend: null
    });

    const profileInfoDiv = document.getElementById('profile-info');
    if (profileInfoDiv) {
        profileInfoDiv.innerHTML = `
            <p style="color: var(--text-secondary); grid-column: 1 / -1;">
                Upload a resume to see your profile here.
            </p>
        `;
    }

    const historyDiv = document.getElementById('performance-history');
    if (historyDiv) {
        historyDiv.innerHTML = `
            <p style="color: var(--text-secondary); text-align: center; padding: 2rem;">
                No interview history yet. Complete an interview to see your performance here.
            </p>
        `;
    }

    const recDiv = document.getElementById('recommendations-content');
    if (recDiv) {
        recDiv.innerHTML = `
            <p style="color: var(--text-secondary); padding: 1rem;">
                Complete an interview to receive personalized recommendations.
            </p>
        `;
    }
}

async function syncDashboardForUser() {
    resetDashboardUI();

    if (!appState.isAuthenticated || !appState.hasProfile) {
        return;
    }

    await loadDashboard();
}

/**
 * Toggle collapsible dashboard panels
 */
function toggleDashboardPanel(panelId) {
    const panel = document.getElementById(panelId);
    const chevron = document.getElementById(`${panelId}-chevron`);
    if (!panel) return;

    const isHidden = panel.style.display === 'none';
    panel.style.display = isHidden ? 'block' : 'none';
    if (chevron) {
        chevron.classList.toggle('collapsed', !isHidden);
    }
}

/**
 * Load dashboard for candidate
 */
async function loadDashboard() {
    if (!requireProfile('dashboard')) return;

    showLoading(true);

    try {
        const [candidate, summary, recommendations] = await Promise.all([
            api.getCandidate(),
            api.getPerformanceSummary(),
            api.getRecommendations()
        ]);

        displayStats(summary);
        displayProfileInfo(candidate.profile, candidate.resume, summary);
        displayPerformanceHistory(summary.sessions || summary.history || []);
        displayRecommendations(recommendations);

        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.style.display = 'block';
        }

        showLoading(false);
        showToast('Dashboard loaded successfully!', 'success');
    } catch (error) {
        showLoading(false);
        showToast('Error loading dashboard: ' + error.message, 'error');
    }
}

function formatTrend(trend) {
    if (trend === 'improving') return '↑ Improving';
    if (trend === 'declining') return '↓ Declining';
    if (trend === 'stable') return '→ Stable';
    return 'Not enough data';
}

function displayStats(summary) {
    const totalEl = document.getElementById('total-interviews');
    const avgEl = document.getElementById('avg-performance');
    const trendEl = document.getElementById('improvement-rate');

    if (!totalEl || !avgEl || !trendEl) return;

    const interviewsCompleted = summary.total_interviews ?? 0;
    const avgScore = summary.avg_total_score ?? 0;

    totalEl.textContent = interviewsCompleted;
    avgEl.textContent = (avgScore * 100).toFixed(0) + '%';
    trendEl.textContent = formatTrend(summary.trend);
}

/**
 * Display profile information
 */
function displayProfileInfo(profile, resume, summary) {
    const profileInfoDiv = document.getElementById('profile-info');
    if (!profileInfoDiv || !profile) return;

    const metadata = profile.metadata || {};

    profileInfoDiv.innerHTML = `
        <div class="info-item">
            <div class="info-label">Experience Level</div>
            <div class="info-value">${metadata.experience_level || 'N/A'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Primary Domain</div>
            <div class="info-value">${metadata.primary_domain || 'N/A'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Total Skills</div>
            <div class="info-value">${resume?.skills?.length || 0}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Questions Answered</div>
            <div class="info-value">${summary?.total_questions || 0}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Profile Version</div>
            <div class="info-value">v${profile.version || 1}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Last Updated</div>
            <div class="info-value">${formatDate(profile.updated_at)}</div>
        </div>
    `;

    if (resume && resume.skills && resume.skills.length > 0) {
        const skillsHtml = `
            <div class="info-item" style="grid-column: 1 / -1;">
                <div class="info-label">Skills</div>
                <div class="info-value" style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                    ${resume.skills.map(skill => `
                        <span style="background: rgba(79, 70, 229, 0.1);
                                     color: var(--primary-color);
                                     padding: 0.25rem 0.75rem;
                                     border-radius: 0.25rem;
                                     font-size: 0.875rem;">
                            ${skill}
                        </span>
                    `).join('')}
                </div>
            </div>
        `;
        profileInfoDiv.innerHTML += skillsHtml;
    }
}

/**
 * Display recent interview sessions
 */
function displayPerformanceHistory(sessions) {
    const historyDiv = document.getElementById('performance-history');
    if (!historyDiv) return;

    if (!sessions || sessions.length === 0) {
        historyDiv.innerHTML = `
            <p style="color: var(--text-secondary); text-align: center; padding: 2rem;">
                No interview history yet. Complete an interview to see your performance here.
            </p>
        `;
        return;
    }

    historyDiv.innerHTML = sessions.map((session) => {
        const label = session.session_number
            ? `Interview #${session.session_number}`
            : 'Interview';
        const questionCount = session.question_count || session.responses?.length || 0;
        const avgScore = session.avg_score ?? session.total_score ?? 0;
        const when = session.ended_at || session.started_at || session.timestamp;

        return `
            <div class="history-item">
                <div class="history-header">
                    <span><strong>${label}</strong> · ${questionCount} question${questionCount === 1 ? '' : 's'}</span>
                    <span class="history-score">${(avgScore * 100).toFixed(0)}%</span>
                </div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                    ${formatDate(when)}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Display recommendations
 */
function displayRecommendations(recommendations) {
    const recDiv = document.getElementById('recommendations-content');
    if (!recDiv) return;

    if (!recommendations || recommendations.error) {
        recDiv.innerHTML = `
            <p style="color: var(--danger-color); padding: 1rem;">
                ${recommendations?.error || 'Could not load recommendations.'}
            </p>
        `;
        return;
    }

    const topics = recommendations.recommended_topics || {};
    const topTopics = Object.entries(topics)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    const avgSimilarity = recommendations.average_similarity ?? 0;

    recDiv.innerHTML = `
        <div style="background: var(--bg-color); padding: 1.5rem; border-radius: 0.375rem; margin-bottom: 1rem;">
            <h4 style="margin-bottom: 0.5rem;">Profile Summary</h4>
            <p style="color: var(--text-secondary);">
                Experience Level: <strong>${recommendations.experience_level || 'N/A'}</strong><br>
                Primary Domain: <strong>${recommendations.primary_domain || 'N/A'}</strong><br>
                Resume Match Strength: <strong>${(avgSimilarity * 100).toFixed(0)}%</strong>
            </p>
        </div>

        <div style="background: var(--bg-color); padding: 1.5rem; border-radius: 0.375rem;">
            <h4 style="margin-bottom: 0.35rem;">Most Relevant Topics</h4>
            <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1rem;">
                How often each topic appears among your top 10 resume-matched interview questions.
            </p>
            ${topTopics.length > 0 ? `
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    ${topTopics.map(([topic, percent]) => `
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                                <span>${topic}</span>
                                <span style="color: var(--primary-color); font-weight: 600; font-size: 0.875rem;">
                                    ${percent % 1 === 0 ? percent.toFixed(0) : percent}% relevant
                                </span>
                            </div>
                            <div style="background: var(--border-color); border-radius: 999px; height: 0.5rem; overflow: hidden;">
                                <div style="background: var(--primary-color); height: 100%; width: ${Math.min(percent, 100)}%; border-radius: 999px;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <p style="color: var(--text-secondary);">
                    Upload a resume to see which topics align best with your profile.
                </p>
            `}
        </div>
    `;
}
