/**
 * Resume Processing Logic - Person A
 */

/**
 * Process resume and create profile
 */
async function processResume() {
    const resumeText = document.getElementById('resume-text').value.trim();
    
    if (!resumeText) {
        showToast('Please paste your resume text', 'error');
        return;
    }
    
    // Show processing status
    document.getElementById('processing-status').style.display = 'block';
    document.getElementById('resume-results').style.display = 'none';
    document.getElementById('status-message').textContent = 'Processing your resume...';
    
    try {
        // Call full resume processing API
        const result = await api.fullResumeProcessing(resumeText);
        
        if (result.success) {
            // Save candidate ID
            appState.currentCandidateId = result.candidate_id;
            saveState();
            
            // Update status
            document.getElementById('status-message').textContent = 'Profile created successfully!';
            
            // Show results after delay
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