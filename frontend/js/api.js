
/**
 * API Service - Handles all backend communication
 */

const API_BASE_URL = '/api';

class APIService {

    async request(endpoint, options = {}) {
        try {
            const headers = { ...(options.headers || {}) };
            const isFormData = options.body instanceof FormData;

            if (!isFormData && !headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }

            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                credentials: 'include',
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== AUTH ====================

    async getMe() {
        return this.request('/me');
    }

    async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    }

    // ==================== PERSON A APIs ====================

    async parseResume(resumeText) {
        return this.request('/parse-resume', {
            method: 'POST',
            body: JSON.stringify({ resume_text: resumeText })
        });
    }

    async fullResumeProcessing(resumeText) {
        return this.request('/full-resume-processing', {
            method: 'POST',
            body: JSON.stringify({ resume_text: resumeText })
        });
    }

    async fullResumeProcessingPDF(file) {
        try {
            const formData = new FormData();
            formData.append('pdf_file', file);

            const response = await fetch(`${API_BASE_URL}/full-resume-processing`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== PERSON B APIs ====================

    async analyzeSpeech(audioBlob, referenceText = '') {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'answer.webm');
        formData.append('reference_text', referenceText);

        const response = await fetch(`${API_BASE_URL}/analyze-speech`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Speech analysis failed');
        }
        return data;
    }

    async recordResponse(questionId, answerText, knowledgeScore, speechScore, interviewSessionId = null) {
        return this.request('/record-response', {
            method: 'POST',
            body: JSON.stringify({
                question_id: questionId,
                answer_text: answerText,
                knowledge_score: knowledgeScore,
                speech_score: speechScore,
                interview_session_id: interviewSessionId
            })
        });
    }

    async getPerformanceSummary() {
        return this.request('/me/performance-summary');
    }

    // ==================== PERSON D APIs ====================

    async retrieveQuestions(options = {}) {
        const params = new URLSearchParams();
        if (options.maxQuestions) params.append('max_questions', options.maxQuestions);
        if (options.difficulty) params.append('difficulty', options.difficulty);
        if (options.category) params.append('category', options.category);

        const query = params.toString() ? `?${params.toString()}` : '';
        return this.request(`/me/retrieve-questions${query}`);
    }

    async getRecommendations() {
        return this.request('/me/recommendations');
    }

    async getCandidate() {
        return this.request('/me/candidate');
    }

    // ==================== PERSON C APIs ====================

    async addQuestion(questionData) {
        return this.request('/add-question', {
            method: 'POST',
            body: JSON.stringify(questionData)
        });
    }

    async bulkAddQuestions(questions) {
        return this.request('/bulk-add-questions', {
            method: 'POST',
            body: JSON.stringify({ questions })
        });
    }

    async getDatabaseSummary() {
        return this.request('/database-summary');
    }

    // ==================== COMMON APIs ====================

    async getStats() {
        return this.request('/stats');
    }

    async healthCheck() {
        return this.request('/health');
    }

    async getEmbedding(text) {
        return this.request('/get-embedding', {
            method: 'POST',
            body: JSON.stringify({ text })
        });
    }
}

const api = new APIService();
