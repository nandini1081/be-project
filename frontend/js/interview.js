/**
 * Interview Session Logic - Person D (Retrieval) + Person B (Recording)
 */

// Interview state
const interviewState = {
    candidateId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: [],
    isActive: false
};

/**
 * Start interview session
 */
async function startInterview() {
    const candidateId = document.getElementById('candidate-id-input').value.trim();
    
    if (!candidateId) {
        showToast('Please enter your Candidate ID', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        // Get interview settings
        const maxQuestions = parseInt(document.getElementById('question-count').value);
        const difficulty = document.getElementById('difficulty-level').value;
        const category = document.getElementById('category-filter').value;
        
        // Retrieve questions
        const options = { maxQuestions };
        if (difficulty) options.difficulty = difficulty;
        if (category) options.category = category;
        
        const result = await api.retrieveQuestions(candidateId, options);
        
        if (result.success && result.questions.length > 0) {
            // Initialize interview state
            interviewState.candidateId = candidateId;
            interviewState.questions = result.questions;
            interviewState.currentQuestionIndex = 0;
            interviewState.answers = [];
            interviewState.isActive = true;
            
            // Save candidate ID
            appState.currentCandidateId = candidateId;
            saveState();
            
            // Hide selection, show interview
            document.getElementById('candidate-selection').style.display = 'none';
            document.getElementById('interview-session').style.display = 'block';
            
            // Display first question
            displayCurrentQuestion();
            
            showLoading(false);
            showToast('Interview started!', 'success');
        } else {
            showLoading(false);
            showToast('No matching questions found. Please try different settings.', 'error');
        }
        
    } catch (error) {
        showLoading(false);
        showToast('Error starting interview: ' + error.message, 'error');
    }
}

/**
 * Display current question
 */
function displayCurrentQuestion() {
    const question = interviewState.questions[interviewState.currentQuestionIndex];
    const totalQuestions = interviewState.questions.length;
    const currentNum = interviewState.currentQuestionIndex + 1;
    
    // Update progress
    document.getElementById('current-question-num').textContent = currentNum;
    document.getElementById('total-questions').textContent = totalQuestions;
    document.getElementById('progress-percentage').textContent = Math.round((currentNum / totalQuestions) * 100) + '%';
    document.getElementById('progress-fill').style.width = ((currentNum / totalQuestions) * 100) + '%';
    
    // Update question display
    document.getElementById('question-category').textContent = question.category;
    document.getElementById('question-difficulty').textContent = question.difficulty;
    document.getElementById('question-text').textContent = question.question_text;
    document.getElementById('question-topics').textContent = question.topics.join(', ');
    document.getElementById('question-similarity').textContent = question.similarity_score.toFixed(2);
    
    // Clear answer textarea
    document.getElementById('answer-text').value = '';
    
    // Hide feedback
    document.getElementById('answer-feedback').style.display = 'none';
}

/**
 * Submit answer
 */
async function submitAnswer() {
    const answerText = document.getElementById('answer-text').value.trim();
    
    if (!answerText) {
        showToast('Please provide an answer', 'error');
        return;
    }
    
    showLoading(true);
    
    const question = interviewState.questions[interviewState.currentQuestionIndex];
    
    try {
        // Simulate scoring (in real app, this would be done by backend)
        const knowledgeScore = calculateKnowledgeScore(answerText, question);
        const speechScore = calculateSpeechScore(answerText);
        
        // Record response
        await api.recordResponse(
            interviewState.candidateId,
            question.question_id,
            answerText,
            knowledgeScore,
            speechScore
        );
        
        // Store answer
        interviewState.answers.push({
            questionId: question.question_id,
            answerText: answerText,
            knowledgeScore: knowledgeScore,
            speechScore: speechScore,
            totalScore: (knowledgeScore * 0.6) + (speechScore * 0.4)
        });
        
        // Show feedback
        displayAnswerFeedback(knowledgeScore, speechScore);
        
        showLoading(false);
        showToast('Answer submitted successfully!', 'success');
        
    } catch (error) {
        showLoading(false);
        showToast('Error submitting answer: ' + error.message, 'error');
    }
}

/**
 * Calculate knowledge score (simplified)
 */
function calculateKnowledgeScore(answer, question) {
    let score = 0.5; // Base score
    
    // Check answer length
    const wordCount = answer.split(/\s+/).length;
    if (wordCount >= 50) score += 0.2;
    else if (wordCount >= 30) score += 0.1;
    
    // Check for topic keywords
    const answerLower = answer.toLowerCase();
    let keywordMatches = 0;
    
    question.topics.forEach(topic => {
        if (answerLower.includes(topic.toLowerCase())) {
            keywordMatches++;
        }
    });
    
    if (keywordMatches > 0) {
        score += Math.min(0.3, keywordMatches * 0.1);
    }
    
    return Math.min(1.0, score);
}

/**
 * Calculate speech score (simplified - based on text quality)
 */
function calculateSpeechScore(answer) {
    let score = 0.6; // Base score
    
    // Check for filler words
    const fillerWords = ['umm', 'uh', 'like', 'you know', 'basically'];
    const answerLower = answer.toLowerCase();
    let fillerCount = 0;
    
    fillerWords.forEach(filler => {
        const regex = new RegExp(filler, 'gi');
        const matches = answerLower.match(regex);
        if (matches) fillerCount += matches.length;
    });
    
    if (fillerCount === 0) score += 0.2;
    else if (fillerCount <= 2) score += 0.1;
    
    // Check sentence structure (has periods)
    const sentences = answer.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length >= 3) score += 0.2;
    
    return Math.min(1.0, score);
}

