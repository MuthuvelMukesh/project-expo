import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import api from '../services/api';
import {
    Sparkles, Send, CheckCircle, XCircle, AlertTriangle,
    Clock, ChevronDown, ChevronUp, Shield, Zap,
    History, RotateCcw, Terminal, Bot, Loader,
} from 'lucide-react';

const RISK_STYLES = {
    safe: { color: '#00E676', bg: 'rgba(0,230,118,0.1)', icon: CheckCircle, label: 'Auto' },
    low: { color: '#FFB300', bg: 'rgba(255,179,0,0.1)', icon: AlertTriangle, label: 'Confirm' },
    high: { color: '#FF5252', bg: 'rgba(255,82,82,0.1)', icon: Shield, label: 'Confirm' },
};

const STATUS_STYLES = {
    executed: { color: '#00E676', icon: CheckCircle },
    pending: { color: '#FFB300', icon: Clock },
    rejected: { color: '#FF5252', icon: XCircle },
    failed: { color: '#FF5252', icon: XCircle },
};

export default function CopilotPanel() {
    const { user } = useAuth();
    const [input, setInput] = useState('');
    const [plan, setPlan] = useState(null);
    const [results, setResults] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [executing, setExecuting] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [error, setError] = useState('');
    const inputRef = useRef(null);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const data = await api.copilotHistory();
            setHistory(data);
        } catch { /* ignore */ }
    };

    const extractErrorMessage = (err, fallback) => {
        if (!err) return fallback;

        const raw =
            (typeof err === 'string' && err) ||
            err?.message ||
            err?.detail ||
            (typeof err?.toString === 'function' ? err.toString() : '');

        if (!raw) return fallback;

        const normalized = String(raw).trim();
        if (!normalized) return fallback;

        if (normalized.startsWith('<!DOCTYPE') || normalized.startsWith('<html')) {
            return 'Server returned HTML instead of JSON. Please verify backend/proxy configuration.';
        }

        return normalized.length > 260 ? `${normalized.slice(0, 260)}...` : normalized;
    };

    const handlePlan = async () => {
        if (!input.trim() || loading) return;
        setError('');
        setPlan(null);
        setResults(null);
        setLoading(true);
        try {
            const data = await api.copilotPlan(input);
            setPlan(data);
            if (!data.requires_confirmation && data.auto_executed?.length) {
                setResults({
                    plan_id: data.plan_id,
                    actions_executed: data.auto_executed.length,
                    actions_failed: 0,
                    actions_rejected: 0,
                    results: data.auto_executed,
                    summary: `✅ All ${data.auto_executed.length} action(s) executed automatically.`,
                });
            }
            loadHistory();
        } catch (err) {
            setError(extractErrorMessage(err, 'Failed to create plan'));
        } finally {
            setLoading(false);
        }
    };

    const handleExecute = async (approveAll = true) => {
        if (!plan || executing) return;
        setExecuting(true);
        setError('');
        try {
            const pendingActions = plan.actions.filter(a => a.type !== 'DENIED');
            const data = await api.copilotExecute(
                plan.plan_id,
                approveAll ? pendingActions.map(a => a.action_id) : [],
                approveAll ? [] : pendingActions.map(a => a.action_id),
            );
            setResults(data);
            loadHistory();
        } catch (err) {
            setError(extractErrorMessage(err, 'Failed to execute plan'));
        } finally {
            setExecuting(false);
        }
    };

    const handleReset = () => {
        setPlan(null);
        setResults(null);
        setInput('');
        setError('');
        inputRef.current?.focus();
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handlePlan();
        }
    };

    const formatResult = (result) => {
        if (!result) return null;
        if (result.summary) return result.summary;
        if (result.result?.summary) return result.result.summary;
        if (result.result?.message) return result.result.message;
        if (result.result?.row_count !== undefined) return `Found ${result.result.row_count} records`;
        return JSON.stringify(result, null, 2);
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div className="page-header animate-in">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 44, height: 44, borderRadius: 12,
                            background: 'linear-gradient(135deg, #7C3AED, #2563EB)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <Sparkles size={22} color="#fff" />
                        </div>
                        <div>
                            <h1 style={{ margin: 0 }}>AI Copilot</h1>
                            <p style={{ margin: 0, opacity: 0.7, fontSize: '0.85rem' }}>
                                Tell me what you need — I'll plan it, you approve it
                            </p>
                        </div>
                    </div>
                    <div style={{
                        padding: '6px 14px', borderRadius: 20,
                        background: 'rgba(124,58,237,0.15)', color: '#A78BFA',
                        fontSize: '0.8rem', fontWeight: 600,
                    }}>
                        {user?.role?.toUpperCase()} MODE
                    </div>
                </div>

                {/* Command Input */}
                <div className="glass-card animate-in mb-lg" style={{ padding: '24px 28px' }}>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{
                                display: 'block', fontSize: '0.8rem', fontWeight: 600,
                                color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                            }}>
                                <Terminal size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                                What would you like to do?
                            </label>
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={
                                    user?.role === 'admin'
                                        ? 'e.g. "Show all students in CS department" or "Create a new course called AI"'
                                        : user?.role === 'faculty'
                                            ? 'e.g. "Generate QR for my Data Structures class" or "Show risk roster"'
                                            : 'e.g. "Show my attendance" or "Update my section to B"'
                                }
                                rows={2}
                                style={{
                                    width: '100%', padding: '14px 16px',
                                    background: 'rgba(15,23,42,0.6)',
                                    border: '1px solid rgba(148,163,184,0.2)',
                                    borderRadius: 12, color: 'var(--text-primary)',
                                    fontSize: '0.95rem', resize: 'none', fontFamily: 'inherit',
                                    outline: 'none', transition: 'border-color 0.2s',
                                }}
                                onFocus={e => e.target.style.borderColor = '#7C3AED'}
                                onBlur={e => e.target.style.borderColor = 'rgba(148,163,184,0.2)'}
                            />
                        </div>
                        <button
                            onClick={handlePlan}
                            disabled={!input.trim() || loading}
                            style={{
                                padding: '14px 24px', borderRadius: 12, border: 'none',
                                background: loading ? 'rgba(124,58,237,0.3)' : 'linear-gradient(135deg, #7C3AED, #2563EB)',
                                color: '#fff', fontWeight: 600, cursor: loading ? 'wait' : 'pointer',
                                display: 'flex', alignItems: 'center', gap: 8,
                                fontSize: '0.9rem', minHeight: 48,
                                transition: 'all 0.2s',
                            }}
                        >
                            {loading ? <Loader size={18} className="spin" /> : <Send size={18} />}
                            {loading ? 'Planning...' : 'Plan'}
                        </button>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="glass-card mb-lg animate-in" style={{
                        borderLeft: '4px solid #FF5252', padding: '16px 20px',
                        color: '#FF8A80',
                    }}>
                        <AlertTriangle size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />
                        {error}
                    </div>
                )}

                {/* Action Plan */}
                {plan && !results && (
                    <div className="glass-card animate-in mb-lg">
                        <div className="section-header" style={{ marginBottom: 16 }}>
                            <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Zap size={20} style={{ color: '#FFB300' }} />
                                Action Plan
                            </h2>
                            <span style={{
                                padding: '4px 12px', borderRadius: 12, fontSize: '0.75rem',
                                background: 'rgba(124,58,237,0.15)', color: '#A78BFA', fontWeight: 600,
                            }}>
                                {plan.plan_id}
                            </span>
                        </div>

                        {/* Summary */}
                        <div style={{
                            padding: '12px 16px', borderRadius: 10,
                            background: 'rgba(15,23,42,0.5)', marginBottom: 16,
                            fontSize: '0.9rem', lineHeight: 1.6,
                        }}
                            dangerouslySetInnerHTML={{ __html: plan.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
                        />

                        {/* Auto-executed results */}
                        {plan.auto_executed?.length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#00E676', marginBottom: 8 }}>
                                    ⚡ Auto-Executed (Safe)
                                </div>
                                {plan.auto_executed.map((r, i) => (
                                    <div key={i} style={{
                                        padding: '10px 14px', borderRadius: 8,
                                        background: 'rgba(0,230,118,0.05)', marginBottom: 6,
                                        borderLeft: '3px solid #00E676', fontSize: '0.85rem',
                                    }}>
                                        <CheckCircle size={14} style={{ verticalAlign: 'middle', marginRight: 8, color: '#00E676' }} />
                                        {r.description}
                                        {r.result?.summary && <div style={{ marginTop: 4, opacity: 0.8, paddingLeft: 22 }}>{r.result.summary}</div>}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Pending actions requiring confirmation */}
                        {plan.actions.filter(a => a.type !== 'DENIED').length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#FFB300', marginBottom: 8 }}>
                                    ⏳ Awaiting Your Approval
                                </div>
                                {plan.actions.filter(a => a.type !== 'DENIED').map((action, i) => {
                                    const rs = RISK_STYLES[action.risk_level] || RISK_STYLES.high;
                                    const RiskIcon = rs.icon;
                                    return (
                                        <div key={i} style={{
                                            padding: '14px 16px', borderRadius: 10,
                                            background: rs.bg, marginBottom: 8,
                                            borderLeft: `3px solid ${rs.color}`,
                                            display: 'flex', alignItems: 'center', gap: 12,
                                        }}>
                                            <RiskIcon size={18} style={{ color: rs.color, flexShrink: 0 }} />
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{action.description}</div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                                    {action.type} → {action.entity}
                                                </div>
                                            </div>
                                            <span style={{
                                                padding: '3px 10px', borderRadius: 8, fontSize: '0.7rem',
                                                background: `${rs.color}22`, color: rs.color, fontWeight: 700,
                                                textTransform: 'uppercase',
                                            }}>
                                                {action.risk_level}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Denied actions */}
                        {plan.actions.filter(a => a.type === 'DENIED').length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#FF5252', marginBottom: 8 }}>
                                    🚫 Denied
                                </div>
                                {plan.actions.filter(a => a.type === 'DENIED').map((action, i) => (
                                    <div key={i} style={{
                                        padding: '10px 14px', borderRadius: 8,
                                        background: 'rgba(255,82,82,0.05)', marginBottom: 6,
                                        borderLeft: '3px solid #FF5252', fontSize: '0.85rem', opacity: 0.7,
                                    }}>
                                        <XCircle size={14} style={{ verticalAlign: 'middle', marginRight: 8, color: '#FF5252' }} />
                                        {action.description}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Action buttons */}
                        {plan.requires_confirmation && (
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', paddingTop: 8 }}>
                                <button
                                    onClick={() => handleExecute(false)}
                                    disabled={executing}
                                    style={{
                                        padding: '10px 20px', borderRadius: 10, border: '1px solid rgba(255,82,82,0.4)',
                                        background: 'transparent', color: '#FF8A80', fontWeight: 600,
                                        cursor: 'pointer', fontSize: '0.85rem',
                                    }}
                                >
                                    <XCircle size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                                    Reject All
                                </button>
                                <button
                                    onClick={() => handleExecute(true)}
                                    disabled={executing}
                                    style={{
                                        padding: '10px 20px', borderRadius: 10, border: 'none',
                                        background: executing ? 'rgba(0,230,118,0.3)' : 'linear-gradient(135deg, #00E676, #00BCD4)',
                                        color: '#fff', fontWeight: 600, cursor: executing ? 'wait' : 'pointer',
                                        fontSize: '0.85rem',
                                    }}
                                >
                                    {executing ? (
                                        <><Loader size={14} className="spin" style={{ verticalAlign: 'middle', marginRight: 6 }} />Executing...</>
                                    ) : (
                                        <><CheckCircle size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />Approve & Execute</>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Execution Results */}
                {results && (
                    <div className="glass-card animate-in mb-lg">
                        <div className="section-header" style={{ marginBottom: 16 }}>
                            <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <CheckCircle size={20} style={{ color: '#00E676' }} />
                                Execution Results
                            </h2>
                        </div>

                        <div style={{
                            padding: '12px 16px', borderRadius: 10,
                            background: 'rgba(0,230,118,0.05)', marginBottom: 16,
                            fontSize: '0.9rem', lineHeight: 1.6,
                            borderLeft: '3px solid #00E676',
                        }}
                            dangerouslySetInnerHTML={{ __html: results.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
                        />

                        {results.results?.map((r, i) => {
                            const ss = STATUS_STYLES[r.status] || STATUS_STYLES.pending;
                            const StatusIcon = ss.icon;
                            return (
                                <div key={i} style={{
                                    padding: '12px 16px', borderRadius: 8,
                                    background: 'rgba(15,23,42,0.4)', marginBottom: 6,
                                    borderLeft: `3px solid ${ss.color}`, fontSize: '0.85rem',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <StatusIcon size={14} style={{ color: ss.color }} />
                                        <span style={{ fontWeight: 600 }}>{r.description}</span>
                                        <span style={{
                                            marginLeft: 'auto', fontSize: '0.7rem', padding: '2px 8px',
                                            borderRadius: 6, background: `${ss.color}18`, color: ss.color,
                                            fontWeight: 700, textTransform: 'uppercase',
                                        }}>{r.status}</span>
                                    </div>
                                    {r.result && (
                                        <div style={{ marginTop: 6, paddingLeft: 22, opacity: 0.8, fontSize: '0.8rem' }}>
                                            {formatResult(r)}
                                        </div>
                                    )}
                                    {r.error && (
                                        <div style={{ marginTop: 6, paddingLeft: 22, color: '#FF8A80', fontSize: '0.8rem' }}>
                                            Error: {r.error}
                                        </div>
                                    )}
                                </div>
                            );
                        })}

                        <div style={{ textAlign: 'center', paddingTop: 16 }}>
                            <button onClick={handleReset} style={{
                                padding: '10px 24px', borderRadius: 10, border: '1px solid rgba(148,163,184,0.2)',
                                background: 'transparent', color: 'var(--text-primary)', fontWeight: 600,
                                cursor: 'pointer', fontSize: '0.85rem',
                            }}>
                                <RotateCcw size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                                New Command
                            </button>
                        </div>
                    </div>
                )}

                {/* History */}
                <div className="glass-card animate-in mb-lg">
                    <div
                        className="section-header"
                        style={{ cursor: 'pointer' }}
                        onClick={() => setShowHistory(!showHistory)}
                    >
                        <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <History size={20} style={{ color: '#64748B' }} />
                            Action History
                        </h2>
                        {showHistory ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>

                    {showHistory && (
                        <div style={{ marginTop: 12 }}>
                            {history.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: 24, opacity: 0.5, fontSize: '0.85rem' }}>
                                    No copilot actions yet. Try a command above!
                                </div>
                            ) : (
                                <table className="data-table" style={{ fontSize: '0.8rem' }}>
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Action</th>
                                            <th>Entity</th>
                                            <th>Description</th>
                                            <th>Risk</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history.slice(0, 20).map((log, i) => {
                                            const rs = RISK_STYLES[log.risk_level] || RISK_STYLES.safe;
                                            const ss = STATUS_STYLES[log.status] || STATUS_STYLES.pending;
                                            return (
                                                <tr key={i}>
                                                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                                                        {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                                                    </td>
                                                    <td>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem',
                                                            background: 'rgba(124,58,237,0.15)', color: '#A78BFA', fontWeight: 600,
                                                        }}>{log.action_type}</span>
                                                    </td>
                                                    <td>{log.entity}</td>
                                                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                        {log.description}
                                                    </td>
                                                    <td>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem',
                                                            background: `${rs.color}18`, color: rs.color, fontWeight: 700,
                                                        }}>{log.risk_level}</span>
                                                    </td>
                                                    <td>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem',
                                                            background: `${ss.color}18`, color: ss.color, fontWeight: 700,
                                                        }}>{log.status}</span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}
                </div>
            </main>

            {/* Spinning animation for loaders */}
            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                .spin { animation: spin 1s linear infinite; }
            `}</style>
        </div>
    );
}
