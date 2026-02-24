import { useState, useEffect } from 'react';
import { CalendarDays, BookOpen, CheckCircle, XCircle } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import api from '../services/api';

export default function AttendanceDetails() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedCourse, setSelectedCourse] = useState(null);

    useEffect(() => {
        (async () => {
            try {
                const d = await api.getAttendanceDetails();
                setData(d);
                if (d.courses?.length > 0) setSelectedCourse(d.courses[0].course_id);
            } catch (e) { console.error(e); }
            finally { setLoading(false); }
        })();
    }, []);

    if (loading) return <div className="app-layout"><Sidebar /><main className="main-content"><p style={{ padding: 40, color: 'var(--text-muted)' }}>Loading...</p></main></div>;

    const courses = data?.courses || [];
    const calendar = data?.calendar || [];
    const selected = courses.find(c => c.course_id === selectedCourse);

    // Build calendar grid from records
    const months = {};
    calendar.forEach(r => {
        const d = new Date(r.date);
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        if (!months[key]) months[key] = [];
        months[key].push(r);
    });

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header animate-in">
                    <h1><CalendarDays size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} /> Attendance Details</h1>
                </div>

                {/* Course Summary Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14, marginBottom: 24 }}>
                    {courses.map(c => {
                        const pctColor = c.percentage >= 75 ? '#00d278' : c.percentage >= 60 ? '#ffaa00' : '#ff4b4b';
                        return (
                            <div key={c.course_id} className="card" onClick={() => setSelectedCourse(c.course_id)}
                                style={{ padding: 18, cursor: 'pointer', border: selectedCourse === c.course_id ? '2px solid var(--primary)' : '1px solid transparent', transition: 'border 0.2s' }}>
                                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--primary)', letterSpacing: 1 }}>{c.course_code}</div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 500, marginTop: 4 }}>{c.course_name}</div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginTop: 12 }}>
                                    <div>
                                        <span style={{ fontSize: '1.5rem', fontWeight: 700, color: pctColor }}>{c.percentage}%</span>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{c.present}/{c.total} classes</div>
                                    </div>
                                    <div style={{ width: 48, height: 48, borderRadius: '50%', border: `3px solid ${pctColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        {c.percentage >= 75 ? <CheckCircle size={20} color={pctColor} /> : <XCircle size={20} color={pctColor} />}
                                    </div>
                                </div>
                                {/* Progress bar */}
                                <div style={{ height: 4, borderRadius: 2, background: 'var(--bg-secondary)', marginTop: 10, overflow: 'hidden' }}>
                                    <div style={{ height: '100%', width: `${c.percentage}%`, background: pctColor, borderRadius: 2, transition: 'width 0.5s' }} />
                                </div>
                            </div>
                        );
                    })}
                    {courses.length === 0 && <div className="card" style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', gridColumn: '1/-1' }}>No attendance records found</div>}
                </div>

                {/* Selected Course Detail */}
                {selected && (
                    <div className="card animate-in" style={{ padding: 24 }}>
                        <h3 style={{ marginBottom: 4 }}><BookOpen size={18} style={{ verticalAlign: 'middle', marginRight: 6 }} /> {selected.course_name}</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: 20 }}>{selected.course_code} — {selected.present}/{selected.total} classes attended ({selected.percentage}%)</p>

                        {/* Records table */}
                        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                                <thead><tr style={{ borderBottom: '1px solid var(--border)' }}>
                                    <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Date</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Status</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Method</th>
                                </tr></thead>
                                <tbody>
                                    {selected.records.map((r, i) => (
                                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.03))' }}>
                                            <td style={{ padding: '10px 14px' }}>{new Date(r.date).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</td>
                                            <td style={{ padding: '10px 14px' }}>
                                                <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600, background: r.is_present ? 'rgba(0,210,120,.12)' : 'rgba(255,75,75,.12)', color: r.is_present ? '#00d278' : '#ff4b4b' }}>
                                                    {r.is_present ? '✓ Present' : '✗ Absent'}
                                                </span>
                                            </td>
                                            <td style={{ padding: '10px 14px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{r.method}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Calendar Heatmap */}
                {Object.keys(months).length > 0 && (
                    <div className="card" style={{ padding: 24, marginTop: 20 }}>
                        <h3 style={{ marginBottom: 16 }}><CalendarDays size={18} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Attendance Calendar</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {calendar.slice(0, 90).map((r, i) => (
                                <div key={i} title={`${r.date} — ${r.course_code}: ${r.is_present ? 'Present' : 'Absent'}`}
                                    style={{ width: 16, height: 16, borderRadius: 3, background: r.is_present ? '#00d278' : '#ff4b4b', opacity: 0.8, cursor: 'pointer', transition: 'transform 0.15s' }}
                                    onMouseOver={e => e.target.style.transform = 'scale(1.4)'}
                                    onMouseOut={e => e.target.style.transform = 'scale(1)'} />
                            ))}
                        </div>
                        <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#00d278' }} /> Present</span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#ff4b4b' }} /> Absent</span>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
