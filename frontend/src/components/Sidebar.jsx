import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard, BookOpen, Users, BarChart3,
    GraduationCap, Shield, LogOut, Bot, CalendarCheck, Sparkles,
    User, Building2, CalendarDays, Download, DollarSign, Briefcase
} from 'lucide-react';
import NotificationBell from './NotificationBell';
import ThemeToggle from './ThemeToggle';

const navConfig = {
    student: [
        { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { to: '/timetable', icon: CalendarCheck, label: 'Timetable' },
        { to: '/profile', icon: User, label: 'My Profile' },
        { to: '/attendance', icon: CalendarDays, label: 'Attendance' },
        { to: '/finance', icon: DollarSign, label: 'Fees & Payments' },
        { to: '/copilot', icon: Sparkles, label: 'AI Copilot' },
    ],
    faculty: [
        { to: '/faculty', icon: BookOpen, label: 'My Classes' },
        { to: '/timetable', icon: CalendarCheck, label: 'Timetable' },
        { to: '/copilot', icon: Sparkles, label: 'AI Copilot' },
    ],
    admin: [
        { to: '/admin', icon: Shield, label: 'Admin Panel' },
        { to: '/manage-users', icon: Users, label: 'Users' },
        { to: '/manage-courses', icon: BookOpen, label: 'Courses' },
        { to: '/manage-departments', icon: Building2, label: 'Departments' },
        { to: '/finance', icon: DollarSign, label: 'Finance' },
        { to: '/hr', icon: Briefcase, label: 'HR & Payroll' },
        { to: '/copilot', icon: Sparkles, label: 'AI Copilot' },
    ],
};

export default function Sidebar() {
    const { user, logout } = useAuth();
    const location = useLocation();

    if (!user) return null;

    const items = navConfig[user.role] || [];
    const initials = user.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || '?';

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="logo-icon">
                    <GraduationCap size={22} />
                </div>
                <h2>CampusIQ</h2>
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <ThemeToggle />
                    <NotificationBell />
                </div>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <span className="nav-section-label">Navigation</span>
                {items.map(item => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        <item.icon size={18} />
                        {item.label}
                    </NavLink>
                ))}

                <span className="nav-section-label" style={{ marginTop: 'auto', paddingTop: 32 }}>
                    Quick Info
                </span>
                <div className="nav-item" style={{ cursor: 'default', opacity: 0.7 }}>
                    <Bot size={18} />
                    AI Chatbot (Bottom Right)
                </div>
            </nav>

            {/* User Footer */}
            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">{initials}</div>
                    <div className="user-details">
                        <div className="user-name">{user.full_name}</div>
                        <div className="user-role">{user.role}</div>
                    </div>
                    <button
                        onClick={logout}
                        className="nav-item"
                        style={{ width: 'auto', padding: 8 }}
                        title="Logout"
                    >
                        <LogOut size={16} />
                    </button>
                </div>
            </div>
        </aside>
    );
}
