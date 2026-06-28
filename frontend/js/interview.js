/**
 * Interview Session Logic - Person D (Retrieval) + Person B (Recording)
 * Enhanced with Text-to-Speech and Speech-to-Text
 * FIXED: Better network error handling
 */

// Interview state
const interviewState = {
    candidateId: null,
    sessionId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: [],
    isActive: false,
    startedAtMs: null
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
    maxNetworkRetries: 3,
    recordingSessionsStarted: 0,
    mediaRecorder: null,
    audioStream: null,
    audioChunks: [],
    recordedAudioBlob: null,
    audioMimeType: 'audio/webm'
};

/** Scoring weights — knowledge weighted higher (matches config.py) */
const SCORING_WEIGHTS = {
    knowledge: 0.6,
    speech: 0.4
};

function createInterviewSessionId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

const FILLER_PATTERNS = [
    /\bumm+\b/gi,
    /\buhm+\b/gi,
    /\buh+\b/gi,
    /\bhmm+\b/gi,
    /\bhm+\b/gi,
    /\ber+\b/gi,
    /\bah+\b/gi,
    /\blike\b/gi,
    /\byou know\b/gi,
    /\bbasically\b/gi,
    /\bactually\b/gi,
    /\bsort of\b/gi,
    /\bkind of\b/gi
];

/** Phrases that mean "ask the question again" — whole-utterance only, not mid-sentence use */
const REPEAT_QUESTION_EXACT = new Set([
    'repeat',
    'repeat please',
    'repeat the question',
    'repeat question',
    'repeat it',
    'repeat that',
    'pardon',
    'pardon me',
    'sorry pardon',
    'excuse me pardon',
    'say again',
    'say that again',
    'say it again',
    'come again',
    'once more',
    'what was the question',
    'what is the question',
    'can you repeat',
    'could you repeat',
    'would you repeat',
    'please repeat',
    'please repeat the question',
    'can you repeat the question',
    'could you repeat the question',
    'would you repeat the question',
    'can you say that again',
    'could you say that again',
    'can you say it again',
    'could you say it again',
    'i didnt hear',
    'i didnt catch',
    'i did not hear',
    'i did not catch',
    'sorry i didnt hear',
    'sorry i didnt catch',
    'didnt hear',
    'didnt catch'
]);

const REPEAT_QUESTION_PATTERNS = [
    /^(?:um |uh |hmm )*(?:can|could|would) you (?:please )?repeat(?: (?:the )?(?:question|it|that))?(?: please)?$/,
    /^(?:um |uh )*please repeat(?: (?:the )?(?:question|it|that))?(?: please)?$/,
    /^(?:um |uh )*repeat(?: (?:the )?(?:question|it|that))?(?: please)?$/,
    /^(?:excuse me )?(?:sorry )?pardon(?: me)?$/,
    /^(?:can|could|would) you (?:please )?say (?:that|it) again$/,
    /^(?:i )?(?:didnt|did not) (?:hear|catch)(?: (?:you|that|it|the question))?$/,
    /^what (?:was|is) (?:the )?question$/,
    /^(?:come again|once more)(?: please)?$/
];

