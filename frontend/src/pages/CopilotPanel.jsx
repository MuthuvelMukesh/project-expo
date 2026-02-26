/**
 * CampusIQ — Command Console (Conversational Operational AI)
 * Full ops-ai integration: NL → Plan → Risk → Approval → Execute → Audit
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import api from '../services/api';
import {
    Sparkles, Send, CheckCircle, XCircle, AlertTriangle,
    Clock, Shield, Zap, History, RotateCcw, Terminal,
    Loader, ChevronDown, ChevronUp, Eye, EyeOff,
    Database, Lock, Info, RefreshCw, Search, Filter,
    TrendingUp, Activity, FileText, ArrowRight,
} from 'lucide-react';

// ─── Constants ──────────────────────────────────────────────────────────────

const MODULES = [
    { value: 'nlp', label: 'Academic', emoji: '🎓' },
    { value: 'finance', label: 'Finance', emoji: '💰' },
    { value: 'hr', label: 'HR & Payroll', emoji: '👥' },
    { value: 'predictions', label: 'Predictions', emoji: '📊' },
];

const ROLE_SUGGESTIONS = {
    admin: [
        'Show all students with CGPA below 6.0',
        'How many students in each department?',
        'List all faculty in Computer Science',
        'Show pending fee invoices this semester',
        'Analyze attendance trends for semester 4',
        'Update CGPA for students in section A',
        'Show employees hired this year',
        'Generate payroll summary for January 2025',
    ],
    faculty: [
        'Show my students with low attendance',
        'List all students in my Data Structures course',
        'How many students are at risk in my courses?',
        'Show predicted grades for my class',
        'Analyze attendance for course CS301',
        'Mark attendance for today\'s class',
    ],
    student: [
        'Show my attendance across all courses',
        'What is my current CGPA?',
        'Show my predicted grades',
        'Show my fee balance',
        'Which courses have I attended less than 75%?',
        'Show my semester timetable',
    ],
};

const RISK_CONFIG = {
    LOW: {
        color: '#00E676', bg: 'rgba(0,230,118,0.12)', border: '#00E676',
        label: 'Low Risk', icon: CheckCircle,
        description: 'Read-only or minimal impact. Executes automatically.',
    },
    MEDIUM: {
        color: '#FFB300', bg: 'rgba(255,179,0,0.12)', border: '#FFB300',
        label: 'Medium Risk', icon: AlertTriangle,
        description: 'Modifies data. Requires your confirmation before execution.',
    },
    HIGH: {
        color: '#FF5252', bg: 'rgba(255,82,82,0.12)', border: '#FF5252',
        label: 'High Risk', icon: Shield,
        description: 'Critical operation. Requires senior admin approval + 2FA.',
    },
};

const INTENT_COLORS = {
    READ: '#64B5F6', ANALYZE: '#CE93D8', CREATE: '#A5D6A7',
    UPDATE: '#FFE082', DELETE: '#EF9A9A', ESCALATE: '#FF8A65',
};

const STATUS_STEPS = [
    { id: 'parse', label: 'Parsing your intent...' },
    { id: 'perms', label: 'Checking permissions...' },
    { id: 'impact', label: 'Estimating impact...' },
    { id: 'preview', label: 'Building execution preview...' },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function RiskBadge({ level, size = 'sm' }) {
    const cfg = RISK_CONFIG[level] || RISK_CONFIG.LOW;
    const RiskIcon = cfg.icon;
    const px = size === 'lg' ? '8px 16px' : '3px 10px';
    const fs = size === 'lg' ? '0.8rem' : '0.7rem';
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: px, borderRadius: 20, fontSize: fs, fontWeight: 700,
            background: cfg.bg, color: cfg.color,
            border: `1px solid ${cfg.border}33`,
        }}>
            <RiskIcon size={size === 'lg' ? 14 : 11} />
            {cfg.label}
        </span>
    );
}

function IntentBadge({ intent }) {
    const color = INTENT_COLORS[intent] || '#94A3B8';
    return (
        <span style={{
            padding: '3px 10px', borderRadius: 20, fontSize: '0.7rem',
            fontWeight: 700, background: `${color}22`, color,
        }}>{intent}</span>
    );
}

function ConfidenceMeter({ value }) {
    const pct = Math.round((value || 0) * 100);
    const color = pct >= 80 ? '#00E676' : pct >= 60 ? '#FFB300' : '#FF5252';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
                flex: 1, height: 6, borderRadius: 3,
                background: 'rgba(255,255,255,0.08)',
            }}>
                <div style={{
                    width: `${pct}%`, height: '100%', borderRadius: 3,
                    background: color,
                    transition: 'width 0.5s ease',
                }} />
            </div>
            <span style={{ fontSize: '0.75rem', color, fontWeight: 700, minWidth: 36 }}>
                {pct}%
            </span>
        </div>
    );
}

function DiffRow({ before, after, field }) {
    const bVal = before?.[field];
    const aVal = after?.[field];
    const changed = JSON.stringify(bVal) !== JSON.stringify(aVal);
    if (!changed) return null;
    return (
        <tr style={{ fontSize: '0.75rem' }}>
            <td style={{ padding: '3px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>{field}</td>
            <td style={{ padding: '3px 8px', color: '#EF9A9A', textDecoration: 'line-through' }}>
                {JSON.stringify(bVal)}
            </td>
            <td style={{ padding: '3px 8px', color: '#A5D6A7' }}>{JSON.stringify(aVal)}</td>
        </tr>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CopilotPanel() {
    const { user } = useAuth();

    // Input state
    const [input, setInput] = useState('');
    const [module, setModule] = useState('nlp');
    const [clarification, setClarification] = useState('');

    // Flow state
    const [planStep, setPlanStep] = useState(0); // 0=idle, 1-4=loading steps
    const [plan, setPlan] = useState(null);
    const [execution, setExecution] = useState(null);
    const [error, setError] = useState('');
    const [executing, setExecuting] = useState(false);
    const [rollingBack, setRollingBack] = useState(false);

    // Approval form state
    const [twoFaCode, setTwoFaCode] = useState('');
    const [approvalComment, setApprovalComment] = useState('');
    const [showTwoFa, setShowTwoFa] = useState(false);
    const [selectedIds, setSelectedIds] = useState([]);

    // History
    const [history, setHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [historyFilter, setHistoryFilter] = useState({ risk_level: '', operation_type: '', module: '' });
    const [loadingHistory, setLoadingHistory] = useState(false);

    // Preview toggle
    const [showPreview, setShowPreview] = useState(false);
    const [showDiff, setShowDiff] = useState(false);

    const inputRef = useRef(null);
    const stepTimerRef = useRef(null);

    // Auto-select all affected records on plan load
    useEffect(() => {
        if (plan?.preview?.affected_records) {
            const ids = plan.preview.affected_records.map(r => r.id).filter(Boolean);
            setSelectedIds(ids);
        }
    }, [plan]);

    const loadHistory = useCallback(async () => {
        setLoadingHistory(true);
        try {
            const params = {};
            if (historyFilter.risk_level) params.risk_level = historyFilter.risk_level;
            if (historyFilter.operation_type) params.operation_type = historyFilter.operation_type;
            if (historyFilter.module) params.module = historyFilter.module;
            params.limit = 50;
            const data = await api.operationalAIAudit(params);
            setHistory(data);
        } catch {
            /* ignore */
        } finally {
            setLoadingHistory(false);
        }
    }, [historyFilter]);

    useEffect(() => {
        if (showHistory) loadHistory();
    }, [showHistory, loadHistory]);

    const animatePlanSteps = () => {
        setPlanStep(1);
        let step = 1;
        stepTimerRef.current = setInterval(() => {
            step += 1;
            if (step > STATUS_STEPS.length) {
                clearInterval(stepTimerRef.current);
                return;
            }
            setPlanStep(step);
        }, 600);
    };

    const handlePlan = async () => {
        if (!input.trim() || planStep > 0) return;
        setError('');
        setPlan(null);
        setExecution(null);
        setTwoFaCode('');
        setApprovalComment('');
        setShowPreview(false);
        setShowDiff(false);
        animatePlanSteps();

        try {
            const data = await api.operationalAIPlan(input, module, null);
            setPlan(data);

            // If auto-executed, populate execution immediately
            if (data.auto_execution && data.auto_execution.status === 'executed') {
                setExecution(data.auto_execution);
            }
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Failed to create plan. Please try again.');
        } finally {
            clearInterval(stepTimerRef.current);
            setPlanStep(0);
        }
    };

    const handleClarify = async () => {
        if (!clarification.trim() || planStep > 0) return;
        setError('');
        setExecution(null);
        animatePlanSteps();
        try {
            const data = await api.operationalAIPlan(input, module, clarification);
            setPlan(data);
            setClarification('');
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Failed to process clarification.');
        } finally {
            clearInterval(stepTimerRef.current);
            setPlanStep(0);
        }
    };

    const handleDecision = async (decision) => {
        if (!plan || executing) return;
        if (plan.requires_2fa && !twoFaCode.trim()) {
            setError('2FA code is required for this high-risk operation.');
            return;
        }
        setExecuting(true);
        setError('');
        try {
            const decisionResp = await api.operationalAIDecision({
                planId: plan.plan_id,
                decision,
                approvedIds: decision === 'APPROVE' ? selectedIds : [],
                rejectedIds: decision === 'REJECT' ? selectedIds : [],
                comment: approvalComment || null,
                twoFactorCode: twoFaCode || null,
            });

            if (decision === 'APPROVE') {
                // Execute after approval
                const execResp = await api.operationalAIExecute(plan.plan_id);
                setExecution(execResp);
                setPlan(prev => ({ ...prev, status: execResp.status }));
            } else {
                setPlan(prev => ({ ...prev, status: decisionResp.status }));
            }
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Decision failed. Please retry.');
        } finally {
            setExecuting(false);
        }
    };

    const handleDirectExecute = async () => {
        if (!plan || executing) return;
        setExecuting(true);
        setError('');
        try {
            const execResp = await api.operationalAIExecute(plan.plan_id);
            setExecution(execResp);
            setPlan(prev => ({ ...prev, status: execResp.status }));
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Execution failed.');
        } finally {
            setExecuting(false);
        }
    };

    const handleRollback = async () => {
        if (!execution?.execution_id || rollingBack) return;
        setRollingBack(true);
        setError('');
        try {
            const rb = await api.operationalAIRollback(execution.execution_id);
            setExecution(prev => ({ ...prev, status: rb.status }));
            setPlan(prev => ({ ...prev, status: rb.status }));
        } catch (err) {
            setError(typeof err?.message === 'string' ? err.message : 'Rollback failed.');
        } finally {
            setRollingBack(false);
        }
    };

    const handleReset = () => {
        setPlan(null);
        setExecution(null);
        setInput('');
        setClarification('');
        setError('');
        setTwoFaCode('');
        setApprovalComment('');
        setShowPreview(false);
        setShowDiff(false);
        inputRef.current?.focus();
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handlePlan();
        }
    };

    const toggleRecordSelection = (id) => {
        setSelectedIds(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const suggestions = ROLE_SUGGESTIONS[user?.role] || ROLE_SUGGESTIONS.student;
    const isLoading = planStep > 0;
    const currentStep = STATUS_STEPS[planStep - 1];
    const riskCfg = plan ? (RISK_CONFIG[plan.risk_level] || RISK_CONFIG.LOW) : null;

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* ── Header ── */}
                <div className="page-header animate-in">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 46, height: 46, borderRadius: 13,
                            background: 'linear-gradient(135deg, #7C3AED 0%, #2563EB 100%)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            boxShadow: '0 0 20px rgba(124,58,237,0.4)',
                        }}>
                            <Terminal size={22} color="#fff" />
                        </div>
                        <div>
                            <h1 style={{ margin: 0, fontSize: '1.3rem' }}>Command Console</h1>
                            <p style={{ margin: 0, opacity: 0.6, fontSize: '0.8rem' }}>
                                Natural language → AI plan → Risk review → Controlled execution
                            </p>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{
                            padding: '5px 14px', borderRadius: 20,
                            background: 'rgba(124,58,237,0.15)', color: '#A78BFA',
                            fontSize: '0.75rem', fontWeight: 700,
                        }}>
                            {user?.role?.toUpperCase()} MODE
                        </span>
                        {plan && (
                            <button onClick={handleReset} style={{
                                padding: '6px 14px', borderRadius: 10,
                                border: '1px solid rgba(148,163,184,0.2)',
                                background: 'transparent', color: 'var(--text-muted)',
                                fontSize: '0.8rem', cursor: 'pointer',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}>
                                <RotateCcw size={13} /> New Command
                            </button>
                        )}
                    </div>
                </div>

                {/* ── Command Input Section ── */}
                {!plan && (
                    <div className="glass-card animate-in mb-lg" style={{ padding: '24px 28px' }}>
                        {/* Module selector */}
                        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                            {MODULES.map(m => (
                                <button key={m.value} onClick={() => setModule(m.value)} style={{
                                    padding: '6px 14px', borderRadius: 20,
                                    border: `1px solid ${module === m.value ? '#7C3AED' : 'rgba(148,163,184,0.2)'}`,
                                    background: module === m.value ? 'rgba(124,58,237,0.2)' : 'transparent',
                                    color: module === m.value ? '#A78BFA' : 'var(--text-muted)',
                                    fontSize: '0.8rem', fontWeight: module === m.value ? 700 : 400,
                                    cursor: 'pointer', transition: 'all 0.15s',
                                }}>
                                    {m.emoji} {m.label}
                                </button>
                            ))}
                        </div>

                        {/* Textarea */}
                        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block', fontSize: '0.75rem', fontWeight: 600,
                                    color: 'var(--text-muted)', marginBottom: 8,
                                    textTransform: 'uppercase', letterSpacing: '0.06em',
                                }}>
                                    <Sparkles size={12} style={{ verticalAlign: 'middle', marginRight: 5 }} />
                                    What would you like to do?
                                </label>
                                <textarea
                                    ref={inputRef}
                                    value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder={suggestions[0]}
                                    rows={2}
                                    disabled={isLoading}
                                    style={{
                                        width: '100%', padding: '14px 16px',
                                        background: 'rgba(148,163,184,0.15)',
                                        border: '1px solid rgba(148,163,184,0.3)',
                                        borderRadius: 12, color: 'var(--text-primary)',
                                        fontSize: '0.95rem', resize: 'none', fontFamily: 'inherit',
                                        outline: 'none', transition: 'border-color 0.2s', boxSizing: 'border-box',
                                    }}
                                    onFocus={e => e.target.style.borderColor = '#7C3AED'}
                                    onBlur={e => e.target.style.borderColor = 'rgba(148,163,184,0.2)'}
                                />
                            </div>
                            <button onClick={handlePlan} disabled={!input.trim() || isLoading} style={{
                                padding: '14px 22px', borderRadius: 12, border: 'none',
                                background: isLoading ? 'rgba(124,58,237,0.3)'
                                    : 'linear-gradient(135deg, #7C3AED, #2563EB)',
                                color: '#fff', fontWeight: 700, cursor: isLoading ? 'wait' : 'pointer',
                                display: 'flex', alignItems: 'center', gap: 8,
                                fontSize: '0.9rem', minHeight: 50, whiteSpace: 'nowrap',
                                transition: 'all 0.2s', opacity: (!input.trim() && !isLoading) ? 0.5 : 1,
                            }}>
                                {isLoading ? <Loader size={18} className="spin" /> : <Send size={18} />}
                                {isLoading ? 'Analyzing...' : 'Analyze'}
                            </button>
                        </div>

                        {/* Loading steps */}
                        {isLoading && (
                            <div style={{
                                marginTop: 16, padding: '12px 16px', borderRadius: 10,
                                background: 'rgba(124,58,237,0.08)',
                                border: '1px solid rgba(124,58,237,0.2)',
                            }}>
                                <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
                                    {STATUS_STEPS.map((s, i) => (
                                        <div key={s.id} style={{
                                            display: 'flex', alignItems: 'center', gap: 6,
                                            fontSize: '0.78rem',
                                            color: planStep > i ? '#A78BFA'
                                                : planStep === i + 1 ? '#7C3AED' : 'var(--text-muted)',
                                            opacity: planStep < i + 1 ? 0.4 : 1,
                                            transition: 'all 0.3s',
                                        }}>
                                            {planStep > i + 1 ? (
                                                <CheckCircle size={13} color="#00E676" />
                                            ) : planStep === i + 1 ? (
                                                <Loader size={13} className="spin" />
                                            ) : (
                                                <div style={{
                                                    width: 13, height: 13, borderRadius: '50%',
                                                    border: '2px solid rgba(148,163,184,0.3)',
                                                }} />
                                            )}
                                            {s.label}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Suggestion pills */}
                        {!isLoading && (
                            <div style={{ marginTop: 14 }}>
                                <div style={{
                                    fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 8,
                                    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
                                }}>
                                    Try these commands
                                </div>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                    {suggestions.slice(0, 6).map((s, i) => (
                                        <button key={i} onClick={() => { setInput(s); inputRef.current?.focus(); }} style={{
                                            padding: '5px 12px', borderRadius: 20,
                                            background: 'rgba(148,163,184,0.06)',
                                            border: '1px solid rgba(148,163,184,0.15)',
                                            color: 'var(--text-muted)', fontSize: '0.78rem',
                                            cursor: 'pointer', transition: 'all 0.15s',
                                            whiteSpace: 'nowrap',
                                        }}
                                            onMouseEnter={e => {
                                                e.target.style.background = 'rgba(124,58,237,0.12)';
                                                e.target.style.borderColor = 'rgba(124,58,237,0.3)';
                                                e.target.style.color = '#A78BFA';
                                            }}
                                            onMouseLeave={e => {
                                                e.target.style.background = 'rgba(148,163,184,0.06)';
                                                e.target.style.borderColor = 'rgba(148,163,184,0.15)';
                                                e.target.style.color = 'var(--text-muted)';
                                            }}
                                        >
                                            {s}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Error Banner ── */}
                {error && (
                    <div className="glass-card mb-lg animate-in" style={{
                        borderLeft: '4px solid #FF5252', padding: '14px 20px', color: '#FF8A80',
                        display: 'flex', alignItems: 'flex-start', gap: 10,
                    }}>
                        <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                        <div>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Error</div>
                            <div style={{ fontSize: '0.82rem', opacity: 0.85, marginTop: 2 }}>{error}</div>
                        </div>
                        <button onClick={() => setError('')} style={{
                            marginLeft: 'auto', background: 'none', border: 'none',
                            color: '#FF8A80', cursor: 'pointer', flexShrink: 0,
                        }}><XCircle size={16} /></button>
                    </div>
                )}

                {/* ── Plan Card ── */}
                {plan && !execution && (
                    <div className="animate-in">
                        {/* Plan summary header */}
                        <div className="glass-card mb-lg" style={{ padding: '20px 24px' }}>
                            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                                        <Zap size={16} style={{ color: '#FFB300' }} />
                                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Execution Plan</span>
                                        <IntentBadge intent={plan.intent} />
                                        <RiskBadge level={plan.risk_level} size="lg" />
                                        <span style={{
                                            padding: '3px 8px', borderRadius: 8, fontSize: '0.65rem',
                                            background: 'rgba(100,116,139,0.2)', color: '#94A3B8',
                                            fontFamily: 'monospace',
                                        }}>{plan.plan_id}</span>
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                                        <strong style={{ color: 'var(--text-primary)' }}>Command:</strong> {plan.status === 'clarification_required' ? input : input}
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
                                        <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(148,163,184,0.12)' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>ENTITY</div>
                                            <div style={{ fontWeight: 700, textTransform: 'capitalize', fontSize: '0.9rem' }}>
                                                <Database size={13} style={{ verticalAlign: 'middle', marginRight: 5, opacity: 0.7 }} />
                                                {plan.entity}
                                            </div>
                                        </div>
                                        <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(148,163,184,0.12)' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>AFFECTED RECORDS</div>
                                            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                                                <Activity size={13} style={{ verticalAlign: 'middle', marginRight: 5, opacity: 0.7 }} />
                                                {plan.estimated_impact_count}
                                            </div>
                                        </div>
                                        <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(148,163,184,0.12)' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 6 }}>AI CONFIDENCE</div>
                                            <ConfidenceMeter value={plan.confidence} />
                                        </div>
                                        <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(148,163,184,0.12)' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>STATUS</div>
                                            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: '#A78BFA' }}>
                                                {plan.status?.replace(/_/g, ' ').toUpperCase()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Risk description */}
                            {riskCfg && (
                                <div style={{
                                    marginTop: 14, padding: '10px 14px', borderRadius: 10,
                                    background: riskCfg.bg, borderLeft: `3px solid ${riskCfg.color}`,
                                    display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem',
                                }}>
                                    <Info size={14} style={{ color: riskCfg.color, flexShrink: 0 }} />
                                    <span style={{ color: riskCfg.color }}>{riskCfg.description}</span>
                                </div>
                            )}
                        </div>

                        {/* ── BLOCKED: Permission denied ── */}
                        {!plan.permission?.allowed && !plan.permission?.escalation_required && (
                            <div className="glass-card mb-lg" style={{
                                borderLeft: '4px solid #FF5252', padding: '16px 20px',
                            }}>
                                <div style={{ display: 'flex', gap: 10 }}>
                                    <Lock size={18} style={{ color: '#FF5252', flexShrink: 0 }} />
                                    <div>
                                        <div style={{ fontWeight: 700, color: '#FF8A80', marginBottom: 4 }}>Access Denied</div>
                                        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                            {plan.permission?.reason === 'ROLE_RESTRICTED' &&
                                                'Your role does not have permission to perform this operation.'}
                                            {plan.permission?.reason === 'DEPARTMENT_SCOPE_RESTRICTED' &&
                                                'This operation is restricted to your department scope.'}
                                            {plan.permission?.reason === 'STUDENT_WRITE_RESTRICTED' &&
                                                'Students cannot perform write operations.'}
                                            {!['ROLE_RESTRICTED', 'DEPARTMENT_SCOPE_RESTRICTED', 'STUDENT_WRITE_RESTRICTED'].includes(plan.permission?.reason) &&
                                                (plan.permission?.reason || 'Permission denied.')}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ marginTop: 12 }}>
                                    <button onClick={handleReset} style={{
                                        padding: '8px 20px', borderRadius: 10,
                                        border: '1px solid rgba(148,163,184,0.2)',
                                        background: 'transparent', color: 'var(--text-primary)',
                                        cursor: 'pointer', fontSize: '0.85rem',
                                    }}>
                                        <RotateCcw size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                                        Try a different command
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* ── Clarification Required ── */}
                        {plan.clarification && (
                            <div className="glass-card mb-lg" style={{
                                borderLeft: '4px solid #FFB300', padding: '18px 22px',
                            }}>
                                <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                                    <AlertTriangle size={18} style={{ color: '#FFB300', flexShrink: 0 }} />
                                    <div>
                                        <div style={{ fontWeight: 700, color: '#FFE082', marginBottom: 4 }}>
                                            Clarification Needed
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                            {plan.clarification.question}
                                        </div>
                                        <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                            {plan.clarification.unclear_parts?.map((part, i) => (
                                                <span key={i} style={{
                                                    padding: '2px 8px', borderRadius: 6, fontSize: '0.72rem',
                                                    background: 'rgba(255,179,0,0.15)', color: '#FFB300',
                                                }}>missing: {part}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <input
                                        value={clarification}
                                        onChange={e => setClarification(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleClarify()}
                                        placeholder="Provide clarification..."
                                        style={{
                                            flex: 1, padding: '10px 14px',
                                            background: 'rgba(148,163,184,0.15)',
                                            border: '1px solid rgba(255,179,0,0.3)',
                                            borderRadius: 10, color: 'var(--text-primary)',
                                            fontSize: '0.88rem', outline: 'none',
                                        }}
                                    />
                                    <button onClick={handleClarify} disabled={!clarification.trim() || isLoading} style={{
                                        padding: '10px 18px', borderRadius: 10, border: 'none',
                                        background: 'linear-gradient(135deg, #FFB300, #F57C00)',
                                        color: '#000', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem',
                                    }}>
                                        {isLoading ? <Loader size={15} className="spin" /> : <ArrowRight size={15} />}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* ── Preview of Affected Records ── */}
                        {plan.preview?.affected_records?.length > 0 && (
                            <div className="glass-card mb-lg">
                                <div
                                    style={{ cursor: 'pointer', padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                                    onClick={() => setShowPreview(v => !v)}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: '0.88rem' }}>
                                        <Eye size={15} style={{ color: '#64B5F6' }} />
                                        Affected Records Preview
                                        <span style={{
                                            padding: '2px 8px', borderRadius: 12, fontSize: '0.7rem',
                                            background: 'rgba(100,181,246,0.15)', color: '#64B5F6',
                                        }}>{plan.preview.affected_records.length} records</span>
                                    </div>
                                    {showPreview ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                </div>
                                {showPreview && (
                                    <div style={{ padding: '0 18px 16px', overflowX: 'auto' }}>
                                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                                            <thead>
                                                <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.1)' }}>
                                                    {/* Checkbox column for selectable approval */}
                                                    {(plan.requires_confirmation || plan.requires_senior_approval) && (
                                                        <th style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--text-muted)' }}>
                                                            <input type="checkbox"
                                                                checked={selectedIds.length === plan.preview.affected_records.filter(r => r.id).length}
                                                                onChange={e => {
                                                                    if (e.target.checked) {
                                                                        setSelectedIds(plan.preview.affected_records.map(r => r.id).filter(Boolean));
                                                                    } else {
                                                                        setSelectedIds([]);
                                                                    }
                                                                }}
                                                            />
                                                        </th>
                                                    )}
                                                    {Object.keys(plan.preview.affected_records[0]).slice(0, 8).map(k => (
                                                        <th key={k} style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600 }}>
                                                            {k}
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {plan.preview.affected_records.map((rec, i) => (
                                                    <tr key={i} style={{ borderBottom: '1px solid rgba(148,163,184,0.05)' }}>
                                                        {(plan.requires_confirmation || plan.requires_senior_approval) && (
                                                            <td style={{ padding: '5px 8px' }}>
                                                                <input type="checkbox"
                                                                    checked={selectedIds.includes(rec.id)}
                                                                    onChange={() => toggleRecordSelection(rec.id)}
                                                                />
                                                            </td>
                                                        )}
                                                        {Object.entries(rec).slice(0, 8).map(([k, v]) => (
                                                            <td key={k} style={{ padding: '5px 10px', color: 'var(--text-muted)' }}>
                                                                {v === null ? <em>null</em> : String(v).slice(0, 40)}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        {plan.preview.rollback_plan?.supports_rollback && (
                                            <div style={{ marginTop: 10, fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 6 }}>
                                                <RotateCcw size={12} style={{ flexShrink: 0, marginTop: 1 }} />
                                                {plan.preview.rollback_plan.note}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ── Action Controls ── */}
                        {plan.permission?.allowed && !plan.clarification && (
                            <div className="glass-card mb-lg" style={{ padding: '20px 24px' }}>
                                <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 14, display: 'flex', gap: 8, alignItems: 'center' }}>
                                    <Shield size={15} style={{ color: '#A78BFA' }} />
                                    Execution Control
                                </div>

                                {/* Escalation notice */}
                                {plan.permission?.escalation_required && (
                                    <div style={{
                                        padding: '12px 16px', borderRadius: 10, marginBottom: 14,
                                        background: 'rgba(255,82,82,0.08)', borderLeft: '3px solid #FF5252',
                                        fontSize: '0.83rem', color: '#FF8A80',
                                    }}>
                                        <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                                        This operation requires senior admin approval.
                                    </div>
                                )}

                                {/* Approval comment field */}
                                {(plan.requires_confirmation || plan.requires_senior_approval) && (
                                    <div style={{ marginBottom: 12 }}>
                                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
                                            Comment (optional)
                                        </label>
                                        <input
                                            value={approvalComment}
                                            onChange={e => setApprovalComment(e.target.value)}
                                            placeholder="Reason for this operation..."
                                            style={{
                                                width: '100%', padding: '9px 13px',
                                                background: 'rgba(148,163,184,0.15)',
                                                border: '1px solid rgba(148,163,184,0.3)',
                                                borderRadius: 10, color: 'var(--text-primary)',
                                                fontSize: '0.85rem', outline: 'none', boxSizing: 'border-box',
                                            }}
                                        />
                                    </div>
                                )}

                                {/* 2FA input */}
                                {plan.requires_2fa && (
                                    <div style={{ marginBottom: 14 }}>
                                        <label style={{
                                            fontSize: '0.75rem', color: '#FFB300',
                                            display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontWeight: 600,
                                        }}>
                                            <Lock size={12} /> 2FA / OTP Code Required
                                        </label>
                                        <div style={{ position: 'relative', width: 200 }}>
                                            <input
                                                value={twoFaCode}
                                                onChange={e => setTwoFaCode(e.target.value)}
                                                type={showTwoFa ? 'text' : 'password'}
                                                placeholder="Enter 6-digit code"
                                                maxLength={8}
                                                style={{
                                                    width: '100%', padding: '10px 36px 10px 13px',
                                                    background: 'rgba(255,179,0,0.06)',
                                                    border: '1px solid rgba(255,179,0,0.3)',
                                                    borderRadius: 10, color: 'var(--text-primary)',
                                                    fontSize: '0.9rem', outline: 'none',
                                                    letterSpacing: '0.12em', boxSizing: 'border-box',
                                                }}
                                            />
                                            <button onClick={() => setShowTwoFa(v => !v)} style={{
                                                position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                                                background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                                            }}>
                                                {showTwoFa ? <EyeOff size={14} /> : <Eye size={14} />}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Record selection summary */}
                                {(plan.requires_confirmation || plan.requires_senior_approval) && selectedIds.length > 0 && (
                                    <div style={{ marginBottom: 12, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                        <CheckCircle size={12} style={{ verticalAlign: 'middle', marginRight: 5, color: '#00E676' }} />
                                        {selectedIds.length} of {plan.estimated_impact_count} records selected for execution
                                    </div>
                                )}

                                {/* Action buttons */}
                                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                    {/* Medium risk: direct confirm */}
                                    {plan.requires_confirmation && !plan.requires_senior_approval && (
                                        <>
                                            <button onClick={() => handleDecision('REJECT')} disabled={executing} style={{
                                                padding: '10px 22px', borderRadius: 11,
                                                border: '1px solid rgba(255,82,82,0.4)',
                                                background: 'transparent', color: '#FF8A80',
                                                fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem',
                                                display: 'flex', alignItems: 'center', gap: 7,
                                            }}>
                                                <XCircle size={15} /> Reject
                                            </button>
                                            <button onClick={() => handleDecision('APPROVE')} disabled={executing} style={{
                                                padding: '10px 22px', borderRadius: 11, border: 'none',
                                                background: executing ? 'rgba(0,230,118,0.3)' : 'linear-gradient(135deg, #00E676, #00BCD4)',
                                                color: '#000', fontWeight: 700, cursor: executing ? 'wait' : 'pointer',
                                                fontSize: '0.85rem',
                                                display: 'flex', alignItems: 'center', gap: 7,
                                            }}>
                                                {executing ? <Loader size={15} className="spin" /> : <CheckCircle size={15} />}
                                                {executing ? 'Executing...' : 'Confirm & Execute'}
                                            </button>
                                        </>
                                    )}

                                    {/* High risk: senior approval */}
                                    {plan.requires_senior_approval && (
                                        <>
                                            <button onClick={() => handleDecision('REJECT')} disabled={executing} style={{
                                                padding: '10px 22px', borderRadius: 11,
                                                border: '1px solid rgba(255,82,82,0.4)',
                                                background: 'transparent', color: '#FF8A80',
                                                fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem',
                                                display: 'flex', alignItems: 'center', gap: 7,
                                            }}>
                                                <XCircle size={15} /> Reject
                                            </button>
                                            <button onClick={() => handleDecision('ESCALATE')} disabled={executing} style={{
                                                padding: '10px 22px', borderRadius: 11,
                                                border: '1px solid rgba(255,179,0,0.4)',
                                                background: 'transparent', color: '#FFB300',
                                                fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem',
                                                display: 'flex', alignItems: 'center', gap: 7,
                                            }}>
                                                <AlertTriangle size={15} /> Escalate
                                            </button>
                                            <button
                                                onClick={() => handleDecision('APPROVE')}
                                                disabled={executing || (plan.requires_2fa && !twoFaCode.trim())}
                                                style={{
                                                    padding: '10px 22px', borderRadius: 11, border: 'none',
                                                    background: executing ? 'rgba(255,82,82,0.3)' : 'linear-gradient(135deg, #FF5252, #E91E63)',
                                                    color: '#fff', fontWeight: 700,
                                                    cursor: (executing || (plan.requires_2fa && !twoFaCode.trim())) ? 'not-allowed' : 'pointer',
                                                    fontSize: '0.85rem',
                                                    display: 'flex', alignItems: 'center', gap: 7,
                                                    opacity: (plan.requires_2fa && !twoFaCode.trim()) ? 0.5 : 1,
                                                }}>
                                                {executing ? <Loader size={15} className="spin" /> : <Shield size={15} />}
                                                {executing ? 'Approving...' : 'Approve & Execute'}
                                            </button>
                                        </>
                                    )}

                                    {/* LOW risk: already auto-executed (should not reach here normally) */}
                                    {!plan.requires_confirmation && !plan.requires_senior_approval && plan.status === 'awaiting_confirmation' && (
                                        <button onClick={handleDirectExecute} disabled={executing} style={{
                                            padding: '10px 22px', borderRadius: 11, border: 'none',
                                            background: 'linear-gradient(135deg, #00E676, #00BCD4)',
                                            color: '#000', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem',
                                            display: 'flex', alignItems: 'center', gap: 7,
                                        }}>
                                            {executing ? <Loader size={15} className="spin" /> : <Zap size={15} />}
                                            Execute
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Execution Results ── */}
                {execution && (
                    <div className="glass-card animate-in mb-lg" style={{ padding: '22px 26px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                            <h2 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, fontSize: '1rem' }}>
                                {execution.status === 'executed' ? (
                                    <CheckCircle size={20} style={{ color: '#00E676' }} />
                                ) : execution.status === 'rolled_back' ? (
                                    <RotateCcw size={20} style={{ color: '#FFB300' }} />
                                ) : (
                                    <XCircle size={20} style={{ color: '#FF5252' }} />
                                )}
                                Execution {execution.status === 'executed' ? 'Complete' : execution.status === 'rolled_back' ? 'Rolled Back' : 'Failed'}
                            </h2>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                {execution.execution_id}
                            </span>
                        </div>

                        {/* Stats */}
                        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 16 }}>
                            {[
                                { label: 'Records Affected', value: execution.affected_count ?? 0, color: '#64B5F6' },
                                { label: 'Status', value: execution.status?.toUpperCase(), color: execution.status === 'executed' ? '#00E676' : execution.status === 'rolled_back' ? '#FFB300' : '#FF5252' },
                            ].map(s => (
                                <div key={s.label} style={{ padding: '10px 16px', borderRadius: 10, background: 'rgba(148,163,184,0.12)' }}>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{s.label}</div>
                                    <div style={{ fontWeight: 700, color: s.color }}>{s.value}</div>
                                </div>
                            ))}
                        </div>

                        {execution.error && (
                            <div style={{
                                padding: '10px 14px', borderRadius: 10, marginBottom: 14,
                                background: 'rgba(255,82,82,0.08)', color: '#FF8A80', fontSize: '0.83rem',
                                borderLeft: '3px solid #FF5252',
                            }}>
                                {execution.error}
                            </div>
                        )}

                        {/* Before/After diff */}
                        {execution.status === 'executed' &&
                            execution.before_state?.length > 0 &&
                            execution.after_state?.length > 0 &&
                            JSON.stringify(execution.before_state) !== JSON.stringify(execution.after_state) && (
                                <div style={{ marginBottom: 14 }}>
                                    <div
                                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontSize: '0.82rem', fontWeight: 600 }}
                                        onClick={() => setShowDiff(v => !v)}
                                    >
                                        <FileText size={14} style={{ color: '#64B5F6' }} />
                                        Changes Made
                                        {showDiff ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                                    </div>
                                    {showDiff && execution.before_state.map((before, idx) => {
                                        const after = execution.after_state[idx] || {};
                                        const fields = [...new Set([...Object.keys(before), ...Object.keys(after)])];
                                        const changedFields = fields.filter(f => JSON.stringify(before[f]) !== JSON.stringify(after[f]));
                                        if (changedFields.length === 0) return null;
                                        return (
                                            <div key={idx} style={{
                                                marginBottom: 8, borderRadius: 8, overflow: 'hidden',
                                                border: '1px solid rgba(148,163,184,0.1)',
                                            }}>
                                                <div style={{ padding: '6px 12px', background: 'rgba(148,163,184,0.12)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                                    Record #{before.id || (idx + 1)}
                                                </div>
                                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                    <thead><tr style={{ background: 'rgba(148,163,184,0.08)' }}>
                                                        {['Field', 'Before', 'After'].map(h => (
                                                            <th key={h} style={{ padding: '5px 10px', textAlign: 'left', fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>{h}</th>
                                                        ))}
                                                    </tr></thead>
                                                    <tbody>
                                                        {changedFields.map(f => (
                                                            <DiffRow key={f} before={before} after={after} field={f} />
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                        {/* Rollback button */}
                        <div style={{ display: 'flex', gap: 10 }}>
                            {execution.status === 'executed' && ['UPDATE', 'DELETE', 'CREATE'].includes(plan?.intent) && (
                                <button onClick={handleRollback} disabled={rollingBack} style={{
                                    padding: '9px 18px', borderRadius: 10,
                                    border: '1px solid rgba(255,179,0,0.3)',
                                    background: 'transparent', color: '#FFB300',
                                    fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
                                    display: 'flex', alignItems: 'center', gap: 6,
                                }}>
                                    {rollingBack ? <Loader size={14} className="spin" /> : <RotateCcw size={14} />}
                                    {rollingBack ? 'Rolling back...' : 'Rollback Changes'}
                                </button>
                            )}
                            <button onClick={handleReset} style={{
                                padding: '9px 18px', borderRadius: 10,
                                border: '1px solid rgba(148,163,184,0.2)',
                                background: 'transparent', color: 'var(--text-primary)',
                                fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}>
                                <Terminal size={14} /> New Command
                            </button>
                        </div>
                    </div>
                )}

                {/* ── Audit / History ── */}
                <div className="glass-card animate-in mb-lg">
                    <div
                        style={{ cursor: 'pointer', padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                        onClick={() => setShowHistory(v => !v)}
                    >
                        <h2 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, fontSize: '0.95rem' }}>
                            <History size={18} style={{ color: '#64748B' }} />
                            Audit Trail
                            {history.length > 0 && (
                                <span style={{
                                    padding: '2px 8px', borderRadius: 12, fontSize: '0.7rem',
                                    background: 'rgba(100,116,139,0.2)', color: '#94A3B8',
                                }}>{history.length}</span>
                            )}
                        </h2>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            {showHistory && (
                                <button onClick={e => { e.stopPropagation(); loadHistory(); }} style={{
                                    background: 'none', border: 'none', color: 'var(--text-muted)',
                                    cursor: 'pointer', padding: 4,
                                }}>
                                    <RefreshCw size={14} />
                                </button>
                            )}
                            {showHistory ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </div>
                    </div>

                    {showHistory && (
                        <div style={{ padding: '0 20px 20px' }}>
                            {/* Filters */}
                            <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
                                {[
                                    { key: 'risk_level', label: 'Risk', options: ['', 'LOW', 'MEDIUM', 'HIGH'] },
                                    { key: 'operation_type', label: 'Operation', options: ['', 'READ', 'CREATE', 'UPDATE', 'DELETE', 'ANALYZE'] },
                                    { key: 'module', label: 'Module', options: ['', 'nlp', 'finance', 'hr', 'predictions'] },
                                ].map(f => (
                                    <select
                                        key={f.key}
                                        value={historyFilter[f.key]}
                                        onChange={e => setHistoryFilter(prev => ({ ...prev, [f.key]: e.target.value }))}
                                        style={{
                                            padding: '6px 12px', borderRadius: 8, fontSize: '0.8rem',
                                            background: 'rgba(148,163,184,0.15)',
                                            border: '1px solid rgba(148,163,184,0.25)',
                                            color: 'var(--text-primary)', outline: 'none',
                                        }}
                                    >
                                        {f.options.map(o => (
                                            <option key={o} value={o}>{o || `All ${f.label}`}</option>
                                        ))}
                                    </select>
                                ))}
                                <button onClick={loadHistory} style={{
                                    padding: '6px 14px', borderRadius: 8, fontSize: '0.8rem',
                                    background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)',
                                    color: '#A78BFA', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: 5,
                                }}>
                                    <Filter size={12} /> Apply
                                </button>
                            </div>

                            {loadingHistory ? (
                                <div style={{ textAlign: 'center', padding: 20, opacity: 0.5 }}>
                                    <Loader size={20} className="spin" />
                                </div>
                            ) : history.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '24px 0', opacity: 0.45, fontSize: '0.85rem' }}>
                                    No operations recorded yet. Try a command above!
                                </div>
                            ) : (
                                <div style={{ overflowX: 'auto' }}>
                                    <table className="data-table" style={{ fontSize: '0.78rem' }}>
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Operation</th>
                                                <th>Entity</th>
                                                <th>Module</th>
                                                <th>Event</th>
                                                <th>Risk</th>
                                                <th>Role</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {history.map((log, i) => {
                                                const rCfg = RISK_CONFIG[log.risk_level] || RISK_CONFIG.LOW;
                                                const intentColor = INTENT_COLORS[log.operation_type] || '#94A3B8';
                                                const evtColor = log.event_type === 'executed' ? '#00E676'
                                                    : log.event_type === 'failed' ? '#FF5252'
                                                        : log.event_type === 'rollback' ? '#FFB300'
                                                            : '#94A3B8';
                                                return (
                                                    <tr key={i}>
                                                        <td style={{ whiteSpace: 'nowrap', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                                            {log.created_at ? new Date(log.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
                                                        </td>
                                                        <td>
                                                            <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem', background: `${intentColor}18`, color: intentColor, fontWeight: 700 }}>
                                                                {log.operation_type}
                                                            </span>
                                                        </td>
                                                        <td style={{ color: 'var(--text-muted)' }}>{log.intent_payload?.entity || '—'}</td>
                                                        <td>
                                                            <span style={{ padding: '2px 6px', borderRadius: 6, fontSize: '0.68rem', background: 'rgba(148,163,184,0.1)', color: '#94A3B8' }}>
                                                                {log.module}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem', background: `${evtColor}18`, color: evtColor, fontWeight: 600 }}>
                                                                {log.event_type}
                                                            </span>
                                                        </td>
                                                        <td><RiskBadge level={log.risk_level} /></td>
                                                        <td style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>{log.role}</td>
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
            `}</style>
        </div>
    );
}
