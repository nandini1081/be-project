/**
 * Question Management Logic - Person C
 */

// Store loaded questions
let allQuestions = [];

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show target tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

/**
 * Handle add question form submission
 */
document.getElementById('add-question-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const questionData = {
        question_text: document.getElementById('new-question-text').value.trim(),
        category: document.getElementById('new-category').value,
        difficulty: document.getElementById('new-difficulty').value,
        topics: document.getElementById('new-topics').value.split(',').map(t => t.trim()),
        job_roles: document.getElementById('new-job-roles').value.split(',').map(r => r.trim()),
        ideal_keywords: document.getElementById('new-keywords').value.split(',').map(k => k.trim()).filter(k => k)
    };
    
    showLoading(true);
    
    try {
        const result = await api.addQuestion(questionData);
        
        if (result.success) {
            showToast('Question added successfully!', 'success');
            
            // Reset form
            document.getElementById('add-question-form').reset();
            
            // Refresh question list if on that tab
            loadAllQuestions();
        }
        
        showLoading(false);
    } catch (error) {
        showLoading(false);
        showToast('Error adding question: ' + error.message, 'error');
    }
});

/**
 * Bulk add questions from JSON
 */
async function bulkAddQuestions() {
    const jsonText = document.getElementById('bulk-questions-json').value.trim();
    
    if (!jsonText) {
        showToast('Please enter JSON data', 'error');
        return;
    }
    
    try {
        const questions = JSON.parse(jsonText);
        
        if (!Array.isArray(questions)) {
            throw new Error('JSON must be an array of questions');
        }
        
        showLoading(true);
        
        const result = await api.bulkAddQuestions(questions);
        
        if (result.success) {
            showToast(`Successfully added ${result.count} questions!`, 'success');
            
            // Clear textarea
            document.getElementById('bulk-questions-json').value = '';
            
            // Refresh question list
            loadAllQuestions();
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        if (error instanceof SyntaxError) {
            showToast('Invalid JSON format', 'error');
        } else {
            showToast('Error adding questions: ' + error.message, 'error');
        }
    }
}

/**
 * Load all questions
 */
async function loadAllQuestions() {
    showLoading(true);
    
    try {
        const summary = await api.getDatabaseSummary();
        
        // Display summary stats
        displayDatabaseStats(summary);
        
        // For now, show summary (in production, you'd fetch all questions)
        const questionsList = document.getElementById('questions-list');
        questionsList.innerHTML = `
            <p style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                Question database contains ${summary.total_questions} questions.<br>
                Use the filters above to search specific categories and difficulties.
            </p>
        `;
        
        showLoading(false);
        showToast('Database loaded successfully!', 'success');
        
    } catch (error) {
        showLoading(false);
        showToast('Error loading questions: ' + error.message, 'error');
    }
}

/**
 * Display database statistics
 */
function displayDatabaseStats(summary) {
    const statsDiv = document.getElementById('database-stats');
    
    const categoryStats = Object.entries(summary.by_category || {})
        .map(([cat, count]) => `<strong>${cat}:</strong> ${count}`)
        .join(' | ');
    
    const difficultyStats = Object.entries(summary.by_difficulty || {})
        .map(([diff, count]) => `<strong>${diff}:</strong> ${count}`)
        .join(' | ');
    
    statsDiv.innerHTML = `
        <h4 style="margin-bottom: 1rem;">Database Statistics</h4>
        <div style="display: grid; gap: 0.75rem;">
            <div>
                <span style="color: var(--text-secondary);">Total Questions:</span>
                <strong>${summary.total_questions}</strong>
            </div>
            <div>
                <span style="color: var(--text-secondary);">By Category:</span>
                ${categoryStats}
            </div>
            <div>
                <span style="color: var(--text-secondary);">By Difficulty:</span>
                ${difficultyStats}
            </div>
        </div>
    `;
}

/**
 * Filter questions
 */
function filterQuestions() {
    const category = document.getElementById('filter-category').value;
    const difficulty = document.getElementById('filter-difficulty').value;
    
    // In production, this would call API with filters
    showToast('Filtering: ' + (category || 'All') + ' / ' + (difficulty || 'All'), 'info');
}