function normalizeRepeatCheckText(text) {
    return String(text || '')
        .toLowerCase()
        .replace(/['']/g, '')
        .replace(/[^\w\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

/**
 * True when the user is asking to hear the question again — not answering with
 * "repeat"/"pardon" used in normal speech (e.g. "repeat the deployment process").
 */
function isRepeatQuestionRequest(answerText) {
    const normalized = normalizeRepeatCheckText(answerText);
    if (!normalized) {
        return false;
    }

    const wordCount = normalized.split(/\s+/).length;

    if (REPEAT_QUESTION_EXACT.has(normalized)) {
        return true;
    }

    const withoutTrailingPlease = normalized.replace(/\s+please$/, '').trim();
    if (REPEAT_QUESTION_EXACT.has(withoutTrailingPlease)) {
        return true;
    }

    // Long answers are real responses even if they contain "repeat" or "pardon"
    if (wordCount > 10) {
        return false;
    }

    return REPEAT_QUESTION_PATTERNS.some(pattern => pattern.test(normalized));
}

/**
 * Re-ask the current question without advancing or scoring.
 */
async function repeatCurrentQuestion() {
    const question = interviewState.questions[interviewState.currentQuestionIndex];

    document.getElementById('answer-text').value = '';
    const interimEl = document.getElementById('interim-transcript');
    if (interimEl) {
        interimEl.textContent = '';
    }
    document.getElementById('answer-feedback').style.display = 'none';

    await stopRecording();
    stopSpeaking();
    speechState.recordingSessionsStarted = 0;
    resetQuestionAudioCapture();

    showToast('Repeating the question...', 'info');
    setTimeout(() => speakQuestion(question.question_text), 400);
}

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
                    startRecording(false);
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
 * Ensure microphone stream and start capturing raw audio for server analysis.
 */
async function ensureAudioStream() {
    if (speechState.audioStream) {
        return speechState.audioStream;
    }
    speechState.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    return speechState.audioStream;
}

async function startAudioCapture() {
    if (speechState.mediaRecorder && speechState.mediaRecorder.state === 'recording') {
        return;
    }

    try {
        const stream = await ensureAudioStream();
        const preferredTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus'
        ];
        const mimeType = preferredTypes.find(type => MediaRecorder.isTypeSupported(type)) || '';
        speechState.audioMimeType = mimeType || 'audio/webm';

        const options = mimeType ? { mimeType } : undefined;
        speechState.mediaRecorder = new MediaRecorder(stream, options);
        speechState.audioChunks = [];

        speechState.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                speechState.audioChunks.push(event.data);
            }
        };

        speechState.mediaRecorder.start(250);
    } catch (error) {
        console.warn('Could not start audio capture:', error);
    }
}

function finalizeAudioBlob() {
    if (!speechState.audioChunks.length) {
        return speechState.recordedAudioBlob;
    }
    speechState.recordedAudioBlob = new Blob(
        speechState.audioChunks,
        { type: speechState.audioMimeType || 'audio/webm' }
    );
    return speechState.recordedAudioBlob;
}

async function stopAudioCapture() {
    if (!speechState.mediaRecorder || speechState.mediaRecorder.state === 'inactive') {
        return finalizeAudioBlob();
    }

    return new Promise((resolve) => {
        speechState.mediaRecorder.onstop = () => {
            resolve(finalizeAudioBlob());
        };
        speechState.mediaRecorder.stop();
    });
}

function resetQuestionAudioCapture() {
    speechState.audioChunks = [];
    speechState.recordedAudioBlob = null;
    speechState.mediaRecorder = null;
}

async function releaseAudioStream() {
    if (speechState.mediaRecorder && speechState.mediaRecorder.state === 'recording') {
        await stopAudioCapture();
    }
    if (speechState.audioStream) {
        speechState.audioStream.getTracks().forEach(track => track.stop());
        speechState.audioStream = null;
    }
    resetQuestionAudioCapture();
}

/**
 * Start voice recording for answer - IMPROVED
 * @param {boolean} userInitiated - false for automatic retries (do not count as pauses)
 */
