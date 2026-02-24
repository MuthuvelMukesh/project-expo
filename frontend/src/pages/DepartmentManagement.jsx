import { useState, useEffect } from 'react';
import { Building2, Plus, Edit2, Trash2, Save, X, Users, BookOpen, GraduationCap } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

export default function DepartmentManagement() {
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [editId, setEditId] = useState(null);
    const [form, setForm] = useState({ name: '', code: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const load = async () => {
        try { setLoading(true); const d = await api.listDepartments(); setDepartments(d); } catch (e) { setError(e.message); } finally { setLoading(false); }
    };
    useEffect(() => { load(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault(); setError(''); setSuccess('');
        try {
            await api.createDepartment(form);
            setSuccess('Department created!'); setShowCreate(false); setForm({ name: '', code: '' }); load();
        } catch (e) { setError(e.message); }
    };

    const handleUpdate = async (deptId) => {
        setError(''); setSuccess('');
        try {
            await api.updateDepartment(deptId, form);
            setSuccess('Department updated!'); setEditId(null); load();
        } catch (e) { setError(e.message); }
    };

    const handleDelete = async (deptId) => {
        if (!window.confirm('Delete this department? Only works if no students/faculty are linked.')) return;
        try { await api.deleteDepartment(deptId); load(); } catch (e) { setError(e.message); }
    };

    const colors = ['#6c63ff', '#00d278', '#ffaa00', '#ff4b4b', '#00bcd4', '#9c27b0', '#ff6b6b', '#4ecdc4'];

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header animate-in">
                    <div>
                        <h1><Building2 size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} /> Department Management</h1>
                        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>Manage academic departments</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)} style={{ gap: 6 }}><Plus size={18} /> Add Department</button>
                </div>

                {error && <div className="error-message" style={{ margin: '0 0 16px' }}>{error}</div>}
                {success && <div style={{ background: 'rgba(0,210,120,.12)', border: '1px solid rgba(0,210,120,.25)', color: '#00d278', padding: '10px 16px', borderRadius: 12, marginBottom: 16, fontSize: '0.85rem' }}>{success}</div>}

                {showCreate && (
                    <div className="card animate-in" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ marginBottom: 16 }}>Create New Department</h3>
                        <form onSubmit={handleCreate} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
                            <div className="form-group" style={{ flex: 2, minWidth: 200 }}><label>Department Name</label><input className="form-input" required placeholder="Computer Science" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
                            <div className="form-group" style={{ flex: 1, minWidth: 100 }}><label>Code</label><input className="form-input" required placeholder="CSE" maxLength={10} value={form.code} onChange={e => setForm({ ...form, code: e.target.value.toUpperCase() })} /></div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button type="submit" className="btn btn-primary" style={{ gap: 4 }}><Save size={16} /> Create</button>
                                <button type="button" className="btn" onClick={() => setShowCreate(false)} style={{ gap: 4 }}><X size={16} /> Cancel</button>
                            </div>
                        </form>
                    </div>
                )}

                {loading ? (
                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading departments...</div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                        {departments.map((d, i) => (
                            <div key={d.id} className="card" style={{ padding: 24, borderTop: `3px solid ${colors[i % colors.length]}` }}>
                                {editId === d.id ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                                        <input className="form-input" value={form.code} onChange={e => setForm({ ...form, code: e.target.value.toUpperCase() })} />
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <button onClick={() => handleUpdate(d.id)} className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '6px 12px', gap: 4 }}><Save size={12} /> Save</button>
                                            <button onClick={() => setEditId(null)} className="btn" style={{ fontSize: '0.75rem', padding: '6px 12px', gap: 4 }}><X size={12} /> Cancel</button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                            <div>
                                                <span style={{ fontSize: '0.65rem', fontWeight: 700, color: colors[i % colors.length], letterSpacing: 2, textTransform: 'uppercase' }}>{d.code}</span>
                                                <h3 style={{ fontSize: '1.05rem', marginTop: 4 }}>{d.name}</h3>
                                            </div>
                                            <div style={{ display: 'flex', gap: 4 }}>
                                                <button onClick={() => { setEditId(d.id); setForm({ name: d.name, code: d.code }); }} style={{ background: 'rgba(108,99,255,.1)', border: 'none', borderRadius: 6, padding: 6, cursor: 'pointer', color: 'var(--primary)' }}><Edit2 size={13} /></button>
                                                <button onClick={() => handleDelete(d.id)} style={{ background: 'rgba(255,75,75,.1)', border: 'none', borderRadius: 6, padding: 6, cursor: 'pointer', color: '#ff4b4b' }}><Trash2 size={13} /></button>
                                            </div>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 16 }}>
                                            <div style={{ textAlign: 'center', padding: 10, borderRadius: 10, background: 'var(--bg-secondary)' }}>
                                                <GraduationCap size={18} style={{ color: 'var(--accent-cyan)', marginBottom: 4 }} />
                                                <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{d.total_students}</div>
                                                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Students</div>
                                            </div>
                                            <div style={{ textAlign: 'center', padding: 10, borderRadius: 10, background: 'var(--bg-secondary)' }}>
                                                <Users size={18} style={{ color: 'var(--accent-green)', marginBottom: 4 }} />
                                                <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{d.total_faculty}</div>
                                                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Faculty</div>
                                            </div>
                                            <div style={{ textAlign: 'center', padding: 10, borderRadius: 10, background: 'var(--bg-secondary)' }}>
                                                <BookOpen size={18} style={{ color: 'var(--accent-amber)', marginBottom: 4 }} />
                                                <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{d.total_courses}</div>
                                                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Courses</div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                        {departments.length === 0 && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', gridColumn: '1/-1' }}>No departments found</div>}
                    </div>
                )}
            </main>
        </div>
    );
}
