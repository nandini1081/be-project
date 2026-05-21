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

            document.getElementById('status-message').textContent = 'Profile created successfully!';

            setTimeout(() => {
                document.getElementById('processing-status').style.display = 'none';
                displayResumeResults(result);
            }, 1000);

            showToast('Profile created successfully!', 'success');
        }

    } catch (error) {
        document.getElementById('processing-status').style.display = 'none';
        showToast('Error processing resume: ' + error.message, 'error');
    }
}

/**
 * Display resume processing results
 */
function displayResumeResults(result) {
    const resultsDiv = document.getElementById('resume-results');
    const summaryDiv = document.getElementById('profile-summary');
    
    summaryDiv.innerHTML = `
        <div class="info-item">
            <div class="info-label">Candidate ID</div>
            <div class="info-value">${result.candidate_id}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Experience Level</div>
            <div class="info-value">${result.metadata.experience_level}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Primary Domain</div>
            <div class="info-value">${result.metadata.primary_domain}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Skills Detected</div>
            <div class="info-value">${result.parsed_data.skills.length} skills</div>
        </div>
        <div class="info-item">
            <div class="info-label">Experience Count</div>
            <div class="info-value">${result.parsed_data.experience_count} positions</div>
        </div>
        <div class="info-item">
            <div class="info-label">Projects</div>
            <div class="info-value">${result.parsed_data.project_count} projects</div>
        </div>
        <div class="info-item">
            <div class="info-label">Resume Vector</div>
            <div class="info-value">${result.vector_dimensions || 0} dimensions</div>
        </div>
    `;
    
    resultsDiv.style.display = 'block';
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