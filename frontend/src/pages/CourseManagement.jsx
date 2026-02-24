import { useState, useEffect } from 'react';
import { BookOpen, Plus, Edit2, Trash2, Save, X } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

export default function CourseManagement() {
    const [courses, setCourses] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [faculty, setFaculty] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [editId, setEditId] = useState(null);
    const [form, setForm] = useState({ code: '', name: '', department_id: '', semester: 1, credits: 3, instructor_id: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const load = async () => {
        try {
            setLoading(true);
            const [c, d, f] = await Promise.all([
                api.listCourses(),
                api.listDepartments(),
                api.listUsers('faculty'),
            ]);
            setCourses(c); setDepartments(d); setFaculty(f);
        } catch (e) { setError(e.message); } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault(); setError(''); setSuccess('');
        try {
            await api.createCourse({ ...form, department_id: parseInt(form.department_id), semester: parseInt(form.semester), credits: parseInt(form.credits), instructor_id: form.instructor_id ? parseInt(form.instructor_id) : null });
            setSuccess('Course created!'); setShowCreate(false); setForm({ code: '', name: '', department_id: '', semester: 1, credits: 3, instructor_id: '' });
            load();
        } catch (e) { setError(e.message); }
    };

    const handleUpdate = async (courseId) => {
        setError(''); setSuccess('');
        try {
            await api.updateCourse(courseId, { ...form, department_id: parseInt(form.department_id), semester: parseInt(form.semester), credits: parseInt(form.credits), instructor_id: form.instructor_id ? parseInt(form.instructor_id) : null });
            setSuccess('Course updated!'); setEditId(null); load();
        } catch (e) { setError(e.message); }
    };

    const handleDelete = async (courseId) => {
        if (!window.confirm('Delete this course?')) return;
        try { await api.deleteCourse(courseId); load(); } catch (e) { setError(e.message); }
    };

    const startEdit = (c) => {
        setEditId(c.id);
        setForm({ code: c.code, name: c.name, department_id: c.department_id || '', semester: c.semester, credits: c.credits, instructor_id: c.instructor_id || '' });
    };

    const semColors = ['', '#6c63ff', '#00d278', '#ffaa00', '#ff4b4b', '#00bcd4', '#9c27b0', '#ff6b6b', '#4ecdc4'];

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header animate-in">
                    <div>
                        <h1><BookOpen size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} /> Course Management</h1>
                        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>Manage courses, assign instructors, and organize by department</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)} style={{ gap: 6 }}><Plus size={18} /> Add Course</button>
                </div>

                {error && <div className="error-message" style={{ margin: '0 0 16px' }}>{error}</div>}
                {success && <div style={{ background: 'rgba(0,210,120,.12)', border: '1px solid rgba(0,210,120,.25)', color: '#00d278', padding: '10px 16px', borderRadius: 12, marginBottom: 16, fontSize: '0.85rem' }}>{success}</div>}

                {showCreate && (
                    <div className="card animate-in" style={{ padding: 24, marginBottom: 20 }}>
                        <h3 style={{ marginBottom: 16 }}>Create New Course</h3>
                        <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                            <div className="form-group"><label>Course Code</label><input className="form-input" required placeholder="CS301" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} /></div>
                            <div className="form-group"><label>Course Name</label><input className="form-input" required placeholder="Database Systems" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
                            <div className="form-group"><label>Department</label>
                                <select className="form-input" required value={form.department_id} onChange={e => setForm({ ...form, department_id: e.target.value })}>
                                    <option value="">Select Department</option>
                                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                                </select>
                            </div>
                            <div className="form-group"><label>Semester</label><input className="form-input" type="number" min={1} max={8} value={form.semester} onChange={e => setForm({ ...form, semester: e.target.value })} /></div>
                            <div className="form-group"><label>Credits</label><input className="form-input" type="number" min={1} max={6} value={form.credits} onChange={e => setForm({ ...form, credits: e.target.value })} /></div>
                            <div className="form-group"><label>Instructor</label>
                                <select className="form-input" value={form.instructor_id} onChange={e => setForm({ ...form, instructor_id: e.target.value })}>
                                    <option value="">Unassigned</option>
                                    {faculty.map(f => <option key={f.id} value={f.id}>{f.full_name}</option>)}
                                </select>
                            </div>
                            <div style={{ display: 'flex', gap: 8, alignItems: 'end' }}>
                                <button type="submit" className="btn btn-primary" style={{ gap: 4 }}><Save size={16} /> Create</button>
                                <button type="button" className="btn" onClick={() => setShowCreate(false)} style={{ gap: 4 }}><X size={16} /> Cancel</button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Course Cards Grid */}
                {loading ? (
                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading courses...</div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
                        {courses.map(c => (
                            <div key={c.id} className="card" style={{ padding: 20, position: 'relative', borderLeft: `3px solid ${semColors[c.semester] || 'var(--primary)'}` }}>
                                {editId === c.id ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} style={{ fontSize: '0.85rem' }} />
                                        <select className="form-input" value={form.instructor_id} onChange={e => setForm({ ...form, instructor_id: e.target.value })} style={{ fontSize: '0.8rem' }}>
                                            <option value="">Unassigned</option>
                                            {faculty.map(f => <option key={f.id} value={f.id}>{f.full_name}</option>)}
                                        </select>
                                        <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                                            <button onClick={() => handleUpdate(c.id)} className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '6px 12px', gap: 4 }}><Save size={12} /> Save</button>
                                            <button onClick={() => setEditId(null)} className="btn" style={{ fontSize: '0.75rem', padding: '6px 12px', gap: 4 }}><X size={12} /> Cancel</button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                            <div>
                                                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: semColors[c.semester] || 'var(--primary)', letterSpacing: 1 }}>{c.code}</span>
                                                <h3 style={{ fontSize: '1rem', marginTop: 4 }}>{c.name}</h3>
                                            </div>
                                            <div style={{ display: 'flex', gap: 4 }}>
                                                <button onClick={() => startEdit(c)} style={{ background: 'rgba(108,99,255,.1)', border: 'none', borderRadius: 6, padding: 6, cursor: 'pointer', color: 'var(--primary)' }}><Edit2 size={13} /></button>
                                                <button onClick={() => handleDelete(c.id)} style={{ background: 'rgba(255,75,75,.1)', border: 'none', borderRadius: 6, padding: 6, cursor: 'pointer', color: '#ff4b4b' }}><Trash2 size={13} /></button>
                                            </div>
                                        </div>
                                        <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            <span style={{ padding: '3px 8px', borderRadius: 6, background: 'var(--bg-secondary)' }}>📚 {c.department_name}</span>
                                            <span style={{ padding: '3px 8px', borderRadius: 6, background: 'var(--bg-secondary)' }}>📅 Sem {c.semester}</span>
                                            <span style={{ padding: '3px 8px', borderRadius: 6, background: 'var(--bg-secondary)' }}>⭐ {c.credits} Credits</span>
                                        </div>
                                        <div style={{ marginTop: 10, fontSize: '0.78rem', color: c.instructor_name ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                                            👨‍🏫 {c.instructor_name || 'Unassigned'}
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                        {courses.length === 0 && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', gridColumn: '1/-1' }}>No courses found. Create the first one!</div>}
                    </div>
                )}
            </main>
        </div>
    );
}