async function startRecording(userInitiated = true) {
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
        
        // First session is normal; later user-initiated starts count as pauses
        if (userInitiated) {
            speechState.recordingSessionsStarted += 1;
        }
        try {
            await startAudioCapture();
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
async function stopRecording() {
    if (speechState.recognition && speechState.isListening) {
        speechState.recognition.stop();
    }
    await stopAudioCapture();
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
 * Format elapsed interview time for the completion summary
 */
function formatInterviewDuration(elapsedMs) {
    const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`;
    }
    if (minutes > 0) {
        return `${minutes} min ${seconds} sec`;
    }
    return `${seconds} sec`;
}

/**
 * Start interview session
 */
async function startInterview() {
    if (!requireProfile('interview')) return;

    showLoading(true);

    try {
        initializeSpeechAPIs();

        const maxQuestions = parseInt(document.getElementById('question-count').value);
        const difficulty = document.getElementById('difficulty-level').value;
        const category = document.getElementById('category-filter').value;

        const options = { maxQuestions };
        if (difficulty) options.difficulty = difficulty;
        if (category) options.category = category;

        const result = await api.retrieveQuestions(options);

        if (result.success && result.questions.length > 0) {
            if (result.questions.length < maxQuestions) {
                showToast(
                    `Only ${result.questions.length} questions matched your filters (requested ${maxQuestions}).`,
                    'warning'
                );
            }

            interviewState.candidateId = 'session';
            interviewState.sessionId = createInterviewSessionId();
            interviewState.questions = result.questions;
            interviewState.currentQuestionIndex = 0;
            interviewState.answers = [];
            interviewState.isActive = true;
            interviewState.startedAtMs = Date.now();

            document.getElementById('candidate-selection').style.display = 'none';
            document.getElementById('interview-session').style.display = 'block';

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
async function displayCurrentQuestion() {
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
    
    // Clear answer textarea
    document.getElementById('answer-text').value = '';
    
    // Hide feedback
    document.getElementById('answer-feedback').style.display = 'none';
    
    // Reset speech states
    stopSpeaking();
    await stopRecording();
    
    // Reset error count and recording session counter for new question
    speechState.networkErrorCount = 0;
    speechState.recordingSessionsStarted = 0;
    resetQuestionAudioCapture();
    
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

    if (isRepeatQuestionRequest(answerText)) {
        await repeatCurrentQuestion();
        return;
    }
    
    // Stop any ongoing recording or speaking
    await stopRecording();
    stopSpeaking();
    
    showLoading(true);
    
    const question = interviewState.questions[interviewState.currentQuestionIndex];
    
    try {
        const pauseCount = Math.max(0, speechState.recordingSessionsStarted - 1);
        const knowledgeScore = await calculateKnowledgeScore(answerText, question);

        let speechScore = calculateSpeechScore(answerText, pauseCount);
        let speechBreakdown = null;
        let speechSource = 'text';

        const audioBlob = speechState.recordedAudioBlob || finalizeAudioBlob();
        if (audioBlob && audioBlob.size > 800) {
            try {
                const speechResult = await api.analyzeSpeech(audioBlob, answerText);
                if (speechResult.success && typeof speechResult.speech_score === 'number') {
                    speechScore = speechResult.speech_score;
                    speechBreakdown = speechResult.breakdown || null;
                    speechSource = speechResult.source || 'audio';
                }
            } catch (audioError) {
                console.warn('Audio speech analysis failed, using text fallback:', audioError);
                speechSource = 'text_fallback';
            }
        }
        
        // Record response
        await api.recordResponse(
            question.question_id,
            answerText,
            knowledgeScore,
            speechScore,
            interviewState.sessionId
        );
        
        // Store answer
        interviewState.answers.push({
            questionId: question.question_id,
            questionText: question.question_text,
            answerText: answerText,
            knowledgeScore: knowledgeScore,
            speechScore: speechScore,
            totalScore: computeTotalScore(knowledgeScore, speechScore),
            pauseCount: pauseCount,
            speechBreakdown: speechBreakdown,
            speechSource: speechSource,
            topics: question.topics || [],
            idealKeywords: question.ideal_keywords || [],
            jobRoles: question.job_roles || []
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

function clampScore(value) {
    return Math.max(0, Math.min(1, value));
}

function computeTotalScore(knowledgeScore, speechScore) {
    return clampScore(
        knowledgeScore * SCORING_WEIGHTS.knowledge +
        speechScore * SCORING_WEIGHTS.speech
    );
}

/**
 * Cosine similarity between two normalized embedding vectors
 */
function cosineSimilarity(vecA, vecB) {
    if (!vecA?.length || !vecB?.length || vecA.length !== vecB.length) {
        return 0;
    }
    let dot = 0;
    for (let i = 0; i < vecA.length; i++) {
        dot += vecA[i] * vecB[i];
    }
    return dot;
}

/**
 * Map raw cosine similarity (0–1 on related answers) to a 0–1 knowledge score
 */
function mapSimilarityToKnowledgeScore(similarity) {
    const floor = 0.25;
    const span = 0.65;
    if (similarity <= floor) {
        return clampScore(similarity / floor * 0.35);
    }
    return clampScore(0.35 + ((similarity - floor) / span) * 0.65);
}

function countFillerWords(answer) {
    let count = 0;
    FILLER_PATTERNS.forEach(pattern => {
        const matches = answer.match(pattern);
        if (matches) count += matches.length;
    });
    return count;
}

/**
 * Fallback when ideal_answer_embedding is unavailable
 */
function calculateKnowledgeScoreFallback(answer, question) {
    const wordCount = answer.trim().split(/\s+/).length;
    if (wordCount <= 2) return 0.1;
    if (wordCount <= 5) return 0.3;

    let score = 0.35;
    const answerLower = answer.toLowerCase();
    const signals = [
        ...(question.ideal_keywords || []),
        ...(question.topics || [])
    ];

    let keywordMatches = 0;
    signals.forEach(signal => {
        const token = String(signal || '').toLowerCase().trim();
        if (token && answerLower.includes(token)) {
            keywordMatches++;
        }
    });

    if (keywordMatches > 0) {
        score += Math.min(0.45, keywordMatches * 0.12);
    }
    if (wordCount >= 30) score += 0.1;
    if (wordCount >= 50) score += 0.1;

    return clampScore(score);
}

/**
 * Knowledge score: cosine similarity between answer and ideal-answer embeddings
 */
async function calculateKnowledgeScore(answer, question) {
    const wordCount = answer.trim().split(/\s+/).length;
    if (wordCount <= 2) return 0.1;
    if (wordCount <= 5) return 0.25;

    const idealVector = question.ideal_answer_embedding;
    if (!idealVector?.length) {
        return calculateKnowledgeScoreFallback(answer, question);
    }

    try {
        const result = await api.getEmbedding(answer);
        const answerVector = result.embedding;
        const similarity = cosineSimilarity(answerVector, idealVector);
        let score = mapSimilarityToKnowledgeScore(similarity);

        if (wordCount < 10) {
            score *= 0.75;
        } else if (wordCount < 20) {
            score *= 0.9;
        }

        return clampScore(score);
    } catch (error) {
        console.warn('Embedding API unavailable, using keyword fallback:', error);
        return calculateKnowledgeScoreFallback(answer, question);
    }
}

/**
 * Speech score: filler-word usage and extra recording sessions (pauses)
 * @param {number} pauseCount - recording starts after the first (ignored)
 */
function calculateSpeechScore(answer, pauseCount = 0) {
    const wordCount = answer.trim().split(/\s+/).length;
    if (wordCount <= 2) return 0.15;
    if (wordCount <= 5) return 0.3;

    let score = 1.0;

    const fillerCount = countFillerWords(answer);
    const fillerPenalty = Math.min(0.45, fillerCount * 0.09);
    score -= fillerPenalty;

    const pausePenalty = Math.min(0.4, pauseCount * 0.12);
    score -= pausePenalty;

    const sentences = answer.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length >= 2 && fillerCount <= 2) {
        score += 0.05;
    }

    return clampScore(score);
}

/**
 * Display answer feedback
 */
function displayAnswerFeedback(knowledgeScore, speechScore) {
    const totalScore = computeTotalScore(knowledgeScore, speechScore);
    
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
        stopSpeaking();
        stopRecording().then(() => {
            const question = interviewState.questions[interviewState.currentQuestionIndex];

            interviewState.answers.push({
                questionId: question.question_id,
                questionText: question.question_text,
                answerText: '[Skipped]',
                knowledgeScore: 0,
                speechScore: 0,
                totalScore: 0,
                topics: question.topics || [],
                idealKeywords: question.ideal_keywords || [],
                jobRoles: question.job_roles || []
            });

            nextQuestion();
        });
    }
}

/**
 * End interview early
 */
function endInterview() {
    if (confirm('Are you sure you want to end the interview? Your progress will be saved.')) {
        stopSpeaking();
        stopRecording().then(() => completeInterview());
    }
}

/**
 * Complete interview
 */
function normalizeToken(text) {
    return String(text || '').toLowerCase().trim();
}

function answerIncludesKeyword(answerText, keyword) {
    const answer = normalizeToken(answerText);
    const key = normalizeToken(keyword);
    if (!answer || !key) return false;
    return answer.includes(key);
}

function countOccurrences(items) {
    const counts = {};
    (items || []).forEach(item => {
        const normalized = normalizeToken(item);
        if (!normalized) return;
        counts[normalized] = (counts[normalized] || 0) + 1;
    });
    return counts;
}

function pickTopKeys(countMap, limit = 5) {
    return Object.entries(countMap || {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([key]) => key);
}

function getExpectedKeywords(answer) {
    return (answer.idealKeywords && answer.idealKeywords.length > 0)
        ? answer.idealKeywords
        : (answer.topics || []);
}

function getMissingKeywordsForAnswer(answer) {
    return getExpectedKeywords(answer).filter(
        keyword => !answerIncludesKeyword(answer.answerText, keyword)
    );
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function computeInterviewImprovementFeedback(answers) {
    const attempted = (answers || []).filter(a => a.answerText !== '[Skipped]');
    const lowScoreAnswers = attempted.filter(a => (a.knowledgeScore || 0) < 0.6);

    const weakTopicCounts = countOccurrences(
        lowScoreAnswers.flatMap(a => a.topics || [])
    );
    const weakTopics = pickTopKeys(weakTopicCounts, 5);

    const missingKeywordCounts = {};
    attempted.forEach(answer => {
        getMissingKeywordsForAnswer(answer).forEach(keyword => {
            const normalized = normalizeToken(keyword);
            if (!normalized) return;
            missingKeywordCounts[normalized] = (missingKeywordCounts[normalized] || 0) + 1;
        });
    });

    const missingKeywords = pickTopKeys(missingKeywordCounts, 8);
    const focusAreas = weakTopics.length > 0 ? weakTopics : missingKeywords.slice(0, 4);

    const staticSentence = focusAreas.length > 0
        ? `These are the topics you need to focus more on: ${focusAreas.join(', ')}.`
        : 'Your performance is stable; continue practicing with more depth in your explanations.';

    const basicsSentence = missingKeywords.length > 0
        ? `Brush up on basics like ${missingKeywords.slice(0, 4).join(', ')} and include these terms explicitly in your answers.`
        : 'Try to include key concepts and terminology clearly while answering to improve your score.';

    const questionFeedback = (answers || []).map((answer, index) => ({
        questionNumber: index + 1,
        questionText: answer.questionText || `Question ${index + 1}`,
        answerText: answer.answerText,
        missingKeywords: getMissingKeywordsForAnswer(answer)
    }));

    return {
        focusAreas,
        missingKeywords,
        sentences: [staticSentence, basicsSentence],
        questionFeedback
    };
}

function buildRoleSkillMap() {
    return {
        'data scientist': ['python', 'machine learning', 'statistics', 'sql', 'pandas', 'numpy', 'model evaluation'],
        'ml engineer': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'mlops', 'deployment'],
        'software engineer': ['data structures', 'algorithms', 'system design', 'oop', 'git', 'testing'],
        'backend engineer': ['apis', 'database', 'sql', 'microservices', 'scalability', 'caching'],
        'frontend engineer': ['javascript', 'html', 'css', 'react', 'state management', 'performance'],
        'product manager': ['product strategy', 'metrics', 'stakeholder management', 'prioritization']
    };
}

function computeResumeSuggestions(resume = {}, answers = []) {
    const roleCounts = countOccurrences(answers.flatMap(a => a.jobRoles || []));
    const topRoles = pickTopKeys(roleCounts, 3);
    const primaryRole = topRoles[0] || '';

    const roleSkillMap = buildRoleSkillMap();
    const roleSkills = roleSkillMap[primaryRole] || [];
    const interviewTopics = pickTopKeys(countOccurrences(answers.flatMap(a => a.topics || [])), 8);
    const requiredSignals = [...new Set([...roleSkills, ...interviewTopics.map(normalizeToken)])];

    const resumeSkills = (resume.skills || []).map(normalizeToken);
    const missingSkills = requiredSignals.filter(skill =>
        skill && !resumeSkills.some(rs => rs.includes(skill) || skill.includes(rs))
    );

    const hasExperience = (resume.experience || []).length > 0;
    const projectText = (resume.projects || [])
        .map(p => `${p.name || ''} ${p.description || ''}`)
        .join(' ')
        .toLowerCase();
    const hasMetrics = /\b(\d+(\.\d+)?%|accuracy|f1|auc|precision|recall|latency)\b/.test(projectText);
    const roleLooksML = primaryRole.includes('data scientist') || primaryRole.includes('ml');

    const sentences = [];
    if (missingSkills.length > 0) {
        sentences.push(`For the ${primaryRole || 'target'} role, consider adding or highlighting skills such as: ${missingSkills.slice(0, 6).join(', ')}.`);
    } else {
        sentences.push('Your resume aligns reasonably well with the role topics from this interview; keep skill names explicit for better matching.');
    }

    if (!hasExperience) {
        sentences.push('Add internship, freelance, or academic project experience to show practical application of your skills.');
    }

    if (roleLooksML && !hasMetrics) {
        sentences.push('For ML projects, include measurable outcomes like model accuracy, F1-score, AUC, or latency improvements.');
    } else if (!hasMetrics) {
        sentences.push('Add measurable impact in projects (percent improvements, scale, or business outcomes) to strengthen your resume.');
    }

    return {
        topRoles,
        missingSkills: missingSkills.slice(0, 8),
        sentences
    };
}

function renderSuggestionList(items) {
    return `
        <ul style="margin: 0.75rem 0 0 1rem; color: var(--text-secondary);">
            ${items.map(item => `<li style="margin-bottom: 0.4rem;">${item}</li>`).join('')}
        </ul>
    `;
}

function renderQuestionImprovementFeedback(questionFeedback) {
    if (!questionFeedback || questionFeedback.length === 0) {
        return '';
    }

    return `
        <div style="margin-top: 1rem;">
            <p style="margin-bottom: 0.5rem;"><strong>Question-wise keyword feedback</strong></p>
            ${questionFeedback.map((item, index) => `
                <div style="margin-top: ${index === 0 ? '0' : '1rem'}; padding-top: ${index === 0 ? '0' : '1rem'}; border-top: ${index === 0 ? 'none' : '1px solid var(--border-color)'};">
                    <p style="margin-bottom: 0.5rem;"><strong>Q${item.questionNumber}:</strong> ${escapeHtml(item.questionText)}</p>
                    <p style="margin-bottom: 0.35rem; color: var(--text-secondary);">
                        <strong>Your answer:</strong> ${escapeHtml(item.answerText)}
                    </p>
                    <p style="color: var(--text-secondary);">
                        <strong>Missing expected keywords:</strong>
                        ${item.missingKeywords.length > 0
                            ? escapeHtml(item.missingKeywords.join(', '))
                            : '<span style="color: var(--success-color, #10B981);">None</span>'}
                    </p>
                </div>
            `).join('')}
        </div>
    `;
}

async function completeInterview() {
    interviewState.isActive = false;
    
    // Stop any ongoing speech
    stopSpeaking();
    await stopRecording();
    
    // Calculate final statistics
    const totalAnswers = interviewState.answers.length;
    const avgScore = totalAnswers > 0
        ? interviewState.answers.reduce((sum, a) => sum + a.totalScore, 0) / totalAnswers
        : 0;
    const skipped = interviewState.answers.filter(a => a.answerText === '[Skipped]').length;
    const improvementFeedback = computeInterviewImprovementFeedback(interviewState.answers);
    const elapsedMs = interviewState.startedAtMs ? Date.now() - interviewState.startedAtMs : 0;
    const totalDuration = formatInterviewDuration(elapsedMs);

    let resumeSuggestions = {
        sentences: ['Resume suggestions could not be generated at this time.'],
        topRoles: [],
        missingSkills: []
    };

    try {
        const candidateData = await api.getCandidate();
        resumeSuggestions = computeResumeSuggestions(candidateData.resume || {}, interviewState.answers);
    } catch (error) {
        console.error('Could not fetch candidate resume for suggestions:', error);
    }
    
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
            <div class="stat-card">
                <i class="fas fa-clock"></i>
                <h3>${totalDuration}</h3>
                <p>Total Time</p>
            </div>
        </div>
        <p style="margin-top: 1.5rem; color: var(--text-secondary);">
            Great job! Your responses have been recorded and your profile has been updated.
            Check your dashboard for detailed analytics.
        </p>
        <div style="margin-top: 1.5rem; background: var(--bg-color); border-radius: 0.75rem; padding: 1rem;">
            <h4 style="margin-bottom: 0.5rem;"><i class="fas fa-lightbulb"></i> Interview Improvement Feedback</h4>
            ${renderSuggestionList(improvementFeedback.sentences)}
            ${renderQuestionImprovementFeedback(improvementFeedback.questionFeedback)}
        </div>
        <div style="margin-top: 1rem; background: var(--bg-color); border-radius: 0.75rem; padding: 1rem;">
            <h4 style="margin-bottom: 0.5rem;"><i class="fas fa-file-alt"></i> Resume Enhancement Suggestions</h4>
            ${renderSuggestionList(resumeSuggestions.sentences)}
            ${resumeSuggestions.topRoles.length > 0 ? `
                <p style="margin-top: 0.75rem;"><strong>Role context from interview:</strong> ${resumeSuggestions.topRoles.join(', ')}</p>
            ` : ''}
        </div>
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
 * Reset interview UI without requiring an active session
 */
function resetInterviewUI() {
    stopSpeaking();
    if (speechState.mediaRecorder && speechState.mediaRecorder.state === 'recording') {
        speechState.mediaRecorder.stop();
    }
    if (speechState.audioStream) {
        speechState.audioStream.getTracks().forEach(track => track.stop());
        speechState.audioStream = null;
    }

    interviewState.candidateId = null;
    interviewState.sessionId = null;
    interviewState.questions = [];
    interviewState.currentQuestionIndex = 0;
    interviewState.answers = [];
    interviewState.isActive = false;
    interviewState.startedAtMs = null;

    const selection = document.getElementById('candidate-selection');
    const session = document.getElementById('interview-session');
    const complete = document.getElementById('interview-complete');

    if (selection) selection.style.display = 'block';
    if (session) session.style.display = 'none';
    if (complete) complete.style.display = 'none';

    if (session) {
        const progressSection = session.querySelector('.progress-section');
        const questionCard = session.querySelector('.question-card');
        const answerSection = session.querySelector('.answer-section');
        if (progressSection) progressSection.style.display = 'block';
        if (questionCard) questionCard.style.display = 'block';
        if (answerSection) answerSection.style.display = 'block';
    }
}

/**
 * Reset interview
 */
async function resetInterview() {
    await resetInterviewUI();
    await releaseAudioStream();
}

// Initialize speech APIs when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeSpeechAPIs();
});