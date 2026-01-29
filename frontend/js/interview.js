/**
 * Interview Session Logic - Person D (Retrieval) + Person B (Recording)
 * Enhanced with Text-to-Speech and Speech-to-Text
 * FIXED: Better network error handling
 */

// Interview state
const interviewState = {
    candidateId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: [],
    isActive: false
};

// Speech state
const speechState = {
    synthesis: window.speechSynthesis,
    recognition: null,
    isListening: false,
    isSpeaking: false,
    voices: [],
    selectedVoice: null,
    networkErrorCount: 0,
    maxNetworkRetries: 3
};

/**
 * Initialize Speech APIs
 */
function initializeSpeechAPIs() {
    // Initialize Text-to-Speech
    if ('speechSynthesis' in window) {
        speechState.synthesis = window.speechSynthesis;
        
        // Load available voices
        loadVoices();
        
        // Voice list updates asynchronously in some browsers
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    } else {
        console.warn('Text-to-Speech not supported in this browser');
    }
    
    // Initialize Speech-to-Text
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        speechState.recognition = new SpeechRecognition();
        
        // Configure recognition - OPTIMIZED SETTINGS
        speechState.recognition.continuous = false; // Changed to false for better stability
        speechState.recognition.interimResults = true;
        speechState.recognition.lang = 'en-US';
        speechState.recognition.maxAlternatives = 1;
        
        // Setup event handlers
        setupRecognitionHandlers();
    } else {
        console.warn('Speech-to-Text not supported in this browser');
    }
}

/**
 * Load available voices for TTS
 */
function loadVoices() {
    speechState.voices = speechState.synthesis.getVoices();
    
    // Try to select a natural-sounding English voice
    speechState.selectedVoice = speechState.voices.find(voice => 
        voice.lang.startsWith('en') && voice.name.includes('Natural')
    ) || speechState.voices.find(voice => 
        voice.lang.startsWith('en')
    ) || speechState.voices[0];
    
    console.log(`Loaded ${speechState.voices.length} voices. Selected: ${speechState.selectedVoice?.name}`);
}

/**
 * Setup Speech Recognition event handlers - IMPROVED ERROR HANDLING
 */
function setupRecognitionHandlers() {
    const recognition = speechState.recognition;
    
    recognition.onstart = () => {
        speechState.isListening = true;
        speechState.networkErrorCount = 0; // Reset error count on successful start
        updateRecordingUI(true);
        console.log('Speech recognition started');
    };
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update answer textarea with transcription
        const answerTextarea = document.getElementById('answer-text');
        if (finalTranscript) {
            const currentText = answerTextarea.value;
            answerTextarea.value = currentText + finalTranscript;
        }
        
        // Show interim results
        if (interimTranscript) {
            document.getElementById('interim-transcript').textContent = interimTranscript;
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        
        let errorMessage = '';
        let shouldRetry = false;
        
        switch(event.error) {
            case 'network':
                speechState.networkErrorCount++;
                if (speechState.networkErrorCount < speechState.maxNetworkRetries) {
                    errorMessage = 'Network issue. Retrying...';
                    shouldRetry = true;
                } else {
                    errorMessage = 'Network connection issue. Please check your internet connection and try again. You can also type your answer instead.';
                }
                break;
                
            case 'no-speech':
                errorMessage = 'No speech detected. Please try speaking again.';
                break;
                
            case 'audio-capture':
                errorMessage = 'No microphone found. Please check your microphone connection.';
                break;
                
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
                showMicrophonePermissionHelp();
                break;
                
            case 'aborted':
                errorMessage = 'Recording aborted. Click Record Answer to try again.';
                break;
                
            case 'service-not-allowed':
                errorMessage = 'Speech service not available. Please use text input instead.';
                break;
                
            default:
                errorMessage = `Speech recognition error: ${event.error}. You can type your answer instead.`;
        }
        
        speechState.isListening = false;
        updateRecordingUI(false);
        
        // Show error in a less intrusive way
        showRecordingError(errorMessage);
        
        // Auto-retry for network errors
        if (shouldRetry) {
            console.log(`Retrying speech recognition (attempt ${speechState.networkErrorCount})...`);
            setTimeout(() => {
                if (!speechState.isListening) {
                    startRecording();
                }
            }, 1000);
        }
    };
    
    recognition.onend = () => {
        speechState.isListening = false;
        updateRecordingUI(false);
        document.getElementById('interim-transcript').textContent = '';
        console.log('Speech recognition ended');
    };
}

/**
 * Show recording error in UI
 */
function showRecordingError(message) {
    const errorDiv = document.getElementById('recording-error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to toast if error div doesn't exist
        showToast(message, 'warning');
    }
}

/**
 * Show microphone permission help
 */
function showMicrophonePermissionHelp() {
    const helpDiv = document.getElementById('mic-permission-help');
    if (helpDiv) {
        helpDiv.style.display = 'block';
    }
}

/**
 * Text-to-Speech: Speak the question
 */
