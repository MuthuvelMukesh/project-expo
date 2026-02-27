import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import FacultyConsole from './pages/FacultyConsole';
import AdminPanel from './pages/AdminPanel';
import CopilotPanel from './pages/CopilotPanel';
import GovernanceDashboard from './pages/GovernanceDashboard';
import UserManagement from './pages/UserManagement';
import CourseManagement from './pages/CourseManagement';
import DepartmentManagement from './pages/DepartmentManagement';
import StudentProfile from './pages/StudentProfile';
import AttendanceDetails from './pages/AttendanceDetails';
import TimetablePage from './pages/Timetable';
import FinanceManagement from './pages/FinanceManagement';
import HRManagement from './pages/HRManagement';
import StaffSelfService from './pages/StaffSelfService';

function ProtectedRoute({ children, allowedRoles }) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
                <div className="skeleton" style={{ width: 200, height: 20 }} />
            </div>
        );
    }

    if (!user) return <Navigate to="/login" replace />;
    if (allowedRoles && !allowedRoles.includes(user.role)) {
        const roleRoutes = { student: '/dashboard', faculty: '/faculty', admin: '/admin' };
        return <Navigate to={roleRoutes[user.role] || '/login'} replace />;
    }

    return children;
}

function RoleRedirect() {
    const { user, loading } = useAuth();
    if (loading) return null;
    if (!user) return <Navigate to="/login" replace />;
    const routes = { student: '/dashboard', faculty: '/faculty', admin: '/admin' };
    return <Navigate to={routes[user.role] || '/login'} replace />;
}

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={<RoleRedirect />} />
                    <Route path="/dashboard" element={<ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>} />
                    <Route path="/profile" element={<ProtectedRoute allowedRoles={['student']}><StudentProfile /></ProtectedRoute>} />
                    <Route path="/attendance" element={<ProtectedRoute allowedRoles={['student']}><AttendanceDetails /></ProtectedRoute>} />
                    <Route path="/finance" element={<ProtectedRoute allowedRoles={['student', 'admin']}><FinanceManagement /></ProtectedRoute>} />
                    <Route path="/faculty" element={<ProtectedRoute allowedRoles={['faculty']}><FacultyConsole /></ProtectedRoute>} />
                    <Route path="/timetable" element={<ProtectedRoute allowedRoles={['student', 'faculty']}><TimetablePage /></ProtectedRoute>} />
                    <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><AdminPanel /></ProtectedRoute>} />
                    <Route path="/manage-users" element={<ProtectedRoute allowedRoles={['admin']}><UserManagement /></ProtectedRoute>} />
                    <Route path="/manage-courses" element={<ProtectedRoute allowedRoles={['admin']}><CourseManagement /></ProtectedRoute>} />
                    <Route path="/manage-departments" element={<ProtectedRoute allowedRoles={['admin']}><DepartmentManagement /></ProtectedRoute>} />
                    <Route path="/hr" element={<ProtectedRoute allowedRoles={['admin']}><HRManagement /></ProtectedRoute>} />
                    <Route path="/my-portal" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><StaffSelfService /></ProtectedRoute>} />
                    <Route path="/copilot" element={<ProtectedRoute allowedRoles={['student', 'faculty', 'admin']}><CopilotPanel /></ProtectedRoute>} />
                    <Route path="/governance" element={<ProtectedRoute allowedRoles={['admin']}><GovernanceDashboard /></ProtectedRoute>} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}
