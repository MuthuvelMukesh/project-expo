import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatWidget from '../components/ChatWidget';
import api from '../services/api';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, CartesianGrid, Legend,
} from 'recharts';
import {
    Users, GraduationCap, Building2, Activity,
    AlertCircle, ShieldAlert, TrendingDown, CheckCircle2,
} from 'lucide-react';

const RISK_COLORS = { low: '#00E676', moderate: '#FFB300', high: '#FF5252' };

export default function AdminPanel() {
    const { user } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        api.getAdminDashboard()
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

    const deptChartData = data?.department_kpis?.map(d => ({
        name: d.department_code,
        attendance: d.avg_attendance,
        risk: d.high_risk_pct,
    })) || [];

    const deptPieData = data?.department_kpis?.map(d => ({
        name: d.department_code,
        value: d.total_students,
        color: ['#6C63FF', '#00D4FF', '#FF4081', '#FFB300', '#00E676'][data.department_kpis.indexOf(d) % 5],
    })) || [];

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div className="page-header animate-in">
                    <h1>Admin Panel 🏛️</h1>
                    <p>Campus-wide analytics and AI-driven insights</p>
                </div>

                {/* KPI Cards */}
                <div className="dashboard-grid grid-4 mb-lg">
                    <div className="stats-card animate-in stagger-1">
                        <div className="icon-wrapper primary"><GraduationCap size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">Total Students</div>
                            <div className="stats-value">{data?.total_students || 0}</div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-2">
                        <div className="icon-wrapper cyan"><Users size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">Total Faculty</div>
                            <div className="stats-value">{data?.total_faculty || 0}</div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-3">
                        <div className="icon-wrapper green"><Activity size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">Campus Avg Attendance</div>
                            <div className="stats-value">{data?.campus_avg_attendance || 0}%</div>
                            <div className={`stats-trend ${data?.campus_avg_attendance >= 80 ? 'up' : 'down'}`}>
                                {data?.campus_avg_attendance >= 80 ? 'Above target' : 'Below 80% target'}
                            </div>
                        </div>
                    </div>

                    <div className="stats-card animate-in stagger-4">
                        <div className="icon-wrapper red"><ShieldAlert size={22} /></div>
                        <div className="stats-info">
                            <div className="stats-label">High Risk (Campus)</div>
                            <div className="stats-value" style={{ color: RISK_COLORS.high }}>
                                {data?.campus_high_risk_pct || 0}%
                            </div>
                            <div className="stats-trend down">Students needing attention</div>
                        </div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="dashboard-grid grid-2 mb-lg">
                    {/* Department Attendance vs Risk */}
                    <div className="glass-card animate-in">
                        <div className="section-header">
                            <h2>📊 Department Attendance vs Risk</h2>
                        </div>
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={deptChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                                <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#94A3B8', fontSize: 12 }} />
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
                                <Legend wrapperStyle={{ color: '#94A3B8', fontSize: 12 }} />
                                <Bar dataKey="attendance" name="Avg Attendance %" fill="#6C63FF" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="risk" name="High Risk %" fill="#FF5252" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Student Distribution */}
                    <div className="glass-card animate-in">
                        <div className="section-header">
                            <h2>🎓 Students by Department</h2>
                        </div>
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={deptPieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    dataKey="value"
                                    label={({ name, value }) => `${name}: ${value}`}
                                    labelLine={{ stroke: '#64748B' }}
                                >
                                    {deptPieData.map((entry, i) => (
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
                </div>

                {/* Department KPI Table */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2>🏢 Department KPIs</h2>
                    </div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Department</th>
                                <th>Students</th>
                                <th>Faculty</th>
                                <th>Avg Attendance</th>
                                <th>High Risk %</th>
                                <th>Avg CGPA</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.department_kpis?.map((dept, i) => (
                                <tr key={i}>
                                    <td>
                                        <strong>{dept.department_code}</strong>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{dept.department_name}</div>
                                    </td>
                                    <td>{dept.total_students}</td>
                                    <td>{dept.total_faculty}</td>
                                    <td>
                                        <span style={{ color: dept.avg_attendance >= 80 ? '#00E676' : dept.avg_attendance >= 70 ? '#FFB300' : '#FF5252' }}>
                                            {dept.avg_attendance}%
                                        </span>
                                    </td>
                                    <td>
                                        <span style={{ color: dept.high_risk_pct > 20 ? '#FF5252' : dept.high_risk_pct > 10 ? '#FFB300' : '#00E676' }}>
                                            {dept.high_risk_pct}%
                                        </span>
                                    </td>
                                    <td>{dept.avg_cgpa}</td>
                                    <td>
                                        {dept.high_risk_pct > 20 ? (
                                            <span className="risk-badge high">⚠ Needs Attention</span>
                                        ) : dept.high_risk_pct > 10 ? (
                                            <span className="risk-badge moderate">Monitor</span>
                                        ) : (
                                            <span className="risk-badge low">Healthy</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Alerts */}
                <div className="glass-card animate-in mb-lg">
                    <div className="section-header">
                        <h2>🔔 AI-Generated Alerts</h2>
                    </div>
                    {data?.recent_alerts?.map((alert, i) => (
                        <div key={i} className={`alert-card ${alert.severity}`}>
                            <div>
                                {alert.severity === 'critical' ? <AlertCircle size={20} color="#FF5252" /> :
                                    alert.severity === 'warning' ? <TrendingDown size={20} color="#FFB300" /> :
                                        <CheckCircle2 size={20} color="#00D4FF" />}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>
                                    {alert.alert_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                    {alert.message}
                                </div>
                                {alert.department && (
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                        Department: {alert.department}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </main>
            <ChatWidget />
        </div>
    );
}
