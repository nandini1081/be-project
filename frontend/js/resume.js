/**
 * Resume Processing Logic - Person A
 */

/**
 * Process resume and create profile
 */
async function processResume() {
    const resumeText = document.getElementById('resume-text').value.trim();
    const resumeFile = document.getElementById('resume-file').files[0];

    if (!resumeText && !resumeFile) {
        showToast('Please upload a PDF or paste resume text', 'error');
        return;
    }

    // UI updates
    document.getElementById('processing-status').style.display = 'block';
    document.getElementById('resume-results').style.display = 'none';
    document.getElementById('status-message').textContent = 'Processing your resume...';

    try {
        let result;

        if (resumeFile) {
            // ✅ PDF upload flow
            result = await api.fullResumeProcessingPDF(resumeFile);
        } else {
            // fallback text flow
            result = await api.fullResumeProcessing(resumeText);
        }

        if (result.success) {
            appState.currentCandidateId = result.candidate_id;
            saveState();
            fillCandidateIdInputs(result.candidate_id);

            document.getElementById('status-message').textContent = 'Profile created successfully!';

            setTimeout(() => {
                document.getElementById('processing-status').style.display = 'none';
                displayResumeResults(result);
            }, 1000);

            showToast(`Profile created! Candidate ID: ${result.candidate_id}`, 'success');
        }

    } catch (error) {
        document.getElementById('processing-status').style.display = 'none';
        showToast('Error processing resume: ' + error.message, 'error');
    }
}

/**
 * Fill candidate ID into interview and dashboard inputs
 */
function fillCandidateIdInputs(candidateId) {
    ['candidate-id-input', 'dashboard-candidate-id'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = candidateId;
    });
}

/**
 * Copy candidate ID to clipboard
 */
function copyCandidateId(candidateId) {
    const id = candidateId || document.getElementById('created-candidate-id')?.textContent?.trim();
    if (!id) return;

    navigator.clipboard.writeText(id).then(() => {
        showToast('Candidate ID copied to clipboard', 'success');
    }).catch(() => {
        showToast('Could not copy — select and copy the ID manually', 'error');
    });
}

/**
 * Display resume processing results
 */
function displayResumeResults(result) {
    const resultsDiv = document.getElementById('resume-results');
    const summaryDiv = document.getElementById('profile-summary');
    if (!summaryDiv || !resultsDiv) return;

    const candidateId = result.candidate_id;
    const metadata = result.metadata || {};
    const parsed = result.parsed_data || {};

    summaryDiv.innerHTML = `
        <div class="candidate-id-banner">
            <div class="info-label">Your Candidate ID</div>
            <div class="candidate-id-row">
                <code id="created-candidate-id" class="candidate-id-value">${candidateId}</code>
                <button type="button" class="btn btn-secondary candidate-id-copy" onclick="copyCandidateId('${candidateId}')">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            <p class="candidate-id-hint">Paste this ID on the <strong>Interview</strong> page under &ldquo;Enter Your Candidate ID&rdquo; to start your mock interview.</p>
        </div>
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

/**
 * View full profile
 */
async function viewProfile() {
    if (!appState.currentCandidateId) {
        showToast('No candidate profile found', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const candidate = await api.getCandidate(appState.currentCandidateId);
        
        showLoading(false);
        
        // Display profile modal or navigate to dashboard
        document.getElementById('dashboard-candidate-id').value = appState.currentCandidateId;
        navigateTo('dashboard');
        loadDashboard();
        
    } catch (error) {
        showLoading(false);
        showToast('Error loading profile: ' + error.message, 'error');
    }
}