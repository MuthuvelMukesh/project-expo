import { useState, useEffect } from 'react';
import { Clock, MapPin, BookOpen, User, Calendar } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const DAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const HOURS = [];
for (let h = 9; h <= 17; h++) {
    HOURS.push(`${String(h).padStart(2, '0')}:00`);
}

const TYPE_COLORS = {
    lecture: { bg: 'rgba(108,99,255,0.15)', border: '#6c63ff', text: '#a5a0ff' },
    lab: { bg: 'rgba(0,212,255,0.15)', border: '#00d4ff', text: '#66e3ff' },
    tutorial: { bg: 'rgba(0,230,118,0.15)', border: '#00e676', text: '#66f0a8' },
};

function timeToMinutes(t) {
    const [h, m] = t.split(':').map(Number);
    return h * 60 + m;
}

export default function Timetable() {
    const { user } = useAuth();
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState('grid'); // grid | list

    useEffect(() => {
        (async () => {
            try {
                const data = user.role === 'student'
                    ? await api.getStudentTimetable()
                    : await api.getFacultyTimetable();
                setSlots(data);
            } catch (e) { console.error(e); }
            finally { setLoading(false); }
        })();
    }, [user.role]);

    const startMin = 9 * 60;  // 9:00 AM
    const endMin = 18 * 60;   // 6:00 PM
    const totalMin = endMin - startMin;

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="skeleton" style={{ width: 200, height: 24 }} />
                </main>
            </div>
        );
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
                    <div>
                        <h1 style={{ fontSize: '2rem', fontWeight: 800, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            <Calendar size={28} style={{ display: 'inline', marginRight: 10, verticalAlign: 'middle' }} />
                            Weekly Schedule
                        </h1>
                        <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
                            {user.role === 'student' ? 'Your enrolled course schedule' : 'Your teaching schedule'}
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: 6, background: 'var(--bg-input)', borderRadius: 8, padding: 3 }}>
                        {['grid', 'list'].map(v => (
                            <button key={v} onClick={() => setView(v)}
                                style={{
                                    padding: '6px 16px', borderRadius: 6, border: 'none', cursor: 'pointer',
                                    background: view === v ? 'var(--primary)' : 'transparent',
                                    color: view === v ? 'white' : 'var(--text-secondary)',
                                    fontWeight: 600, fontSize: '0.8rem', fontFamily: 'var(--font-sans)',
                                    transition: 'all 0.15s',
                                }}>
                                {v === 'grid' ? '📊 Grid' : '📋 List'}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Legend */}
                <div style={{ display: 'flex', gap: 20, marginBottom: 20, flexWrap: 'wrap' }}>
                    {Object.entries(TYPE_COLORS).map(([type, c]) => (
                        <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 12, height: 12, borderRadius: 3, background: c.border }} />
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{type}</span>
                        </div>
                    ))}
                    <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {slots.length} classes/week
                    </span>
                </div>

                {slots.length === 0 ? (
                    <div className="card" style={{ padding: 48, textAlign: 'center' }}>
                        <Calendar size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
                        <h3 style={{ color: 'var(--text-secondary)' }}>No schedule found</h3>
                        <p style={{ color: 'var(--text-muted)', marginTop: 6 }}>Schedule entries haven't been created yet.</p>
                    </div>
                ) : view === 'grid' ? (
                    /* ── GRID VIEW ── */
                    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 16, overflow: 'hidden' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '70px repeat(6, 1fr)', minHeight: 540 }}>
                            {/* Day headers */}
                            <div style={{ padding: 12, background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', borderRight: '1px solid var(--border)' }} />
                            {DAYS.map((d, i) => (
                                <div key={d} style={{
                                    padding: '10px 8px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)',
                                    borderRight: i < 5 ? '1px solid var(--border)' : 'none',
                                    textAlign: 'center', fontWeight: 700, fontSize: '0.78rem', color: 'var(--text-primary)',
                                }}>
                                    <span style={{ display: 'block' }}>{DAY_SHORT[i]}</span>
                                </div>
                            ))}

                            {/* Time slots */}
                            {HOURS.map((hour, hi) => (
                                <>
                                    {/* Time label */}
                                    <div key={`t-${hour}`} style={{
                                        padding: '6px 8px', fontSize: '0.68rem', color: 'var(--text-muted)',
                                        borderRight: '1px solid var(--border)', borderBottom: '1px solid var(--border-light)',
                                        display: 'flex', alignItems: 'flex-start', justifyContent: 'center', height: 60,
                                    }}>{hour}</div>

                                    {/* Day cells */}
                                    {DAYS.map((_, di) => {
                                        const cellSlots = slots.filter(s =>
                                            s.day_of_week === di &&
                                            timeToMinutes(s.start_time) >= timeToMinutes(hour) &&
                                            timeToMinutes(s.start_time) < timeToMinutes(hour) + 60
                                        );
                                        return (
                                            <div key={`${hour}-${di}`} style={{
                                                position: 'relative', borderRight: di < 5 ? '1px solid var(--border-light)' : 'none',
                                                borderBottom: '1px solid var(--border-light)', height: 60, padding: 2,
                                            }}>
                                                {cellSlots.map(s => {
                                                    const c = TYPE_COLORS[s.class_type] || TYPE_COLORS.lecture;
                                                    return (
                                                        <div key={s.id} style={{
                                                            background: c.bg, borderLeft: `3px solid ${c.border}`,
                                                            borderRadius: 6, padding: '4px 6px', fontSize: '0.65rem',
                                                            height: '100%', overflow: 'hidden', cursor: 'default',
                                                            transition: 'transform 0.15s',
                                                        }}
                                                            title={`${s.course_name}\n${s.start_time}-${s.end_time}\n${s.room}\n${s.instructor_name}`}
                                                        >
                                                            <div style={{ fontWeight: 700, color: c.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                                {s.course_code}
                                                            </div>
                                                            <div style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                                {s.room}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        );
                                    })}
                                </>
                            ))}
                        </div>
                    </div>
                ) : (
                    /* ── LIST VIEW ── */
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {DAYS.map((day, di) => {
                            const daySlots = slots.filter(s => s.day_of_week === di).sort((a, b) => a.start_time.localeCompare(b.start_time));
                            if (daySlots.length === 0) return null;
                            return (
                                <div key={day}>
                                    <h3 style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 800 }}>
                                            {DAY_SHORT[di]}
                                        </span>
                                        {day}
                                    </h3>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingLeft: 36 }}>
                                        {daySlots.map(s => {
                                            const c = TYPE_COLORS[s.class_type] || TYPE_COLORS.lecture;
                                            return (
                                                <div key={s.id} style={{
                                                    display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px',
                                                    background: 'var(--bg-card)', border: '1px solid var(--border)',
                                                    borderLeft: `3px solid ${c.border}`, borderRadius: 10,
                                                    transition: 'transform 0.15s, box-shadow 0.15s',
                                                }}
                                                    onMouseOver={e => { e.currentTarget.style.transform = 'translateX(4px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
                                                    onMouseOut={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
                                                >
                                                    <div style={{ minWidth: 90, fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary)', fontFamily: 'monospace' }}>
                                                        {s.start_time} – {s.end_time}
                                                    </div>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                                                            {s.course_name}
                                                            <span style={{ marginLeft: 8, fontSize: '0.7rem', padding: '2px 8px', borderRadius: 4, background: c.bg, color: c.text }}>{s.class_type}</span>
                                                        </div>
                                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 3, display: 'flex', gap: 16 }}>
                                                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><BookOpen size={12} />{s.course_code}</span>
                                                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={12} />{s.room}</span>
                                                            {s.instructor_name && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><User size={12} />{s.instructor_name}</span>}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
