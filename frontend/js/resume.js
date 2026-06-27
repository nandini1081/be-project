/**
 * Resume Processing Logic - Person A
 */

function resetUploadUI() {
    const resultsDiv = document.getElementById('resume-results');
    const summaryDiv = document.getElementById('profile-summary');
    const processingStatus = document.getElementById('processing-status');
    const resumeText = document.getElementById('resume-text');
    const resumeFile = document.getElementById('resume-file');

    if (resultsDiv) resultsDiv.style.display = 'none';
    if (summaryDiv) summaryDiv.innerHTML = '';
    if (processingStatus) processingStatus.style.display = 'none';
    if (resumeText) resumeText.value = '';
    if (resumeFile) resumeFile.value = '';
}

function displayResumeResultsFromCandidate(candidateData) {
    const metadata = candidateData?.profile?.metadata || {};
    const resume = candidateData?.resume || {};

    displayResumeResults({
        metadata,
        parsed_data: {
            skills: resume.skills || [],
            experience_count: (resume.experience || []).length,
            project_count: (resume.projects || []).length
        },
        vector_dimensions: 384
    });
}

async function syncUploadPageForUser() {
    resetUploadUI();

    if (!appState.isAuthenticated || !appState.hasProfile) {
        return;
    }

    try {
        const candidateData = await api.getCandidate();
        displayResumeResultsFromCandidate(candidateData);
    } catch (error) {
        console.warn('Could not load resume summary for current user:', error);
    }
}

async function processResume() {
    if (!requireAuth('upload')) return;

    const resumeText = document.getElementById('resume-text').value.trim();
    const resumeFile = document.getElementById('resume-file').files[0];

    if (!resumeText && !resumeFile) {
        showToast('Please upload a PDF or paste resume text', 'error');
        return;
    }

    document.getElementById('processing-status').style.display = 'block';
    document.getElementById('resume-results').style.display = 'none';
    document.getElementById('status-message').textContent = 'Processing your resume...';

    try {
        const result = resumeFile
            ? await api.fullResumeProcessingPDF(resumeFile)
            : await api.fullResumeProcessing(resumeText);

        if (result.success) {
            appState.hasProfile = true;
            if (appState.user) {
                appState.user.has_profile = true;
            }
            saveState();

            document.getElementById('status-message').textContent = 'Profile updated successfully!';

            setTimeout(() => {
                document.getElementById('processing-status').style.display = 'none';
                displayResumeResults(result);
            }, 1000);

            showToast('Resume processed successfully!', 'success');
        }
    } catch (error) {
        document.getElementById('processing-status').style.display = 'none';
        showToast('Error processing resume: ' + error.message, 'error');
    }
}

function displayResumeResults(result) {
    const resultsDiv = document.getElementById('resume-results');
    const summaryDiv = document.getElementById('profile-summary');
    if (!summaryDiv || !resultsDiv) return;

    const metadata = result.metadata || {};
    const parsed = result.parsed_data || {};

    summaryDiv.innerHTML = `
        <div class="info-item">
            <div class="info-label">Experience Level</div>
            <div class="info-value">${metadata.experience_level || 'N/A'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Primary Domain</div>
            <div class="info-value">${metadata.primary_domain || 'N/A'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Skills Detected</div>
            <div class="info-value">${parsed.skills?.length ?? 0} skills</div>
        </div>
        <div class="info-item">
            <div class="info-label">Experience Count</div>
            <div class="info-value">${parsed.experience_count ?? 0} positions</div>
        </div>
        <div class="info-item">
            <div class="info-label">Projects</div>
            <div class="info-value">${parsed.project_count ?? 0} projects</div>
        </div>
        <div class="info-item">
            <div class="info-label">Resume Vector</div>
            <div class="info-value">${result.vector_dimensions || 0} dimensions</div>
        </div>
    `;

    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function viewProfile() {
    if (!requireProfile('dashboard')) return;

    showLoading(true);
    try {
        navigateTo('dashboard');
        await loadDashboard();
    } catch (error) {
        showToast('Error loading profile: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}
