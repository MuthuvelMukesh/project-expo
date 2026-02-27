/**
 * CampusIQ — API Service
 * Centralized HTTP client for all backend API calls.
 * Uses httpOnly cookies for authentication.
 */

import {
    buildAuditQuery,
    buildConversationalPayload,
    buildOperationalRollbackPayload,
} from './operationalAI.contract';

const API_BASE = '/api';

class ApiService {
    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
            credentials: 'include',  // Send cookies with every request
        });

        if (response.status === 401) {
            // Don't redirect for auth-check calls or if already on login page
            const isAuthCheck = endpoint === '/auth/me';
            const isOnLogin = window.location.pathname === '/login';
            if (!isAuthCheck && !isOnLogin) {
                window.location.href = '/login';
            }
            throw new Error('Session expired. Please login again.');
        }

        const contentType = response.headers.get('content-type') || '';
        const rawBody = await response.text();

        let data = null;
        if (rawBody && contentType.includes('application/json')) {
            try {
                data = JSON.parse(rawBody);
            } catch {
                throw new Error('Invalid JSON response from server. Please try again.');
            }
        } else if (rawBody) {
            data = { detail: rawBody };
        }

        if (!response.ok) {
            const detail =
                data?.detail ||
                data?.message ||
                (rawBody ? rawBody.slice(0, 200) : '') ||
                'Something went wrong';
            throw new Error(detail);
        }

        return data ?? {};
    }

    // ─── Generic convenience methods ─────────────────────────
    // These handle paths with or without the /api prefix
    _normalizePath(path) {
        return path.startsWith('/api/') ? path.slice(4) : path;
    }

    async get(url) {
        return this.request(this._normalizePath(url));
    }

    async post(url, body = {}) {
        return this.request(this._normalizePath(url), {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async put(url, body = {}) {
        return this.request(this._normalizePath(url), {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    }

    // ─── Auth ────────────────────────────────────────────────
    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
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

    // ─── AI Data Operations (NLP CRUD) ──────────────────────
    async aiDataQuery(message, context = null) {
        return this.request('/ai-data/query', {
            method: 'POST',
            body: JSON.stringify({ message, context }),
        });
    }

    // ─── Operational AI (Conversational Ops) ────────────────
    async operationalAIExecute(message, module = 'nlp') {
        return this.request('/ops-ai/execute', {
            method: 'POST',
            body: JSON.stringify(buildConversationalPayload(message, module)),
        });
    }

    async operationalAIRollback(executionId) {
        return this.request('/ops-ai/rollback', {
            method: 'POST',
            body: JSON.stringify(buildOperationalRollbackPayload(executionId)),
        });
    }

    async operationalAIAudit(filters = {}) {
        const q = buildAuditQuery(filters);
        return this.request(`/ops-ai/history${q ? `?${q}` : ''}`);
    }

    async getOpsStats() {
        return this.request('/ops-ai/stats');
    }

    // ─── User Management (Admin) ─────────────────────────────
    async listUsers(role = null) {
        const q = role ? `?role=${role}` : '';
        return this.request(`/users/${q}`);
    }

    async createUser(data) {
        return this.request('/users/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateUser(userId, data) {
        return this.request(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async toggleUserActive(userId) {
        return this.request(`/users/${userId}`, { method: 'DELETE' });
    }

    // ─── Course Management ───────────────────────────────────
    async listCourses(departmentId = null) {
        const q = departmentId ? `?department_id=${departmentId}` : '';
        return this.request(`/courses/${q}`);
    }

    async createCourse(data) {
        return this.request('/courses/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateCourse(courseId, data) {
        return this.request(`/courses/${courseId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteCourse(courseId) {
        return this.request(`/courses/${courseId}`, { method: 'DELETE' });
    }

    // ─── Department Management ───────────────────────────────
    async listDepartments() {
        return this.request('/departments/');
    }

    async createDepartment(data) {
        return this.request('/departments/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateDepartment(deptId, data) {
        return this.request(`/departments/${deptId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteDepartment(deptId) {
        return this.request(`/departments/${deptId}`, { method: 'DELETE' });
    }

    // ─── Notifications ───────────────────────────────────────
    async getNotifications(unreadOnly = false) {
        const q = unreadOnly ? '?unread_only=true' : '';
        return this.request(`/notifications/${q}`);
    }

    async getUnreadCount() {
        return this.request('/notifications/count');
    }

    async markNotificationRead(notifId) {
        return this.request(`/notifications/${notifId}/read`, { method: 'PUT' });
    }

    async markAllNotificationsRead() {
        return this.request('/notifications/read-all', { method: 'PUT' });
    }

    // ─── Student Profile ─────────────────────────────────────
    async getStudentProfile() {
        return this.request('/students/me/profile');
    }

    async updateStudentProfile(data) {
        return this.request('/students/me/profile', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async getAttendanceDetails() {
        return this.request('/students/me/attendance/details');
    }

    // ─── Password ────────────────────────────────────────────
    async forgotPassword(email) {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
    }

    async resetPassword(token, newPassword) {
        return this.request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, new_password: newPassword }),
        });
    }

    async changePassword(oldPassword, newPassword) {
        return this.request('/auth/change-password', {
            method: 'PUT',
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });
    }

    // ─── Export ──────────────────────────────────────────────
    getExportUrl(type, id = null) {
        // Auth is handled via httpOnly cookies (credentials: 'include')
        const base = '/api/export';
        if (type === 'students') return `${base}/students`;
        if (type === 'attendance') return `${base}/attendance/${id}`;
        if (type === 'risk-roster') return `${base}/risk-roster/${id}`;
        return base;
    }

    // ─── Timetable ────────────────────────────────────────────
    getStudentTimetable() { return this.request('/timetable/student'); }
    getFacultyTimetable() { return this.request('/timetable/faculty'); }
    createTimetableSlot(data) { return this.request('/timetable/', { method: 'POST', body: JSON.stringify(data) }); }
    deleteTimetableSlot(id) { return this.request(`/timetable/${id}`, { method: 'DELETE' }); }

    // ─── Financial Management ──────────────────────────────────
    async createFeeStructure(data) {
        return this.request('/finance/fee-structures', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async listFeeStructures() {
        return this.request('/finance/fee-structures');
    }

    async getStudentBalance(studentId) {
        return this.request(`/finance/student-balance/${studentId}`);
    }

    async createInvoice(studentId) {
        return this.request(`/finance/invoices/generate/${studentId}`, {
            method: 'POST',
        });
    }

    async getInvoices(studentId = null) {
        if (studentId) {
            return this.request(`/finance/invoices/student/${studentId}`);
        }
        return this.request('/finance/invoices');
    }

    async recordPayment(data) {
        return this.request('/finance/payments', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getPayments(invoiceId = null) {
        const q = invoiceId ? `?invoice_id=${invoiceId}` : '';
        return this.request(`/finance/payments${q}`);
    }

    async getFinanceReports(reportType) {
        // reportType: 'outstanding', 'collection', 'revenue'
        return this.request(`/finance/reports/${reportType}`);
    }

    async verifyPayment(paymentId) {
        return this.request(`/finance/payments/${paymentId}/verify`, {
            method: 'PUT',
        });
    }

    // ─── HR & Payroll Management ───────────────────────────────
    async createEmployee(data) {
        return this.request('/hr/employees', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async listEmployees() {
        return this.request('/hr/employees');
    }

    async getEmployeeDetails(employeeId) {
        return this.request(`/hr/employees/${employeeId}`);
    }

    async updateEmployee(employeeId, data) {
        return this.request(`/hr/employees/${employeeId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async createSalaryStructure(data) {
        return this.request('/hr/salary-structures', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getSalaryStructure(employeeId) {
        return this.request(`/hr/salary-structures/${employeeId}`);
    }

    async updateSalaryStructure(structureId, data) {
        return this.request(`/hr/salary-structures/${structureId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async processSalary(data) {
        // body: { employee_id, month, year }
        return this.request('/hr/salary-records/process', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getSalaryRecords(employeeId = null) {
        const q = employeeId ? `?employee_id=${employeeId}` : '';
        return this.request(`/hr/salary-records${q}`);
    }

    async getSalarySlip(recordId) {
        return this.request(`/hr/salary-records/${recordId}/slip`);
    }

    async markSalaryPaid(recordId) {
        return this.request(`/hr/salary-records/${recordId}/pay`, {
            method: 'POST',
        });
    }

    async getPayrollReport(reportType, month = null, year = null) {
        // reportType: 'summary', 'slip'
        const params = new URLSearchParams();
        if (month) params.set('month', month);
        if (year) params.set('year', year);
        const q = params.toString();
        return this.request(`/hr/reports/${reportType}${q ? `?${q}` : ''}`);
    }

    async recordEmployeeAttendance(data) {
        // body: { employee_id, date, check_in, check_out, hours_worked }
        return this.request('/hr/attendance', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getEmployeeAttendance(employeeId, month = null, year = null) {
        const params = new URLSearchParams();
        if (month) params.set('month', month);
        if (year) params.set('year', year);
        const q = params.toString();
        return this.request(`/hr/attendance/${employeeId}${q ? `?${q}` : ''}`);
    }

    // ─── Employee Update & Delete ──────────────────────────────
    async deleteEmployee(employeeId) {
        return this.request(`/hr/employees/${employeeId}`, { method: 'DELETE' });
    }

    // ─── Employee Directory ────────────────────────────────────
    async getEmployeeDirectory(search = null, employeeType = null) {
        const params = new URLSearchParams();
        if (search) params.set('search', search);
        if (employeeType) params.set('employee_type', employeeType);
        const q = params.toString();
        return this.request(`/hr/directory${q ? `?${q}` : ''}`);
    }

    // ─── Attendance Summary ────────────────────────────────────
    async getAttendanceSummary(employeeId, month = null, year = null) {
        const params = new URLSearchParams();
        if (month) params.set('month', month);
        if (year) params.set('year', year);
        const q = params.toString();
        return this.request(`/hr/attendance-summary/${employeeId}${q ? `?${q}` : ''}`);
    }

    async updateAttendance(recordId, data) {
        return this.request(`/hr/attendance/${recordId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // ─── Leave Management ──────────────────────────────────────
    async createLeaveType(data) {
        return this.request('/hr/leave-types', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getLeaveTypes() {
        return this.request('/hr/leave-types');
    }

    async updateLeaveType(leaveTypeId, data) {
        return this.request(`/hr/leave-types/${leaveTypeId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async initializeLeaveBalances(employeeId, year) {
        return this.request(`/hr/leave-balances/initialize?employee_id=${employeeId}&year=${year}`, {
            method: 'POST',
        });
    }

    async getLeaveBalances(employeeId, year = null) {
        const params = new URLSearchParams();
        if (year) params.set('year', year);
        const q = params.toString();
        return this.request(`/hr/leave-balances/${employeeId}${q ? `?${q}` : ''}`);
    }

    async createLeaveRequest(data) {
        return this.request('/hr/leave-requests', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getLeaveRequests(employeeId = null, statusFilter = null) {
        const params = new URLSearchParams();
        if (employeeId) params.set('employee_id', employeeId);
        if (statusFilter) params.set('status_filter', statusFilter);
        const q = params.toString();
        return this.request(`/hr/leave-requests${q ? `?${q}` : ''}`);
    }

    async reviewLeaveRequest(requestId, data) {
        return this.request(`/hr/leave-requests/${requestId}/review`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async cancelLeaveRequest(requestId) {
        return this.request(`/hr/leave-requests/${requestId}/cancel`, {
            method: 'PUT',
        });
    }

    // ─── Staff Self-Service ────────────────────────────────────
    async getMyEmployeeProfile() {
        return this.request('/hr/my-profile');
    }
}

const api = new ApiService();
export default api;
