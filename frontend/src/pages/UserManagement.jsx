import { useState, useEffect } from 'react';
import { Users, Plus, Edit2, Trash2, Search, Filter, X, Check, Save } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

export default function UserManagement() {
    const [users, setUsers] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterRole, setFilterRole] = useState('');
    const [search, setSearch] = useState('');
    const [showCreate, setShowCreate] = useState(false);
    const [editId, setEditId] = useState(null);
    const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'student', department_id: '', semester: 1, section: 'A', designation: 'Assistant Professor' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const load = async () => {
        try {
            setLoading(true);
            const [u, d] = await Promise.all([api.listUsers(filterRole || null), api.listDepartments()]);
            setUsers(u);
            setDepartments(d);
        } catch (e) { setError(e.message); } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [filterRole]);

    const filtered = users.filter(u =>
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        (u.roll_number || '').toLowerCase().includes(search.toLowerCase())
    );

    const handleCreate = async (e) => {
        e.preventDefault(); setError(''); setSuccess('');
        try {
            await api.createUser({ ...form, department_id: form.department_id ? parseInt(form.department_id) : 1 });
            setSuccess('User created!'); setShowCreate(false); setForm({ email: '', password: '', full_name: '', role: 'student', department_id: '', semester: 1, section: 'A', designation: 'Assistant Professor' });
            load();
        } catch (e) { setError(e.message); }
    };

    const handleUpdate = async (userId) => {
        setError(''); setSuccess('');
        try {
            await api.updateUser(userId, form);
            setSuccess('User updated!'); setEditId(null); load();
        } catch (e) { setError(e.message); }
    };

    const handleToggle = async (userId) => {
        try { await api.toggleUserActive(userId); load(); } catch (e) { setError(e.message); }
    };

    const startEdit = (u) => {
        setEditId(u.id);
        setForm({ full_name: u.full_name, is_active: u.is_active, department_id: u.department_id || '', semester: u.semester || 1, section: u.section || 'A', designation: u.designation || '' });
    };

    const roleColors = { student: 'var(--accent-cyan)', faculty: 'var(--accent-green)', admin: 'var(--accent-amber)' };
    const roleIcons = { student: '👨‍🎓', faculty: '👨‍🏫', admin: '🔑' };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header animate-in">
                    <div>
                        <h1><Users size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} /> User Management</h1>
                        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>Create, edit, and manage all users across the platform</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)} style={{ gap: 6 }}>
                        <Plus size={18} /> Add User
                    </button>
                </div>

                {error && <div className="error-message" style={{ margin: '0 0 16px' }}>{error}</div>}
                {success && <div style={{ background: 'rgba(0,210,120,.12)', border: '1px solid rgba(0,210,120,.25)', color: '#00d278', padding: '10px 16px', borderRadius: 12, marginBottom: 16, fontSize: '0.85rem' }}>{success}</div>}

                {/* Filters */}
                <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                    <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
                        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input className="form-input" placeholder="Search by name, email, or roll number..." value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 36 }} />
                    </div>
                    {['', 'student', 'faculty', 'admin'].map(r => (
                        <button key={r} onClick={() => setFilterRole(r)}
                            style={{ padding: '8px 16px', borderRadius: 8, border: filterRole === r ? '2px solid var(--primary)' : '1px solid var(--border)', background: filterRole === r ? 'rgba(108,99,255,.15)' : 'var(--card-bg)', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 500 }}>
                            {r ? `${roleIcons[r]} ${r.charAt(0).toUpperCase() + r.slice(1)}` : '📋 All'}
                        </button>
                    ))}
                </div>

                {/* Create Form */}
                {showCreate && (
                    <div className="card animate-in" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ marginBottom: 16 }}>Create New User</h3>
                        <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                            <div className="form-group"><label>Full Name</label><input className="form-input" required value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} /></div>
                            <div className="form-group"><label>Email</label><input className="form-input" type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></div>
                            <div className="form-group"><label>Password</label><input className="form-input" type="password" required minLength={6} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></div>
                            <div className="form-group"><label>Role</label>
                                <select className="form-input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                                    <option value="student">Student</option><option value="faculty">Faculty</option><option value="admin">Admin</option>
                                </select>
                            </div>
                            <div className="form-group"><label>Department</label>
                                <select className="form-input" value={form.department_id} onChange={e => setForm({ ...form, department_id: e.target.value })}>
                                    <option value="">Default</option>
                                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                                </select>
                            </div>
                            {form.role === 'student' && <>
                                <div className="form-group"><label>Semester</label><input className="form-input" type="number" min={1} max={8} value={form.semester} onChange={e => setForm({ ...form, semester: parseInt(e.target.value) })} /></div>
                                <div className="form-group"><label>Section</label><input className="form-input" value={form.section} onChange={e => setForm({ ...form, section: e.target.value })} /></div>
                            </>}
                            {form.role === 'faculty' && <div className="form-group"><label>Designation</label><input className="form-input" value={form.designation} onChange={e => setForm({ ...form, designation: e.target.value })} /></div>}
                            <div style={{ display: 'flex', gap: 8, alignItems: 'end' }}>
                                <button type="submit" className="btn btn-primary" style={{ gap: 4 }}><Save size={16} /> Create</button>
                                <button type="button" className="btn" onClick={() => setShowCreate(false)} style={{ gap: 4 }}><X size={16} /> Cancel</button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Users Table */}
                <div className="card" style={{ overflow: 'auto' }}>
                    {loading ? (
                        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading users...</div>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                    {['Name', 'Email', 'Role', 'Department', 'Details', 'Status', 'Actions'].map(h => (
                                        <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600 }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(u => (
                                    <tr key={u.id} style={{ borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.04))' }}>
                                        <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                                            {editId === u.id ? <input className="form-input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} style={{ fontSize: '0.8rem', padding: '4px 8px' }} /> : u.full_name}
                                        </td>
                                        <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{u.email}</td>
                                        <td style={{ padding: '12px 16px' }}><span style={{ padding: '4px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600, background: `${roleColors[u.role]}20`, color: roleColors[u.role] }}>{roleIcons[u.role]} {u.role}</span></td>
                                        <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{u.department_name || '—'}</td>
                                        <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                                            {u.roll_number && <span>🎫 {u.roll_number}</span>}
                                            {u.employee_id && <span>🆔 {u.employee_id}</span>}
                                            {u.designation && <span style={{ marginLeft: 6 }}>{u.designation}</span>}
                                            {u.semester && <span style={{ marginLeft: 6 }}>Sem {u.semester}</span>}
                                        </td>
                                        <td style={{ padding: '12px 16px' }}>
                                            <span style={{ padding: '4px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600, background: u.is_active ? 'rgba(0,210,120,.12)' : 'rgba(255,75,75,.12)', color: u.is_active ? '#00d278' : '#ff4b4b' }}>
                                                {u.is_active ? '● Active' : '● Inactive'}
                                            </span>
                                        </td>
                                        <td style={{ padding: '12px 16px' }}>
                                            <div style={{ display: 'flex', gap: 6 }}>
                                                {editId === u.id ? (
                                                    <>
                                                        <button onClick={() => handleUpdate(u.id)} style={{ background: 'rgba(0,210,120,.15)', border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer', color: '#00d278' }}><Check size={14} /></button>
                                                        <button onClick={() => setEditId(null)} style={{ background: 'rgba(255,75,75,.15)', border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer', color: '#ff4b4b' }}><X size={14} /></button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button onClick={() => startEdit(u)} style={{ background: 'rgba(108,99,255,.12)', border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer', color: 'var(--primary)' }}><Edit2 size={14} /></button>
                                                        <button onClick={() => handleToggle(u.id)} style={{ background: 'rgba(255,170,0,.12)', border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer', color: 'var(--accent-amber)' }}><Trash2 size={14} /></button>
                                                    </>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {filtered.length === 0 && <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>No users found</td></tr>}
                            </tbody>
                        </table>
                    )}
                </div>

                <div style={{ marginTop: 16, color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                    Total: {filtered.length} users {filterRole && `(${filterRole})`}
                </div>
            </main>
        </div>
    );
}