function speakQuestion(questionText) {
    // Stop any ongoing speech
    if (speechState.isSpeaking) {
        speechState.synthesis.cancel();
    }
    
    if (!('speechSynthesis' in window)) {
        showToast('Text-to-Speech not supported', 'warning');
        return;
    }
    
    const utterance = new SpeechSynthesisUtterance(questionText);
    
    // Configure utterance
    utterance.voice = speechState.selectedVoice;
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Event handlers
    utterance.onstart = () => {
        speechState.isSpeaking = true;
        updateSpeakingUI(true);
        console.log('Started speaking question');
    };
    
    utterance.onend = () => {
        speechState.isSpeaking = false;
        updateSpeakingUI(false);
        console.log('Finished speaking question');
    };
    
    utterance.onerror = (event) => {
        speechState.isSpeaking = false;
        updateSpeakingUI(false);
        console.error('Speech synthesis error:', event);
        showToast('Error speaking question', 'error');
    };
    
    // Speak the question
    speechState.synthesis.speak(utterance);
}

/**
 * Stop speaking
 */
function stopSpeaking() {
    if (speechState.synthesis && speechState.isSpeaking) {
        speechState.synthesis.cancel();
        speechState.isSpeaking = false;
        updateSpeakingUI(false);
    }
}

/**
 * Start voice recording for answer - IMPROVED
 */
function startRecording() {
    if (!speechState.recognition) {
        showToast('Speech recognition not supported. Please use Chrome or Edge browser.', 'error');
        return;
    }
    
    if (speechState.isListening) {
        // Stop recording
        speechState.recognition.stop();
    } else {
        // Clear any previous errors
        const errorDiv = document.getElementById('recording-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
        
        // Start recording
        try {
            speechState.recognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            
            // Handle already started error
            if (error.message.includes('already started')) {
                speechState.recognition.stop();
                setTimeout(() => {
                    try {
                        speechState.recognition.start();
                    } catch (e) {
                        showToast('Please wait a moment and try again.', 'warning');
                    }
                }, 500);
            } else {
                showToast('Error starting microphone. Please try again.', 'error');
            }
        }
    }
}

/**
 * Stop voice recording
 */
function stopRecording() {
    if (speechState.recognition && speechState.isListening) {
        speechState.recognition.stop();
    }
}

/**
 * Update UI for speaking state
 */
function updateSpeakingUI(isSpeaking) {
    const speakBtn = document.getElementById('speak-question-btn');
    const stopSpeakBtn = document.getElementById('stop-speaking-btn');
    const questionText = document.getElementById('question-text');
    
    if (speakBtn && stopSpeakBtn && questionText) {
        if (isSpeaking) {
            speakBtn.style.display = 'none';
            stopSpeakBtn.style.display = 'inline-flex';
            questionText.classList.add('speaking');
        } else {
            speakBtn.style.display = 'inline-flex';
            stopSpeakBtn.style.display = 'none';
            questionText.classList.remove('speaking');
        }
    }
}

/**
 * Update UI for recording state
 */
function updateRecordingUI(isRecording) {
    const recordBtn = document.getElementById('record-answer-btn');
    const recordingIndicator = document.getElementById('recording-indicator');
    
    if (recordBtn) {
        if (isRecording) {
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            if (recordingIndicator) {
                recordingIndicator.style.display = 'flex';
            }
        } else {
            recordBtn.classList.remove('recording');
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Record Answer';
            if (recordingIndicator) {
                recordingIndicator.style.display = 'none';
            }
        }
    }
}

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
        // Initialize speech APIs
        initializeSpeechAPIs();
        
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
            if (typeof appState !== 'undefined') {
                appState.currentCandidateId = candidateId;
                if (typeof saveState === 'function') {
                    saveState();
                }
            }
            
            // Hide selection, show interview
            document.getElementById('candidate-selection').style.display = 'none';
            document.getElementById('interview-session').style.display = 'block';
            
            // Display first question
            displayCurrentQuestion();
            
            showLoading(false);
            showToast('Interview started! Click the speaker icon to hear the question.', 'success');
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
    
    // Reset speech states
    stopSpeaking();
    stopRecording();
    
    // Reset error count for new question
    speechState.networkErrorCount = 0;
    
    // Auto-speak question (optional - can be disabled)
    const autoSpeak = document.getElementById('auto-speak-questions')?.checked;
    if (autoSpeak) {
        setTimeout(() => speakQuestion(question.question_text), 500);
    }
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
    
    // Stop any ongoing recording or speaking
    stopRecording();
    stopSpeaking();
    
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
        // Stop any ongoing speech
        stopSpeaking();
        stopRecording();
        
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
        stopSpeaking();
        stopRecording();
        completeInterview();
    }
}

/**
 * Complete interview
 */
function completeInterview() {
    interviewState.isActive = false;
    
    // Stop any ongoing speech
    stopSpeaking();
    stopRecording();
    
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
    // Stop any ongoing speech
    stopSpeaking();
    stopRecording();
    
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

// Initialize speech APIs when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeSpeechAPIs();
});