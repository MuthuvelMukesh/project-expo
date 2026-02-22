import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, Mail, Lock, LogIn, Sparkles } from 'lucide-react';

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const user = await login(email, password);
            const routes = { student: '/dashboard', faculty: '/faculty', admin: '/admin' };
            navigate(routes[user.role] || '/');
        } catch (err) {
            setError(err.message || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    const quickLogin = (email, password) => {
        setEmail(email);
        setPassword(password);
    };

    return (
        <div className="login-page">
            {/* Animated background orbs */}
            <div className="login-bg-orb orb-1" />
            <div className="login-bg-orb orb-2" />

            <div className="login-card animate-in">
                {/* Logo */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
                    <div
                        style={{
                            width: 64,
                            height: 64,
                            background: 'var(--gradient-primary)',
                            borderRadius: 16,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: '0 8px 30px var(--primary-glow)',
                        }}
                    >
                        <GraduationCap size={32} color="white" />
                    </div>
                </div>

                <h1>CampusIQ</h1>
                <p className="login-subtitle">
                    <Sparkles size={14} style={{ display: 'inline', verticalAlign: 'middle' }} />{' '}
                    AI-Powered Campus Intelligence
                </p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email">
                            <Mail size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            className="form-input"
                            placeholder="your.email@campusiq.edu"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">
                            <Lock size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            className="form-input"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? (
                            <>
                                <span className="skeleton" style={{ width: 16, height: 16, borderRadius: '50%' }} />
                                Signing in...
                            </>
                        ) : (
                            <>
                                <LogIn size={18} />
                                Sign In
                            </>
                        )}
                    </button>
                </form>

                {/* Demo credentials */}
                <div className="demo-creds">
                    <div style={{ marginBottom: 8 }}><strong>🎓 Demo Accounts</strong> (click to fill):</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button
                            type="button"
                            onClick={() => quickLogin('student1@campusiq.edu', 'student123')}
                            style={{
                                background: 'none', border: 'none', color: 'var(--accent-cyan)',
                                cursor: 'pointer', textAlign: 'left', padding: 0, fontFamily: 'var(--font-sans)', fontSize: '0.75rem'
                            }}
                        >
                            👨‍🎓 Student: student1@campusiq.edu / student123
                        </button>
                        <button
                            type="button"
                            onClick={() => quickLogin('faculty1@campusiq.edu', 'faculty123')}
                            style={{
                                background: 'none', border: 'none', color: 'var(--accent-green)',
                                cursor: 'pointer', textAlign: 'left', padding: 0, fontFamily: 'var(--font-sans)', fontSize: '0.75rem'
                            }}
                        >
                            👨‍🏫 Faculty: faculty1@campusiq.edu / faculty123
                        </button>
                        <button
                            type="button"
                            onClick={() => quickLogin('admin@campusiq.edu', 'admin123')}
                            style={{
                                background: 'none', border: 'none', color: 'var(--accent-amber)',
                                cursor: 'pointer', textAlign: 'left', padding: 0, fontFamily: 'var(--font-sans)', fontSize: '0.75rem'
                            }}
                        >
                            🔑 Admin: admin@campusiq.edu / admin123
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
