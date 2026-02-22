/**
 * CampusIQ — API Service
 * Centralized HTTP client for all backend API calls.
 */

const API_BASE = '/api';

class ApiService {
    constructor() {
        this.token = localStorage.getItem('campusiq_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('campusiq_token', token);
        } else {
            localStorage.removeItem('campusiq_token');
        }
    }

    getToken() {
        return this.token || localStorage.getItem('campusiq_token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            this.setToken(null);
            window.location.href = '/login';
            throw new Error('Session expired. Please login again.');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Something went wrong');
        }

        return data;
    }

    // ─── Auth ────────────────────────────────────────────────
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setToken(data.access_token);
        return data;
    }

    async register(email, password, fullName, role) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName, role }),
        });
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // ─── Student ─────────────────────────────────────────────
    async getStudentDashboard() {
        return this.request('/students/me/dashboard');
    }

    async getMyAttendance() {
        return this.request('/students/me/attendance');
    }

    async getMyPredictions() {
        return this.request('/students/me/predictions');
    }

    // ─── Faculty ─────────────────────────────────────────────
    async getMyCourses() {
        return this.request('/faculty/me/courses');
    }

    async getRiskRoster(courseId) {
        return this.request(`/faculty/course/${courseId}/risk-roster`);
    }

    async generateQR(courseId, validSeconds = 90) {
        return this.request('/attendance/generate-qr', {
            method: 'POST',
            body: JSON.stringify({ course_id: courseId, valid_seconds: validSeconds }),
        });
    }

    async getAttendanceAnalytics(courseId) {
        return this.request(`/attendance/analytics/${courseId}`);
    }

    // ─── Admin ───────────────────────────────────────────────
    async getAdminDashboard() {
        return this.request('/admin/dashboard');
    }

    // ─── Predictions ─────────────────────────────────────────
    async getStudentPredictions(studentId) {
        return this.request(`/predictions/${studentId}`);
    }

    async getBatchPredictions(courseId) {
        return this.request(`/predictions/course/${courseId}/batch`);
    }

    // ─── Chatbot ─────────────────────────────────────────────
    async chatQuery(message) {
        return this.request('/chatbot/query', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    // ─── Utility ─────────────────────────────────────────────
    logout() {
        this.setToken(null);
        window.location.href = '/login';
    }
}

const api = new ApiService();
export default api;
