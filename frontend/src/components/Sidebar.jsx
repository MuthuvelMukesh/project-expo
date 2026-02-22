import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard, BookOpen, Users, BarChart3,
    GraduationCap, Shield, LogOut, Bot, CalendarCheck
} from 'lucide-react';

const navConfig = {
    student: [
        { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    ],
    faculty: [
        { to: '/faculty', icon: BookOpen, label: 'My Classes' },
    ],
    admin: [
        { to: '/admin', icon: Shield, label: 'Admin Panel' },
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
