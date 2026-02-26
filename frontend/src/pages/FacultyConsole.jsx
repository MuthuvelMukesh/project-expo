import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatWidget from '../components/ChatWidget';
import api from '../services/api';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, CartesianGrid,
} from 'recharts';
import {
    BookOpen, Users, AlertTriangle, QrCode,
    Eye, RefreshCw, ArrowRight,
} from 'lucide-react';

const RISK_COLORS = { low: '#00E676', moderate: '#FFB300', high: '#FF5252' };

export default function FacultyConsole() {
    const { user } = useAuth();
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [riskRoster, setRiskRoster] = useState(null);
    const [qrData, setQrData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [rosterLoading, setRosterLoading] = useState(false);
    const [qrLoading, setQrLoading] = useState(false);

    useEffect(() => {
        api.getMyCourses()
            .then(data => {
                setCourses(data);
                if (data.length > 0) setSelectedCourse(data[0]);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        if (selectedCourse) {
            setRosterLoading(true);
            api.getRiskRoster(selectedCourse.id)
                .then(setRiskRoster)
                .catch(console.error)
                .finally(() => setRosterLoading(false));
        }
    }, [selectedCourse]);

    const handleGenerateQR = async () => {
        if (!selectedCourse) return;
        setQrLoading(true);
        try {
            const data = await api.generateQR(selectedCourse.id);
            setQrData(data);
            // Auto-expire after 90 seconds
            setTimeout(() => setQrData(null), 90000);
        } catch (err) {
            console.error(err);
        } finally {
            setQrLoading(false);
        }
    };

    const pieData = riskRoster ? [
        { name: 'Low', value: riskRoster.risk_distribution?.low || 0, color: RISK_COLORS.low },
        { name: 'Moderate', value: riskRoster.risk_distribution?.moderate || 0, color: RISK_COLORS.moderate },
        { name: 'High', value: riskRoster.risk_distribution?.high || 0, color: RISK_COLORS.high },
    ].filter(d => d.value > 0) : [];

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div className="page-header animate-in">
                    <h1>Faculty Console 👨‍🏫</h1>
                    <p>Class analytics, risk roster, and smart attendance</p>
                </div>

                {/* Course Selector */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2><BookOpen size={20} style={{ display: 'inline', verticalAlign: 'middle' }} /> My Courses</h2>
                        <button className="btn btn-primary btn-sm" onClick={handleGenerateQR} disabled={qrLoading || !selectedCourse}>
                            <QrCode size={14} />
                            {qrLoading ? 'Generating...' : 'Generate QR Attendance'}
                        </button>
                    </div>

                    {loading ? (
                        <div className="skeleton" style={{ width: '100%', height: 40 }} />
                    ) : (
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {courses.map(course => (
                                <button
                                    key={course.id}
                                    onClick={() => setSelectedCourse(course)}
                                    className={`btn ${selectedCourse?.id === course.id ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                                >
                                    {course.code} — {course.name}
                                </button>
                            ))}
                            {courses.length === 0 && (
                                <p className="text-muted">No courses assigned yet.</p>
                            )}
                        </div>
                    )}
                </div>

                {/* QR Code Display */}
                {qrData && (
                    <div className="glass-card animate-in mb-lg" style={{ textAlign: 'center' }}>
                        <div className="section-header">
                            <h2>📱 Scan QR to Mark Attendance</h2>
                            <span className="risk-badge moderate">Expires in 90 seconds</span>
                        </div>
                        <img
                            src={`data:image/png;base64,${qrData.qr_image_base64}`}
                            alt="Attendance QR Code"
                            style={{ width: 250, height: 250, borderRadius: 12, margin: '0 auto', display: 'block' }}
                        />
                        <p className="text-secondary mt-md">{qrData.course_name}</p>
                    </div>
                )}

                {/* Analytics Row */}
                {riskRoster && (
                    <>
                        <div className="dashboard-grid grid-3 mb-lg">
                            <div className="stats-card animate-in stagger-1">
                                <div className="icon-wrapper primary"><Users size={22} /></div>
                                <div className="stats-info">
                                    <div className="stats-label">Total Students</div>
                                    <div className="stats-value">{riskRoster.total_students}</div>
                                </div>
                            </div>

                            <div className="stats-card animate-in stagger-2">
                                <div className="icon-wrapper red"><AlertTriangle size={22} /></div>
                                <div className="stats-info">
                                    <div className="stats-label">High Risk</div>
                                    <div className="stats-value" style={{ color: RISK_COLORS.high }}>
                                        {riskRoster.risk_distribution?.high || 0}
                                    </div>
                                    <div className="stats-trend down">Need immediate attention</div>
                                </div>
                            </div>

                            <div className="stats-card animate-in stagger-3">
                                <div className="icon-wrapper green">
                                    <span style={{ fontSize: 18, fontWeight: 700 }}>
                                        {riskRoster.risk_distribution?.low || 0}
                                    </span>
                                </div>
                                <div className="stats-info">
                                    <div className="stats-label">Low Risk</div>
                                    <div className="stats-value" style={{ color: RISK_COLORS.low }}>
                                        {Math.round(((riskRoster.risk_distribution?.low || 0) / Math.max(riskRoster.total_students, 1)) * 100)}%
                                    </div>
                                    <div className="stats-trend up">Performing well</div>
                                </div>
                            </div>
                        </div>

                        {/* Charts */}
                        <div className="dashboard-grid grid-2 mb-lg">
                            <div className="glass-card animate-in">
                                <div className="section-header">
                                    <h2>🎯 Risk Distribution</h2>
                                </div>
                                <ResponsiveContainer width="100%" height={250}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={50}
                                            outerRadius={90}
                                            dataKey="value"
                                            label={({ name, value }) => `${name}: ${value}`}
                                            labelLine={{ stroke: '#64748B' }}
                                        >
                                            {pieData.map((entry, i) => (
                                                <Cell key={i} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip 
                                            contentStyle={{ 
                                                backgroundColor: 'var(--bg-elevated)', 
                                                border: '1px solid var(--border-color)', 
                                                borderRadius: 8, 
                                                color: 'var(--text-primary)',
                                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                            }}
                                            labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="glass-card animate-in">
                                <div className="section-header">
                                    <h2>📊 Risk Scores</h2>
                                </div>
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={riskRoster.students?.slice(0, 10)?.map(s => ({
                                        name: s.roll_number,
                                        risk: Math.round(s.risk_score * 100),
                                        fill: RISK_COLORS[s.risk_level],
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                        <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 10 }} angle={-30} textAnchor="end" height={50} />
                                        <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 12 }} />
                                        <Tooltip 
                                            contentStyle={{ 
                                                backgroundColor: 'var(--bg-elevated)', 
                                                border: '1px solid var(--border-color)', 
                                                borderRadius: 8, 
                                                color: 'var(--text-primary)',
                                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                            }}
                                            labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
                                        />
                                        <Bar dataKey="risk" radius={[6, 6, 0, 0]}>
                                            {riskRoster.students?.slice(0, 10)?.map((s, i) => (
                                                <Cell key={i} fill={RISK_COLORS[s.risk_level]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Risk Roster Table */}
                        <div className="glass-card animate-in mb-lg">
                            <div className="section-header">
                                <h2>🔴 Student Risk Roster — {riskRoster.course_name}</h2>
                            </div>
                            {rosterLoading ? (
                                <div className="skeleton" style={{ width: '100%', height: 200 }} />
                            ) : (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Roll No</th>
                                            <th>Student Name</th>
                                            <th>Attendance</th>
                                            <th>Predicted Grade</th>
                                            <th>Risk Score</th>
                                            <th>Risk Level</th>
                                            <th>Top Factor</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {riskRoster.students?.map((s, i) => (
                                            <tr key={i}>
                                                <td><strong>{s.roll_number}</strong></td>
                                                <td>{s.student_name}</td>
                                                <td>
                                                    <span style={{ color: s.attendance_pct >= 75 ? '#00E676' : s.attendance_pct >= 65 ? '#FFB300' : '#FF5252' }}>
                                                        {s.attendance_pct}%
                                                    </span>
                                                </td>
                                                <td>
                                                    <span style={{
                                                        fontWeight: 700,
                                                        color: ['A+', 'A'].includes(s.predicted_grade) ? '#00E676' :
                                                            ['B+', 'B'].includes(s.predicted_grade) ? '#FFB300' : '#FF5252'
                                                    }}>
                                                        {s.predicted_grade}
                                                    </span>
                                                </td>
                                                <td>{Math.round(s.risk_score * 100)}%</td>
                                                <td><span className={`risk-badge ${s.risk_level}`}>{s.risk_level}</span></td>
                                                <td style={{ fontSize: '0.8rem' }}>
                                                    {s.top_factors?.[0]?.factor}: {s.top_factors?.[0]?.value}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </>
                )}
            </main>
            <ChatWidget />
        </div>
    );
}
