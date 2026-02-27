import { useState, useEffect } from 'react';
import { User, Mail, GraduationCap, Building2, Calendar, Award, Save, Lock, Eye, EyeOff } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

export default function StudentProfile() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [form, setForm] = useState({});
    const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' });
    const [showPw, setShowPw] = useState(false);
    const [pwMsg, setPwMsg] = useState({ text: '', type: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        (async () => {
            try {
                const p = await api.getStudentProfile();
                setProfile(p);
                setForm({ full_name: p.full_name, section: p.section });
            } catch (e) { setError(e.message); }
            finally { setLoading(false); }
        })();
    }, []);

    const handleSave = async () => {
        setError('');
        setSuccess('');
        try {
            await api.updateStudentProfile(form);
            setSuccess('Profile updated!');
            setEditing(false);
            const p = await api.getStudentProfile();
            setProfile(p);
        } catch (e) { setError(e.message); }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        setPwMsg({ text: '', type: '' });
        if (pwForm.new_password !== pwForm.confirm) {
            setPwMsg({ text: 'Passwords do not match', type: 'error' });
            return;
        }
        try {
            await api.changePassword(pwForm.old_password, pwForm.new_password);
            setPwMsg({ text: 'Password changed!', type: 'success' });
            setPwForm({ old_password: '', new_password: '', confirm: '' });
        } catch (e) { setPwMsg({ text: e.message, type: 'error' }); }
    };

    if (loading) return (
        <div className="app-layout"><Sidebar />
            <main className="main-content">
                <p style={{ padding: 40, color: 'var(--text-muted)' }}>Loading profile...</p>
            </main>
        </div>
    );

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header animate-in">
                    <h1><User size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} /> My Profile</h1>
                </div>

                {error && <div className="error-message" style={{ marginBottom: 16 }}>{error}</div>}
                {success && <div style={{ background: 'rgba(0,210,120,.12)', border: '1px solid rgba(0,210,120,.25)', color: '#00d278', padding: '10px 16px', borderRadius: 12, marginBottom: 16, fontSize: '0.85rem' }}>{success}</div>}

                {profile && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
                        {/* Profile Card */}
                        <div className="card animate-in" style={{ padding: 28 }}>
                            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                                <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', fontSize: 32, fontWeight: 700, color: 'white' }}>
                                    {profile.full_name?.charAt(0)?.toUpperCase()}
                                </div>
                                {editing
                                    ? <input className="form-input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} style={{ textAlign: 'center', fontSize: '1.1rem' }} />
                                    : <h2 style={{ fontSize: '1.2rem' }}>{profile.full_name}</h2>
                                }
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: 4 }}>{profile.roll_number}</p>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <InfoRow icon={<Mail size={18} style={{ color: 'var(--primary)' }} />} label="Email" value={profile.email} />
                                <InfoRow icon={<Building2 size={18} style={{ color: 'var(--accent-green)' }} />} label="Department" value={profile.department_name} />
                                <InfoRow icon={<Calendar size={18} style={{ color: 'var(--accent-cyan)' }} />} label="Semester" value={`Semester ${profile.semester}`} />
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <GraduationCap size={18} style={{ color: 'var(--accent-amber)' }} />
                                    <div>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Section</div>
                                        {editing
                                            ? <input className="form-input" value={form.section} onChange={e => setForm({ ...form, section: e.target.value })} style={{ padding: '4px 8px', fontSize: '0.85rem' }} />
                                            : <div style={{ fontSize: '0.9rem' }}>Section {profile.section}</div>
                                        }
                                    </div>
                                </div>
                                <InfoRow icon={<Award size={18} style={{ color: '#ffaa00' }} />} label="CGPA" value={profile.cgpa?.toFixed(2)} bold />
                            </div>
                            <div style={{ marginTop: 20, display: 'flex', gap: 8 }}>
                                {editing ? (<>
                                    <button className="btn btn-primary" onClick={handleSave} style={{ flex: 1, gap: 6 }}><Save size={16} /> Save</button>
                                    <button className="btn" onClick={() => setEditing(false)} style={{ flex: 1 }}>Cancel</button>
                                </>) : (
                                    <button className="btn btn-primary" onClick={() => setEditing(true)} style={{ width: '100%' }}>Edit Profile</button>
                                )}
                            </div>
                        </div>

                        {/* Change Password */}
                        <div className="card animate-in" style={{ padding: 28 }}>
                            <h3 style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}><Lock size={20} /> Change Password</h3>
                            {pwMsg.text && <div style={{ padding: '10px 16px', borderRadius: 10, marginBottom: 16, fontSize: '0.85rem', background: pwMsg.type === 'success' ? 'rgba(0,210,120,.12)' : 'rgba(255,75,75,.12)', color: pwMsg.type === 'success' ? '#00d278' : '#ff4b4b' }}>{pwMsg.text}</div>}
                            <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <div className="form-group"><label>Current Password</label><input className="form-input" type={showPw ? 'text' : 'password'} required value={pwForm.old_password} onChange={e => setPwForm({ ...pwForm, old_password: e.target.value })} /></div>
                                <div className="form-group"><label>New Password</label><input className="form-input" type={showPw ? 'text' : 'password'} required minLength={6} value={pwForm.new_password} onChange={e => setPwForm({ ...pwForm, new_password: e.target.value })} /></div>
                                <div className="form-group"><label>Confirm Password</label><input className="form-input" type={showPw ? 'text' : 'password'} required value={pwForm.confirm} onChange={e => setPwForm({ ...pwForm, confirm: e.target.value })} /></div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                                    {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                                    <input type="checkbox" checked={showPw} onChange={e => setShowPw(e.target.checked)} style={{ display: 'none' }} />
                                    {showPw ? 'Hide' : 'Show'} passwords
                                </label>
                                <button type="submit" className="btn btn-primary" style={{ gap: 6 }}><Lock size={16} /> Change Password</button>
                            </form>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

function InfoRow({ icon, label, value, bold }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {icon}
            <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{label}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: bold ? 600 : 400 }}>{value}</div>
            </div>
        </div>
    );
}
