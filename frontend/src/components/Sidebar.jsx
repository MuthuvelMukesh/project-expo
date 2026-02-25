import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import {
    LayoutDashboard, BookOpen, Users, BarChart3,
    GraduationCap, Shield, LogOut, Bot, CalendarCheck, Terminal,
    User, Building2, CalendarDays, Download, DollarSign, Briefcase
} from 'lucide-react';
import NotificationBell from './NotificationBell';
import ThemeToggle from './ThemeToggle';
import api from '../services/api';

const navConfig = {
    student: [
        { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { to: '/timetable', icon: CalendarCheck, label: 'Timetable' },
        { to: '/profile', icon: User, label: 'My Profile' },
        { to: '/attendance', icon: CalendarDays, label: 'Attendance' },
        { to: '/finance', icon: DollarSign, label: 'Fees & Payments' },
        { to: '/copilot', icon: Terminal, label: 'Command Console' },
    ],
    faculty: [
        { to: '/faculty', icon: BookOpen, label: 'My Classes' },
        { to: '/timetable', icon: CalendarCheck, label: 'Timetable' },
        { to: '/copilot', icon: Terminal, label: 'Command Console' },
    ],
    admin: [
        { to: '/admin', icon: Shield, label: 'Admin Panel' },
        { to: '/manage-users', icon: Users, label: 'Users' },
        { to: '/manage-courses', icon: BookOpen, label: 'Courses' },
        { to: '/manage-departments', icon: Building2, label: 'Departments' },
        { to: '/finance', icon: DollarSign, label: 'Finance' },
        { to: '/hr', icon: Briefcase, label: 'HR & Payroll' },
        { to: '/copilot', icon: Terminal, label: 'Command Console' },
        { to: '/governance', icon: Shield, label: 'Governance', badge: true },
    ],
};

export default function Sidebar() {
    const { user, logout } = useAuth();
    const location = useLocation();
    const [pendingCount, setPendingCount] = useState(0);

    // Poll pending approvals count for admins
    useEffect(() => {
        if (user?.role !== 'admin') return;

        const fetchCount = async () => {
            try {
                const data = await api.getPendingApprovals();
                setPendingCount(Array.isArray(data) ? data.length : 0);
            } catch {
                /* ignore */
            }
        };

        fetchCount();
        const interval = setInterval(fetchCount, 30000);
        return () => clearInterval(interval);
    }, [user?.role]);

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
                {items.map(item => {
                    const showBadge = item.badge && pendingCount > 0;
                    return (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                            style={{ position: 'relative' }}
                        >
                            <item.icon size={18} />
                            {item.label}
                            {showBadge && (
                                <span style={{
                                    marginLeft: 'auto',
                                    minWidth: 18, height: 18,
                                    borderRadius: 9,
                                    background: '#FF5252',
                                    color: '#fff',
                                    fontSize: '0.65rem',
                                    fontWeight: 800,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '0 5px',
                                    lineHeight: 1,
                                }}>
                                    {pendingCount > 99 ? '99+' : pendingCount}
                                </span>
                            )}
                        </NavLink>
                    );
                })}

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
