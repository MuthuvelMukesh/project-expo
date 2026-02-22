import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatWidget from '../components/ChatWidget';
import api from '../services/api';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, RadialBarChart, RadialBar, Legend,
    AreaChart, Area, CartesianGrid,
} from 'recharts';
import {
    Activity, TrendingUp, BookOpen, AlertTriangle,
    CheckCircle, Target, Brain, Sparkles,
} from 'lucide-react';

const RISK_COLORS = { low: '#00E676', moderate: '#FFB300', high: '#FF5252' };

export default function StudentDashboard() {
    const { user } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        api.getStudentDashboard()
            .then(setData)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header"><h1>Loading...</h1></div>
                <div className="dashboard-grid grid-4">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="stats-card"><div className="skeleton" style={{ width: '100%', height: 80 }} /></div>
                    ))}
                </div>
            </main>
        </div>
    );

    if (error) return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="error-message">{error}</div>
            </main>
        </div>
    );

    const riskAngle = data ? (data.overall_risk === 'high' ? -45 : data.overall_risk === 'moderate' ? 0 : 45) : 45;

    // Prepare chart data
    const attendanceChartData = data?.attendance_summary?.map(a => ({
        name: a.course_code,
        attendance: a.percentage,
        fill: a.status === 'safe' ? '#00E676' : a.status === 'warning' ? '#FFB300' : '#FF5252',
    })) || [];

    const predictionChartData = data?.predictions?.map(p => ({
        name: p.course_code,
        risk: Math.round(p.risk_score * 100),
        fill: RISK_COLORS[p.risk_level],
    })) || [];

    const riskDistribution = data?.predictions?.reduce((acc, p) => {
        acc[p.risk_level] = (acc[p.risk_level] || 0) + 1;
        return acc;
    }, {}) || {};

    const pieData = Object.entries(riskDistribution).map(([key, val]) => ({
        name: key.charAt(0).toUpperCase() + key.slice(1),
        value: val,
        color: RISK_COLORS[key],
    }));

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Page Header */}
                <div className="page-header animate-in">
                    <h1>Welcome, {data?.student?.full_name || user?.full_name} 👋</h1>
                    <p>Your AI-powered academic intelligence dashboard</p>
                </div>

                {/* KPI Cards */}
                <div className="dashboard-grid grid-4 mb-lg">
                    <div className="stats-card animate-in stagger-1">
                        <div className="icon-wrapper primary"><Activity size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">Overall Attendance</div>
                            <div className="stats-value">{data?.overall_attendance || 0}%</div>
                            <div className={`stats-trend ${data?.overall_attendance >= 75 ? 'up' : 'down'}`}>
                                {data?.overall_attendance >= 75 ? '✓ Above 75% threshold' : '⚠ Below 75% threshold'}
                            </div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-2">
                        <div className={`icon-wrapper ${data?.overall_risk === 'high' ? 'red' : data?.overall_risk === 'moderate' ? 'amber' : 'green'}`}>
                            <Target size={22} />
                        </div>
                        <div className="stats-info">
                            <div className="stats-label">Risk Level</div>
                            <div className="stats-value" style={{ textTransform: 'uppercase', color: RISK_COLORS[data?.overall_risk] }}>
                                {data?.overall_risk || 'Low'}
                            </div>
                            <div className="stats-trend">AI-powered assessment</div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-3">
                        <div className="icon-wrapper cyan"><BookOpen size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">Active Courses</div>
                            <div className="stats-value">{data?.attendance_summary?.length || 0}</div>
                            <div className="stats-trend">Semester {data?.student?.semester}</div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-4">
                        <div className="icon-wrapper green"><TrendingUp size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">CGPA</div>
                            <div className="stats-value">{data?.student?.cgpa || '-'}</div>
                            <div className="stats-trend">Cumulative average</div>
                        </div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="dashboard-grid grid-2 mb-lg">
                    {/* Attendance Chart */}
                    <div className="glass-card animate-in">
                        <div className="section-header">
                            <h2>📊 Attendance by Subject</h2>
                        </div>
                        <ResponsiveContainer width="100%" height={260}>
                            <BarChart data={attendanceChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                                <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ background: '#1E293B', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#F1F5F9' }}
                                />
                                <Bar dataKey="attendance" radius={[6, 6, 0, 0]}>
                                    {attendanceChartData.map((entry, i) => (
                                        <Cell key={i} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Risk Distribution */}
                    <div className="glass-card animate-in">
                        <div className="section-header">
                            <h2>🎯 Risk Distribution</h2>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ResponsiveContainer width="100%" height={260}>
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        dataKey="value"
                                        label={({ name, value }) => `${name}: ${value}`}
                                        labelLine={{ stroke: '#64748B' }}
                                    >
                                        {pieData.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ background: '#1E293B', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#F1F5F9' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Attendance Bars */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2>📅 Attendance Progress</h2>
                    </div>
                    {data?.attendance_summary?.map((att, i) => (
                        <div key={i} className="attendance-bar-wrapper">
                            <div className="attendance-bar-header">
                                <span className="course-name">{att.course_name}</span>
                                <span className={`percentage ${att.status}`}>
                                    {att.percentage}%
                                    {att.status === 'danger' && ` (need ${att.classes_needed_for_75} more)`}
                                </span>
                            </div>
                            <div className="attendance-bar-track">
                                <div className={`attendance-bar-fill ${att.status}`} style={{ width: `${att.percentage}%` }} />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Predictions Table */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2>🔮 AI Grade Predictions</h2>
                        <span className="risk-badge low" style={{ fontSize: '0.7rem' }}>
                            <Brain size={12} /> Powered by XGBoost
                        </span>
                    </div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Course</th>
                                <th>Predicted Grade</th>
                                <th>Risk Score</th>
                                <th>Risk Level</th>
                                <th>Confidence</th>
                                <th>Top Factor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.predictions?.map((pred, i) => (
                                <tr key={i}>
                                    <td>
                                        <strong>{pred.course_code}</strong>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{pred.course_name}</div>
                                    </td>
                                    <td>
                                        <span style={{
                                            fontSize: '1.25rem', fontWeight: 700,
                                            color: ['A+', 'A'].includes(pred.predicted_grade) ? '#00E676' :
                                                ['B+', 'B'].includes(pred.predicted_grade) ? '#FFB300' : '#FF5252'
                                        }}>
                                            {pred.predicted_grade}
                                        </span>
                                    </td>
                                    <td>{Math.round(pred.risk_score * 100)}%</td>
                                    <td><span className={`risk-badge ${pred.risk_level}`}>{pred.risk_level}</span></td>
                                    <td>{Math.round(pred.confidence * 100)}%</td>
                                    <td>
                                        {pred.top_factors?.[0] && (
                                            <span style={{ fontSize: '0.8rem' }}>
                                                {pred.top_factors[0].factor}: {pred.top_factors[0].value}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* AI Recommendations */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2><Sparkles size={20} style={{ display: 'inline', verticalAlign: 'middle' }} /> AI Recommendations</h2>
                    </div>
                    {data?.ai_recommendations?.map((rec, i) => (
                        <div key={i} className="recommendation-card">{rec}</div>
                    ))}
                </div>
            </main>

            <ChatWidget />
        </div>
    );
}
