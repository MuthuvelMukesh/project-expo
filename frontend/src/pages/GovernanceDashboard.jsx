/**
 * CampusIQ — Governance Dashboard (Admin Only)
 * Operational AI oversight: pending approvals, system stats, full audit trail.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import api from '../services/api';
import {
    Shield, CheckCircle, XCircle, AlertTriangle, Clock,
    BarChart3, Activity, RefreshCw, Filter, Loader,
    ChevronDown, ChevronUp, Terminal, Eye, TrendingUp,
    Users, Database, FileText, Info, ArrowRight
} from 'lucide-react';

// ─── Constants ────────────────────────────────────────────────────────────────

const RISK_CONFIG = {
    LOW: { color: '#00E676', bg: 'rgba(0,230,118,0.12)', label: 'Low' },
    MEDIUM: { color: '#FFB300', bg: 'rgba(255,179,0,0.12)', label: 'Medium' },
    HIGH: { color: '#FF5252', bg: 'rgba(255,82,82,0.12)', label: 'High' },
};

const INTENT_COLORS = {
    READ: '#64B5F6', ANALYZE: '#CE93D8', CREATE: '#A5D6A7',
    UPDATE: '#FFE082', DELETE: '#EF9A9A', ESCALATE: '#FF8A65',
};

const EVT_COLOR = {
    executed: '#00E676', failed: '#FF5252', rollback: '#FFB300',
    approved: '#A5D6A7', rejected: '#EF9A9A', escalated: '#FF8A65',
};

// ─── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({ label, value, subtitle, color, icon: Icon, pulse }) {
    return (
        <div style={{
            flex: '1 1 180px', padding: '18px 20px', borderRadius: 14,
            background: 'rgba(15,23,42,0.6)',
            border: `1px solid ${color}22`,
            position: 'relative', overflow: 'hidden',
        }}>
            {pulse && value > 0 && (
                <div style={{
                    position: 'absolute', top: 10, right: 10,
                    width: 10, height: 10, borderRadius: '50%',
                    background: color,
                    animation: 'pulse 2s ease-in-out infinite',
                }} />
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div style={{
                    width: 34, height: 34, borderRadius: 10,
                    background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                    <Icon size={16} style={{ color }} />
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {label}
                </span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color, lineHeight: 1 }}>{value ?? '—'}</div>
            {subtitle && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{subtitle}</div>}
        </div>
    );
}

// ─── Risk Bar ─────────────────────────────────────────────────────────────────

function RiskBar({ data, total }) {
    if (!data?.length || !total) return <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No data</div>;
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {data.map(({ risk_level, count }) => {
                const cfg = RISK_CONFIG[risk_level] || RISK_CONFIG.LOW;
                const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                return (
                    <div key={risk_level}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
                            <span style={{ color: cfg.color, fontWeight: 600 }}>{cfg.label} Risk</span>
                            <span style={{ color: 'var(--text-muted)' }}>{count} ({pct}%)</span>
                        </div>
                        <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.06)' }}>
                            <div style={{ width: `${pct}%`, height: '100%', borderRadius: 4, background: cfg.color, transition: 'width 0.8s ease' }} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// ─── Module Table ─────────────────────────────────────────────────────────────

function ModuleTable({ data }) {
    if (!data?.length) return <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '8px 0' }}>No module data</div>;
    return (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
                <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.1)' }}>
                    {['Module', 'Total', 'Executed', 'Failed', 'Rolled Back'].map(h => (
                        <th key={h} style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.72rem', textTransform: 'uppercase' }}>{h}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {data.map(r => (
                    <tr key={r.module} style={{ borderBottom: '1px solid rgba(148,163,184,0.04)' }}>
                        <td style={{ padding: '7px 10px' }}>
                            <span style={{ padding: '2px 8px', borderRadius: 6, background: 'rgba(124,58,237,0.15)', color: '#A78BFA', fontSize: '0.72rem', fontWeight: 600 }}>{r.module}</span>
                        </td>
                        <td style={{ padding: '7px 10px', color: 'var(--text-primary)', fontWeight: 700 }}>{r.total}</td>
                        <td style={{ padding: '7px 10px', color: '#00E676' }}>{r.executed}</td>
                        <td style={{ padding: '7px 10px', color: r.failed > 0 ? '#FF5252' : 'var(--text-muted)' }}>{r.failed}</td>
                        <td style={{ padding: '7px 10px', color: r.rolled_back > 0 ? '#FFB300' : 'var(--text-muted)' }}>{r.rolled_back}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

// ─── Pending Approval Card ────────────────────────────────────────────────────

function PendingCard({ item, onDecision, loading }) {
    const [comment, setComment] = useState('');
    const [twoFa, setTwoFa] = useState('');
    const [expanded, setExpanded] = useState(false);
    const rCfg = RISK_CONFIG[item.risk_level] || RISK_CONFIG.HIGH;
    const intentColor = INTENT_COLORS[item.intent_type] || '#94A3B8';

    return (
        <div style={{
            borderRadius: 12, overflow: 'hidden', marginBottom: 12,
            border: `1px solid ${rCfg.color}33`,
            background: rCfg.bg,
        }}>
            {/* Card header */}
            <div style={{ padding: '14px 18px', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 6 }}>
                        <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem', fontWeight: 700, background: `${intentColor}22`, color: intentColor }}>
                            {item.intent_type}
                        </span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'capitalize', color: 'var(--text-primary)' }}>
                            {item.entity}
                        </span>
                        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 6, background: rCfg.bg, color: rCfg.color, fontWeight: 700, border: `1px solid ${rCfg.color}33` }}>
                            {item.risk_level} RISK
                        </span>
                        {item.requires_2fa && (
                            <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: 6, background: 'rgba(255,179,0,0.15)', color: '#FFB300' }}>
                                2FA Required
                            </span>
                        )}
                    </div>
                    <div style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{item.requester_name}</strong> requested:{' '}
                        <em>"{item.message?.slice(0, 100)}{item.message?.length > 100 ? '...' : ''}"</em>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {item.estimated_impact_count} record(s) affected &middot; Module: <strong>{item.module}</strong>
                        {item.created_at && <> &middot; {new Date(item.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</>}
                    </div>
                </div>
                <button onClick={() => setExpanded(v => !v)} style={{
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', flexShrink: 0,
                }}>
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
            </div>

            {/* Expanded actions */}
            {expanded && (
                <div style={{ padding: '0 18px 16px', borderTop: `1px solid ${rCfg.color}22` }}>
                    <div style={{ marginTop: 12, marginBottom: 10 }}>
                        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Comment (optional)</label>
                        <input value={comment} onChange={e => setComment(e.target.value)}
                            placeholder="Reason for your decision..."
                            style={{
                                width: '100%', padding: '8px 12px',
                                background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(148,163,184,0.15)',
                                borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.82rem',
                                outline: 'none', boxSizing: 'border-box',
                            }}
                        />
                    </div>
                    {item.requires_2fa && (
                        <div style={{ marginBottom: 10 }}>
                            <label style={{ fontSize: '0.72rem', color: '#FFB300', display: 'block', marginBottom: 5, fontWeight: 600 }}>
                                2FA Code
                            </label>
                            <input value={twoFa} onChange={e => setTwoFa(e.target.value)}
                                placeholder="Enter OTP..."
                                maxLength={8}
                                style={{
                                    width: 160, padding: '8px 12px',
                                    background: 'rgba(255,179,0,0.06)', border: '1px solid rgba(255,179,0,0.3)',
                                    borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.85rem',
                                    outline: 'none', letterSpacing: '0.1em',
                                }}
                            />
                        </div>
                    )}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                            onClick={() => onDecision(item.plan_id, 'REJECT', comment, twoFa)}
                            disabled={loading}
                            style={{
                                padding: '8px 18px', borderRadius: 9,
                                border: '1px solid rgba(255,82,82,0.4)',
                                background: 'transparent', color: '#FF8A80',
                                fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}>
                            <XCircle size={14} /> Reject
                        </button>
                        <button
                            onClick={() => onDecision(item.plan_id, 'ESCALATE', comment, twoFa)}
                            disabled={loading}
                            style={{
                                padding: '8px 18px', borderRadius: 9,
                                border: '1px solid rgba(255,179,0,0.4)',
                                background: 'transparent', color: '#FFB300',
                                fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}>
                            <AlertTriangle size={14} /> Escalate
                        </button>
                        <button
                            onClick={() => onDecision(item.plan_id, 'APPROVE', comment, twoFa)}
                            disabled={loading || (item.requires_2fa && !twoFa.trim())}
                            style={{
                                padding: '8px 18px', borderRadius: 9, border: 'none',
                                background: loading ? 'rgba(0,230,118,0.3)' : 'linear-gradient(135deg, #00E676, #00BCD4)',
                                color: '#000', fontWeight: 700, cursor: 'pointer', fontSize: '0.82rem',
                                display: 'flex', alignItems: 'center', gap: 6,
                                opacity: (item.requires_2fa && !twoFa.trim()) ? 0.5 : 1,
                            }}>
                            {loading ? <Loader size={13} className="spin" /> : <CheckCircle size={14} />}
                            {loading ? 'Processing...' : 'Approve & Execute'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function GovernanceDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [stats, setStats] = useState(null);
    const [pending, setPending] = useState([]);
    const [audit, setAudit] = useState([]);
    const [loadingStats, setLoadingStats] = useState(true);
    const [loadingPending, setLoadingPending] = useState(true);
    const [loadingAudit, setLoadingAudit] = useState(false);
    const [processingId, setProcessingId] = useState(null);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    // Audit filters
    const [auditFilter, setAuditFilter] = useState({ risk_level: '', operation_type: '', module: '', limit: 100 });
    const [showAudit, setShowAudit] = useState(false);

    const loadStats = useCallback(async () => {
        setLoadingStats(true);
        try {
            const data = await api.getOpsStats();
            setStats(data);
        } catch {
            /* ignore */
        } finally {
            setLoadingStats(false);
        }
    }, []);

    const loadPending = useCallback(async () => {
        setLoadingPending(true);
        try {
            const data = await api.getPendingApprovals();
            setPending(data);
        } catch {
            /* ignore */
        } finally {
            setLoadingPending(false);
        }
    }, []);

    const loadAudit = useCallback(async () => {
        setLoadingAudit(true);
        try {
            const params = {};
            if (auditFilter.risk_level) params.risk_level = auditFilter.risk_level;
            if (auditFilter.operation_type) params.operation_type = auditFilter.operation_type;
            if (auditFilter.module) params.module = auditFilter.module;
            params.limit = auditFilter.limit || 100;
            const data = await api.operationalAIAudit(params);
            setAudit(data);
        } catch {
            /* ignore */
        } finally {
            setLoadingAudit(false);
        }
    }, [auditFilter]);

    useEffect(() => {
        loadStats();
        loadPending();
    }, [loadStats, loadPending]);

    useEffect(() => {
        if (showAudit) loadAudit();
    }, [showAudit, loadAudit]);

    // Refresh pending + stats every 30 seconds
    useEffect(() => {
        const interval = setInterval(() => {
            loadStats();
            loadPending();
        }, 30000);
        return () => clearInterval(interval);
    }, [loadStats, loadPending]);

    const handleDecision = async (planId, decision, comment, twoFaCode) => {
        setProcessingId(planId);
        setError('');
        setSuccessMsg('');
        try {
            const resp = await api.operationalAIDecision({
                planId,
                decision,
                comment: comment || null,
                twoFactorCode: twoFaCode || null,
            });

            if (decision === 'APPROVE') {
                // Execute the plan after approval
                await api.operationalAIExecute(planId);
                setSuccessMsg(`Plan ${planId} approved and executed successfully.`);
            } else if (decision === 'REJECT') {
                setSuccessMsg(`Plan ${planId} rejected.`);
            } else {
                setSuccessMsg(`Plan ${planId} escalated for further review.`);
            }

            // Refresh data
            await loadPending();
            await loadStats();
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Decision failed. Please retry.');
        } finally {
            setProcessingId(null);
        }
    };

    const totalPlans = stats?.total_plans || 0;

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* ── Header ── */}
                <div className="page-header animate-in">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 46, height: 46, borderRadius: 13,
                            background: 'linear-gradient(135deg, #E91E63 0%, #FF5252 100%)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            boxShadow: '0 0 20px rgba(233,30,99,0.4)',
                        }}>
                            <Shield size={22} color="#fff" />
                        </div>
                        <div>
                            <h1 style={{ margin: 0, fontSize: '1.3rem' }}>Governance Dashboard</h1>
                            <p style={{ margin: 0, opacity: 0.6, fontSize: '0.8rem' }}>
                                Operational AI oversight — Approvals, Audit Trail, Risk Analytics
                            </p>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={() => { loadStats(); loadPending(); }} style={{
                            padding: '7px 16px', borderRadius: 10, fontSize: '0.82rem',
                            border: '1px solid rgba(148,163,184,0.2)', background: 'transparent',
                            color: 'var(--text-muted)', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            <RefreshCw size={13} /> Refresh
                        </button>
                        <button onClick={() => navigate('/copilot')} style={{
                            padding: '7px 16px', borderRadius: 10, fontSize: '0.82rem',
                            border: 'none', background: 'linear-gradient(135deg, #7C3AED, #2563EB)',
                            color: '#fff', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            <Terminal size={13} /> Command Console
                        </button>
                    </div>
                </div>

                {/* ── Toast messages ── */}
                {successMsg && (
                    <div className="glass-card mb-lg animate-in" style={{
                        borderLeft: '4px solid #00E676', padding: '12px 18px',
                        color: '#A5D6A7', display: 'flex', gap: 8, alignItems: 'center',
                    }}>
                        <CheckCircle size={15} />
                        {successMsg}
                        <button onClick={() => setSuccessMsg('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#A5D6A7' }}>×</button>
                    </div>
                )}
                {error && (
                    <div className="glass-card mb-lg animate-in" style={{
                        borderLeft: '4px solid #FF5252', padding: '12px 18px',
                        color: '#FF8A80', display: 'flex', gap: 8, alignItems: 'center',
                    }}>
                        <AlertTriangle size={15} />
                        {error}
                        <button onClick={() => setError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#FF8A80' }}>×</button>
                    </div>
                )}

                {/* ── Stats Grid ── */}
                <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 24 }}>
                    {loadingStats ? (
                        Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} style={{ flex: '1 1 180px', height: 100, borderRadius: 14, background: 'rgba(15,23,42,0.4)' }}
                                className="skeleton" />
                        ))
                    ) : (
                        <>
                            <StatCard label="Total Plans" value={stats?.total_plans ?? 0} subtitle="All time" color="#64B5F6" icon={Database} />
                            <StatCard label="Awaiting Approval" value={stats?.awaiting_approval ?? 0} subtitle="Needs review" color="#FF5252" icon={Shield} pulse />
                            <StatCard label="Executed Today" value={stats?.executed_today ?? 0} subtitle="Since midnight" color="#00E676" icon={Activity} />
                            <StatCard label="Total Failures" value={stats?.failed_total ?? 0} subtitle="All time" color="#FFB300" icon={AlertTriangle} />
                        </>
                    )}
                </div>

                {/* ── Analytics Row ── */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 24 }}>
                    {/* Risk distribution */}
                    <div className="glass-card" style={{ padding: '18px 20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                            <BarChart3 size={16} style={{ color: '#A78BFA' }} />
                            <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>Risk Distribution</span>
                        </div>
                        {loadingStats ? (
                            <div className="skeleton" style={{ height: 80, borderRadius: 8 }} />
                        ) : (
                            <RiskBar data={stats?.by_risk} total={totalPlans} />
                        )}
                    </div>

                    {/* Module breakdown */}
                    <div className="glass-card" style={{ padding: '18px 20px', gridColumn: 'span 2' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                            <TrendingUp size={16} style={{ color: '#64B5F6' }} />
                            <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>Module Breakdown</span>
                        </div>
                        {loadingStats ? (
                            <div className="skeleton" style={{ height: 80, borderRadius: 8 }} />
                        ) : (
                            <ModuleTable data={stats?.by_module} />
                        )}
                    </div>
                </div>

                {/* ── Pending Approvals Queue ── */}
                <div className="glass-card animate-in mb-lg">
                    <div style={{ padding: '18px 22px', borderBottom: '1px solid rgba(148,163,184,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: 9,
                                background: 'rgba(255,82,82,0.15)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}>
                                <Clock size={16} style={{ color: '#FF5252' }} />
                            </div>
                            <div>
                                <div style={{ fontWeight: 700, fontSize: '0.92rem' }}>
                                    Pending Approvals
                                    {pending.length > 0 && (
                                        <span style={{
                                            marginLeft: 8, padding: '2px 8px', borderRadius: 12,
                                            background: '#FF5252', color: '#fff',
                                            fontSize: '0.72rem', fontWeight: 800,
                                        }}>{pending.length}</span>
                                    )}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    High-risk operations awaiting senior approval
                                </div>
                            </div>
                        </div>
                        <button onClick={loadPending} style={{
                            background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                        }}>
                            <RefreshCw size={15} />
                        </button>
                    </div>

                    <div style={{ padding: '16px 22px' }}>
                        {loadingPending ? (
                            <div style={{ textAlign: 'center', padding: 24, opacity: 0.5 }}>
                                <Loader size={22} className="spin" />
                            </div>
                        ) : pending.length === 0 ? (
                            <div style={{
                                textAlign: 'center', padding: '28px 0',
                                fontSize: '0.85rem', color: 'var(--text-muted)',
                            }}>
                                <CheckCircle size={28} style={{ color: '#00E676', marginBottom: 8, display: 'block', margin: '0 auto 8px' }} />
                                No pending approvals — all clear!
                            </div>
                        ) : (
                            pending.map(item => (
                                <PendingCard
                                    key={item.plan_id}
                                    item={item}
                                    loading={processingId === item.plan_id}
                                    onDecision={handleDecision}
                                />
                            ))
                        )}
                    </div>
                </div>

                {/* ── Full Audit Trail ── */}
                <div className="glass-card animate-in mb-lg">
                    <div
                        style={{
                            padding: '16px 22px', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            borderBottom: showAudit ? '1px solid rgba(148,163,184,0.08)' : 'none',
                        }}
                        onClick={() => setShowAudit(v => !v)}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <FileText size={16} style={{ color: '#64748B' }} />
                            <div>
                                <div style={{ fontWeight: 700, fontSize: '0.92rem' }}>
                                    System Audit Trail
                                    {audit.length > 0 && showAudit && (
                                        <span style={{
                                            marginLeft: 8, padding: '2px 7px', borderRadius: 12, fontSize: '0.7rem',
                                            background: 'rgba(100,116,139,0.2)', color: '#94A3B8',
                                        }}>{audit.length}</span>
                                    )}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    Immutable log of all operational AI events
                                </div>
                            </div>
                        </div>
                        {showAudit ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>

                    {showAudit && (
                        <div style={{ padding: '14px 22px 20px' }}>
                            {/* Filters */}
                            <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
                                {[
                                    { key: 'risk_level', label: 'Risk', opts: ['', 'LOW', 'MEDIUM', 'HIGH'] },
                                    { key: 'operation_type', label: 'Operation', opts: ['', 'READ', 'CREATE', 'UPDATE', 'DELETE', 'ANALYZE', 'ESCALATE'] },
                                    { key: 'module', label: 'Module', opts: ['', 'nlp', 'finance', 'hr', 'predictions'] },
                                ].map(f => (
                                    <select key={f.key} value={auditFilter[f.key]}
                                        onChange={e => setAuditFilter(prev => ({ ...prev, [f.key]: e.target.value }))}
                                        style={{
                                            padding: '6px 12px', borderRadius: 8, fontSize: '0.8rem',
                                            background: 'rgba(15,23,42,0.5)',
                                            border: '1px solid rgba(148,163,184,0.15)',
                                            color: 'var(--text-primary)', outline: 'none',
                                        }}>
                                        {f.opts.map(o => <option key={o} value={o}>{o || `All ${f.label}`}</option>)}
                                    </select>
                                ))}
                                <select value={auditFilter.limit}
                                    onChange={e => setAuditFilter(prev => ({ ...prev, limit: Number(e.target.value) }))}
                                    style={{
                                        padding: '6px 12px', borderRadius: 8, fontSize: '0.8rem',
                                        background: 'rgba(15,23,42,0.5)',
                                        border: '1px solid rgba(148,163,184,0.15)',
                                        color: 'var(--text-primary)', outline: 'none',
                                    }}>
                                    {[50, 100, 200, 500].map(n => <option key={n} value={n}>Last {n}</option>)}
                                </select>
                                <button onClick={loadAudit} style={{
                                    padding: '6px 14px', borderRadius: 8, fontSize: '0.8rem',
                                    background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)',
                                    color: '#A78BFA', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: 5,
                                }}>
                                    <Filter size={12} /> Apply
                                </button>
                            </div>

                            {loadingAudit ? (
                                <div style={{ textAlign: 'center', padding: 24, opacity: 0.5 }}>
                                    <Loader size={22} className="spin" />
                                </div>
                            ) : audit.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '24px 0', opacity: 0.45, fontSize: '0.85rem' }}>
                                    No audit events found with current filters.
                                </div>
                            ) : (
                                <div style={{ overflowX: 'auto' }}>
                                    <table className="data-table" style={{ fontSize: '0.77rem' }}>
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>User</th>
                                                <th>Role</th>
                                                <th>Operation</th>
                                                <th>Entity</th>
                                                <th>Module</th>
                                                <th>Event</th>
                                                <th>Risk</th>
                                                <th>Plan ID</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {audit.map((log, i) => {
                                                const rCfg = RISK_CONFIG[log.risk_level] || RISK_CONFIG.LOW;
                                                const opColor = INTENT_COLORS[log.operation_type] || '#94A3B8';
                                                const evtColor = EVT_COLOR[log.event_type] || '#94A3B8';
                                                return (
                                                    <tr key={i}>
                                                        <td style={{ whiteSpace: 'nowrap', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                                                            {log.created_at ? new Date(log.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
                                                        </td>
                                                        <td style={{ color: 'var(--text-muted)' }}>#{log.user_id}</td>
                                                        <td style={{ textTransform: 'capitalize', color: 'var(--text-muted)', fontSize: '0.72rem' }}>{log.role}</td>
                                                        <td>
                                                            <span style={{ padding: '2px 7px', borderRadius: 6, fontSize: '0.68rem', fontWeight: 700, background: `${opColor}18`, color: opColor }}>
                                                                {log.operation_type}
                                                            </span>
                                                        </td>
                                                        <td style={{ color: 'var(--text-muted)' }}>{log.intent_payload?.entity || '—'}</td>
                                                        <td>
                                                            <span style={{ padding: '2px 6px', borderRadius: 6, fontSize: '0.67rem', background: 'rgba(148,163,184,0.1)', color: '#94A3B8' }}>
                                                                {log.module}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span style={{ padding: '2px 7px', borderRadius: 6, fontSize: '0.68rem', fontWeight: 600, background: `${evtColor}18`, color: evtColor }}>
                                                                {log.event_type}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span style={{ padding: '2px 7px', borderRadius: 6, fontSize: '0.68rem', fontWeight: 700, background: rCfg.bg, color: rCfg.color }}>
                                                                {log.risk_level}
                                                            </span>
                                                        </td>
                                                        <td style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                                                            {log.plan_id?.slice(0, 14) || '—'}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                .spin { animation: spin 1s linear infinite; }
                @keyframes pulse {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.5; transform: scale(1.3); }
                }
            `}</style>
        </div>
    );
}
