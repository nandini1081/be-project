
/**
 * API Service - Handles all backend communication
 */

const API_BASE_URL = 'http://localhost:5000/api';

class APIService {
    
    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
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
    
    // ==================== PERSON A APIs ====================
    
    /**
     * Parse resume text
     */
    async parseResume(resumeText) {
        return this.request('/parse-resume', {
            method: 'POST',
            body: JSON.stringify({ resume_text: resumeText })
        });
    }
    
    /**
     * Create candidate profile
     */
    async createProfile(resumeData, candidateId = null) {
        return this.request('/create-profile', {
            method: 'POST',
            body: JSON.stringify({ 
                resume_data: resumeData,
                candidate_id: candidateId
            })
        });
    }
    
    /**
     * Full resume processing pipeline
     */
    async fullResumeProcessing(resumeText, candidateId = null) {
        return this.request('/full-resume-processing', {
            method: 'POST',
            body: JSON.stringify({ 
                resume_text: resumeText,
                candidate_id: candidateId
            })
        });
    }
    
    // ==================== PERSON B APIs ====================
    
    /**
     * Update candidate profile
     */
    async updateProfile(candidateId) {
        return this.request(`/update-profile/${candidateId}`, {
            method: 'POST'
        });
    }
    
    /**
     * Record interview response
     */
    async recordResponse(candidateId, questionId, answerText, knowledgeScore, speechScore) {
        return this.request('/record-response', {
            method: 'POST',
            body: JSON.stringify({
                candidate_id: candidateId,
                question_id: questionId,
                answer_text: answerText,
                knowledge_score: knowledgeScore,
                speech_score: speechScore
            })
        });
    }
    
    /**
     * Get performance summary
     */
    async getPerformanceSummary(candidateId) {
        return this.request(`/performance-summary/${candidateId}`);
    }
    
    // ==================== PERSON C APIs ====================
    
    /**
     * Add single question
     */
    async addQuestion(questionData) {
        return this.request('/add-question', {
            method: 'POST',
            body: JSON.stringify(questionData)
        });
    }
    
    /**
     * Bulk add questions
     */
    async bulkAddQuestions(questions) {
        return this.request('/bulk-add-questions', {
            method: 'POST',
            body: JSON.stringify({ questions })
        });
    }
    
    /**
     * Get database summary
     */
    async getDatabaseSummary() {
        return this.request('/database-summary');
    }
    
    // ==================== PERSON D APIs ====================
    
    /**
     * Retrieve personalized questions
     */
    async retrieveQuestions(candidateId, options = {}) {
        const params = new URLSearchParams();
        if (options.maxQuestions) params.append('max_questions', options.maxQuestions);
        if (options.difficulty) params.append('difficulty', options.difficulty);
        if (options.category) params.append('category', options.category);
        
        const query = params.toString() ? `?${params.toString()}` : '';
        return this.request(`/retrieve-questions/${candidateId}${query}`);
    }
    
    /**
     * Get adaptive questions
     */
    async getAdaptiveQuestions(candidateId, lastScore = null, maxQuestions = 5) {
        const params = new URLSearchParams();
        if (lastScore !== null) params.append('last_score', lastScore);
        params.append('max_questions', maxQuestions);
        
        return this.request(`/adaptive-questions/${candidateId}?${params.toString()}`);
    }
    
    /**
     * Get diverse questions
     */
    async getDiverseQuestions(candidateId, perCategory = 3) {
        return this.request(`/diverse-questions/${candidateId}?per_category=${perCategory}`);
    }
    
    /**
     * Get question recommendations
     */
    async getRecommendations(candidateId) {
        return this.request(`/recommendations/${candidateId}`);
    }
    
    // ==================== COMMON APIs ====================
    
    /**
     * Get candidate information
     */
    async getCandidate(candidateId) {
        return this.request(`/candidate/${candidateId}`);
    }
    
    /**
     * Get database statistics
     */
    async getStats() {
        return this.request('/stats');
    }
    
    /**
     * Health check
     */
    async healthCheck() {
        return this.request('/health');
    }
}

// Create global API instance
const api = new APIService();