/**
 * Display answer feedback
 */
function displayAnswerFeedback(knowledgeScore, speechScore) {
    const totalScore = (knowledgeScore * 0.6) + (speechScore * 0.4);
    
    document.getElementById('knowledge-score').textContent = (knowledgeScore * 100).toFixed(0) + '%';
    document.getElementById('speech-score').textContent = (speechScore * 100).toFixed(0) + '%';
    document.getElementById('total-score').textContent = (totalScore * 100).toFixed(0) + '%';
    
    // Color code based on score
    const totalScoreElement = document.getElementById('total-score');
    if (totalScore >= 0.8) {
        totalScoreElement.style.color = '#10B981'; // Green
    } else if (totalScore >= 0.6) {
        totalScoreElement.style.color = '#F59E0B'; // Yellow
    } else {
        totalScoreElement.style.color = '#EF4444'; // Red
    }
    
    document.getElementById('answer-feedback').style.display = 'block';
}

/**
 * Move to next question
 */
function nextQuestion() {
    interviewState.currentQuestionIndex++;
    
    if (interviewState.currentQuestionIndex >= interviewState.questions.length) {
        // Interview complete
        completeInterview();
    } else {
        // Show next question
        displayCurrentQuestion();
    }
}

/**
 * Skip current question
 */
function skipQuestion() {
    if (confirm('Are you sure you want to skip this question?')) {
        // Record as skipped with zero scores
        const question = interviewState.questions[interviewState.currentQuestionIndex];
        
        interviewState.answers.push({
            questionId: question.question_id,
            answerText: '[Skipped]',
            knowledgeScore: 0,
            speechScore: 0,
            totalScore: 0
        });
        
        nextQuestion();
    }
}

/**
 * End interview early
 */
function endInterview() {
    if (confirm('Are you sure you want to end the interview? Your progress will be saved.')) {
        completeInterview();
    }
}

/**
 * Complete interview
 */
function completeInterview() {
    interviewState.isActive = false;
    
    // Calculate final statistics
    const totalAnswers = interviewState.answers.length;
    const avgScore = interviewState.answers.reduce((sum, a) => sum + a.totalScore, 0) / totalAnswers;
    const skipped = interviewState.answers.filter(a => a.answerText === '[Skipped]').length;
    
    // Display summary
    const summaryDiv = document.getElementById('final-summary');
    summaryDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-question-circle"></i>
                <h3>${totalAnswers}</h3>
                <p>Questions Attempted</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-star"></i>
                <h3>${(avgScore * 100).toFixed(0)}%</h3>
                <p>Average Score</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-forward"></i>
                <h3>${skipped}</h3>
                <p>Questions Skipped</p>
            </div>
        </div>
        <p style="margin-top: 1.5rem; color: var(--text-secondary);">
            Great job! Your responses have been recorded and your profile has been updated.
            Check your dashboard for detailed analytics.
        </p>
    `;
    
    // Hide question section, show complete
    document.getElementById('interview-session').querySelector('.progress-section').style.display = 'none';
    document.getElementById('interview-session').querySelector('.question-card').style.display = 'none';
    document.getElementById('interview-session').querySelector('.answer-section').style.display = 'none';
    document.getElementById('answer-feedback').style.display = 'none';
    document.getElementById('interview-complete').style.display = 'block';
    
    showToast('Interview completed!', 'success');
}

/**
 * Reset interview
 */
function resetInterview() {
    // Reset state
    interviewState.candidateId = null;
    interviewState.questions = [];
    interviewState.currentQuestionIndex = 0;
    interviewState.answers = [];
    interviewState.isActive = false;
    
    // Show selection, hide session
    document.getElementById('candidate-selection').style.display = 'block';
    document.getElementById('interview-session').style.display = 'none';
    
    // Reset display states
    document.getElementById('interview-session').querySelector('.progress-section').style.display = 'block';
    document.getElementById('interview-session').querySelector('.question-card').style.display = 'block';
    document.getElementById('interview-session').querySelector('.answer-section').style.display = 'block';
    document.getElementById('interview-complete').style.display = 'none';
}