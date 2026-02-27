/**
 * CampusIQ — Command Console (Pure Chat Interface)
 * Message → Execute → Result. No approval gates.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import api from '../services/api';
import {
    Sparkles, Send, CheckCircle, XCircle, AlertTriangle,
    Shield, Zap, History, RotateCcw, Terminal,
    Loader, ChevronDown, ChevronUp, Eye, EyeOff,
    Database, Info, RefreshCw, Filter,
    TrendingUp, Activity, FileText,
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
        'Analyze attendance trends for semester 4',
        'Update CGPA for students in section A',
        'Show employees hired this year',
    ],
    faculty: [
        'Show my students with low attendance',
        'List all students in my Data Structures course',
        'How many students are at risk in my courses?',
        'Show predicted grades for my class',
        'Analyze attendance for course CS301',
    ],
    student: [
        'Show my attendance across all courses',
        'What is my current CGPA?',
        'Show my predicted grades',
        'Show my fee balance',
    ],
};

const RISK_BADGE = {
    LOW:    { color: '#00E676', bg: 'rgba(0,230,118,0.12)', label: 'Low Risk' },
    MEDIUM: { color: '#FFB300', bg: 'rgba(255,179,0,0.12)', label: 'Medium Risk' },
    HIGH:   { color: '#FF5252', bg: 'rgba(255,82,82,0.12)', label: 'High Risk' },
};

const INTENT_COLOR = {
    READ: '#64B5F6', ANALYZE: '#CE93D8', CREATE: '#A5D6A7',
    UPDATE: '#FFE082', DELETE: '#EF9A9A',
};

// ─── Component ──────────────────────────────────────────────────────────────

export default function CopilotPanel() {
    const { user } = useAuth();
    const location = useLocation();
    const role = user?.role || 'student';

    // Chat state
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [module, setModule] = useState('nlp');
    const [sending, setSending] = useState(false);

    // Audit trail
    const [history, setHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [historyFilter, setHistoryFilter] = useState({ risk_level: '', operation_type: '', module: '' });
    const [loadingHistory, setLoadingHistory] = useState(false);

    const inputRef = useRef(null);
    const chatEndRef = useRef(null);

    // Auto-fill from navigation
    useEffect(() => {
        const q = new URLSearchParams(location.search).get('q');
        if (q) setInput(q);
    }, [location.search]);

    // Auto-scroll chat
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // ─── Send message ────────────────────────────────────
    const handleSend = useCallback(async () => {
        const text = input.trim();
        if (!text || sending) return;

        const userMsg = { role: 'user', text, module, ts: new Date() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setSending(true);

        try {
            const data = await api.operationalAIExecute(text, module);
            const botMsg = {
                role: 'bot',
                ts: new Date(),
                ...data,
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'bot', ts: new Date(),
                status: 'error',
                message: err.message || 'Something went wrong. Please try again.',
            }]);
        } finally {
            setSending(false);
            inputRef.current?.focus();
        }
    }, [input, module, sending]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // ─── Rollback ────────────────────────────────────────
    const handleRollback = useCallback(async (executionId, msgIdx) => {
        try {
            const rb = await api.operationalAIRollback(executionId);
            setMessages(prev => prev.map((m, i) =>
                i === msgIdx ? { ...m, rolledBack: true, rollbackResult: rb } : m
            ));
        } catch (err) {
            setMessages(prev => prev.map((m, i) =>
                i === msgIdx ? { ...m, rollbackError: err.message } : m
            ));
        }
    }, []);

    // ─── Audit history ───────────────────────────────────
    const loadHistory = useCallback(async () => {
        setLoadingHistory(true);
        try {
            const params = {};
            if (historyFilter.risk_level) params.risk_level = historyFilter.risk_level;
            if (historyFilter.operation_type) params.operation_type = historyFilter.operation_type;
            if (historyFilter.module) params.module = historyFilter.module;
            params.limit = 50;
            const data = await api.operationalAIAudit(params);
            setHistory(Array.isArray(data) ? data : []);
        } catch { setHistory([]); }
        setLoadingHistory(false);
    }, [historyFilter]);

    useEffect(() => { if (showHistory) loadHistory(); }, [showHistory, loadHistory]);

    // ─── Suggestion click ────────────────────────────────
    const handleSuggestion = (text) => {
        setInput(text);
        inputRef.current?.focus();
    };

    // ─── Render helpers ──────────────────────────────────

    const renderBotMessage = (msg, idx) => {
        const risk = RISK_BADGE[msg.risk_level] || RISK_BADGE.LOW;
        const intentColor = INTENT_COLOR[msg.intent] || '#94A3B8';

        if (msg.status === 'error' || msg.status === 'failed') {
            return (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                    <XCircle size={18} color="#FF5252" style={{ marginTop: 2, flexShrink: 0 }} />
                    <div>
                        <div style={{ color: '#FF8A80', fontSize: 14 }}>{msg.message}</div>
                        {msg.error && msg.error !== msg.message && (
                            <details style={{ marginTop: 6 }}>
                                <summary style={{ color: '#94A3B8', fontSize: 12, cursor: 'pointer' }}>Error details</summary>
                                <pre style={{ color: '#EF9A9A', fontSize: 11, marginTop: 4, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                                    {msg.error}
                                </pre>
                            </details>
                        )}
                    </div>
                </div>
            );
        }

        if (msg.status === 'denied') {
            return (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                    <Shield size={18} color="#FF5252" style={{ marginTop: 2, flexShrink: 0 }} />
                    <div style={{ color: '#FF8A80', fontSize: 14 }}>{msg.message}</div>
                </div>
            );
        }

        if (msg.status === 'clarification_needed') {
            return (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                    <AlertTriangle size={18} color="#FFB300" style={{ marginTop: 2, flexShrink: 0 }} />
                    <div>
                        <div style={{ color: '#FFE082', fontSize: 14, fontWeight: 600 }}>Need more details</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{msg.message}</div>
                        {msg.confidence != null && (
                            <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 4 }}>
                                Confidence: {(msg.confidence * 100).toFixed(0)}%
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        if (msg.status === 'validation_error') {
            return (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                    <AlertTriangle size={18} color="#FF5252" style={{ marginTop: 2, flexShrink: 0 }} />
                    <div>
                        <div style={{ color: '#FF8A80', fontSize: 14, fontWeight: 600 }}>{msg.message}</div>
                        {msg.errors?.map((e, i) => (
                            <div key={i} style={{ color: '#EF9A9A', fontSize: 13 }}>• {e}</div>
                        ))}
                    </div>
                </div>
            );
        }

        // Executed successfully
        return (
            <div style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                    <CheckCircle size={18} color="#00E676" style={{ flexShrink: 0 }} />
                    <span style={{
                        fontSize: 12, padding: '2px 8px', borderRadius: 6,
                        background: `${intentColor}22`, color: intentColor, fontWeight: 600,
                    }}>{msg.intent}</span>
                    <span style={{
                        fontSize: 12, padding: '2px 8px', borderRadius: 6,
                        background: risk.bg, color: risk.color,
                    }}>{risk.label}</span>
                    {msg.affected_count != null && (
                        <span style={{ fontSize: 12, color: '#94A3B8' }}>
                            {msg.affected_count} record{msg.affected_count !== 1 ? 's' : ''}
                        </span>
                    )}
                </div>

                <div style={{ fontSize: 14, color: 'var(--text-primary)', marginBottom: 6 }}>
                    {msg.message}
                </div>

                {/* Confidence indicator */}
                {msg.confidence != null && (
                    <div style={{
                        fontSize: 11, color: '#94A3B8', marginBottom: 6,
                        display: 'flex', alignItems: 'center', gap: 6,
                    }}>
                        <div style={{
                            width: 60, height: 4, borderRadius: 2,
                            background: 'rgba(148,163,184,0.15)',
                            overflow: 'hidden',
                        }}>
                            <div style={{
                                width: `${Math.round(msg.confidence * 100)}%`,
                                height: '100%',
                                borderRadius: 2,
                                background: msg.confidence > 0.8 ? '#00E676' : msg.confidence > 0.5 ? '#FFB300' : '#FF5252',
                            }} />
                        </div>
                        {Math.round(msg.confidence * 100)}% confidence
                    </div>
                )}

                {/* Data table for READ/ANALYZE */}
                {msg.after_state && msg.after_state.length > 0 && msg.intent === 'READ' && (
                    <DataTable rows={msg.after_state} />
                )}

                {/* Analysis summary */}
                {msg.analysis && (
                    <AnalysisSummary analysis={msg.analysis} />
                )}

                {/* Diff for UPDATE */}
                {msg.intent === 'UPDATE' && msg.before_state?.length > 0 && (
                    <DiffView before={msg.before_state} after={msg.after_state} />
                )}

                {/* Rollback button */}
                {msg.execution_id && !msg.rolledBack && msg.intent !== 'READ' && msg.intent !== 'ANALYZE' && (
                    <button
                        onClick={() => handleRollback(msg.execution_id, idx)}
                        style={{
                            display: 'inline-flex', alignItems: 'center', gap: 6,
                            padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(255,179,0,0.3)',
                            background: 'rgba(255,179,0,0.08)', color: '#FFB300',
                            cursor: 'pointer', fontSize: 13, marginTop: 6,
                        }}
                    >
                        <RotateCcw size={14} /> Undo
                    </button>
                )}
                {msg.rolledBack && (
                    <div style={{ fontSize: 13, color: '#FFB300', marginTop: 6, display: 'flex', gap: 6, alignItems: 'center' }}>
                        <RotateCcw size={14} /> Rolled back successfully
                    </div>
                )}
                {msg.rollbackError && (
                    <div style={{ fontSize: 13, color: '#FF5252', marginTop: 6 }}>
                        Rollback failed: {msg.rollbackError}
                    </div>
                )}
            </div>
        );
    };

    // ─── Render ──────────────────────────────────────────

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

                {/* Header */}
                <div className="page-header" style={{ flexShrink: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 40, height: 40, borderRadius: 12,
                            background: 'linear-gradient(135deg, #7C3AED, #2563EB)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <Terminal size={20} color="white" />
                        </div>
                        <div>
                            <h1 style={{ margin: 0, fontSize: 22 }}>Command Console</h1>
                            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>
                                Type a command — it runs immediately
                            </p>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{
                            fontSize: 12, padding: '4px 10px', borderRadius: 8,
                            background: 'rgba(124,58,237,0.12)', color: '#A78BFA',
                            textTransform: 'capitalize',
                        }}>{role}</span>
                        <button
                            onClick={() => setShowHistory(h => !h)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 6,
                                padding: '6px 12px', borderRadius: 8,
                                border: '1px solid rgba(148,163,184,0.2)',
                                background: showHistory ? 'rgba(124,58,237,0.12)' : 'transparent',
                                color: showHistory ? '#A78BFA' : 'var(--text-muted)',
                                cursor: 'pointer', fontSize: 13,
                            }}
                        >
                            <History size={14} /> Audit
                        </button>
                    </div>
                </div>

                {/* Chat area */}
                <div style={{
                    flex: 1, overflowY: 'auto', padding: '16px 20px',
                    display: 'flex', flexDirection: 'column', gap: 12,
                }}>
                    {messages.length === 0 && (
                        <div style={{
                            flex: 1, display: 'flex', flexDirection: 'column',
                            alignItems: 'center', justifyContent: 'center', gap: 16,
                        }}>
                            <Sparkles size={36} color="#7C3AED" />
                            <div style={{ fontSize: 16, color: 'var(--text-muted)', textAlign: 'center' }}>
                                Ask anything about your campus data
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 600 }}>
                                {(ROLE_SUGGESTIONS[role] || ROLE_SUGGESTIONS.student).slice(0, 6).map((s, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSuggestion(s)}
                                        style={{
                                            padding: '8px 14px', borderRadius: 20,
                                            border: '1px solid rgba(148,163,184,0.2)',
                                            background: 'rgba(148,163,184,0.06)',
                                            color: 'var(--text-muted)', cursor: 'pointer',
                                            fontSize: 13, transition: 'all 0.15s',
                                        }}
                                        onMouseEnter={e => { e.target.style.borderColor = '#7C3AED44'; e.target.style.color = '#A78BFA'; }}
                                        onMouseLeave={e => { e.target.style.borderColor = 'rgba(148,163,184,0.2)'; e.target.style.color = 'var(--text-muted)'; }}
                                    >{s}</button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div key={idx} style={{
                            display: 'flex',
                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        }}>
                            <div style={{
                                maxWidth: msg.role === 'user' ? '70%' : '90%',
                                padding: '10px 16px',
                                borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                                background: msg.role === 'user'
                                    ? 'linear-gradient(135deg, #7C3AED, #2563EB)'
                                    : 'rgba(15,23,42,0.6)',
                                border: msg.role === 'user' ? 'none' : '1px solid rgba(148,163,184,0.12)',
                                color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                                fontSize: 14,
                            }}>
                                {msg.role === 'user' ? (
                                    <div>
                                        {msg.text}
                                        <div style={{ fontSize: 11, opacity: 0.7, marginTop: 4 }}>
                                            {MODULES.find(m => m.value === msg.module)?.emoji} {MODULES.find(m => m.value === msg.module)?.label}
                                        </div>
                                    </div>
                                ) : renderBotMessage(msg, idx)}
                            </div>
                        </div>
                    ))}

                    {sending && (
                        <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                            <div style={{
                                padding: '12px 16px', borderRadius: '16px 16px 16px 4px',
                                background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(148,163,184,0.12)',
                                display: 'flex', gap: 8, alignItems: 'center', color: '#94A3B8',
                            }}>
                                <Loader size={16} className="spin" /> Executing...
                            </div>
                        </div>
                    )}

                    <div ref={chatEndRef} />
                </div>

                {/* Input area */}
                <div style={{
                    flexShrink: 0, padding: '12px 20px 16px',
                    borderTop: '1px solid rgba(148,163,184,0.1)',
                    background: 'rgba(15,23,42,0.3)',
                }}>
                    {/* Module pills */}
                    <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
                        {MODULES.map(m => (
                            <button
                                key={m.value}
                                onClick={() => setModule(m.value)}
                                style={{
                                    padding: '4px 12px', borderRadius: 16, fontSize: 12,
                                    border: `1px solid ${module === m.value ? '#7C3AED44' : 'rgba(148,163,184,0.15)'}`,
                                    background: module === m.value ? 'rgba(124,58,237,0.12)' : 'transparent',
                                    color: module === m.value ? '#A78BFA' : 'var(--text-muted)',
                                    cursor: 'pointer', transition: 'all 0.15s',
                                }}
                            >{m.emoji} {m.label}</button>
                        ))}
                    </div>

                    {/* Input + Send */}
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Type a command... (e.g. Show all students with CGPA below 6)"
                            rows={1}
                            style={{
                                flex: 1, padding: '10px 14px', borderRadius: 12,
                                border: '1px solid rgba(148,163,184,0.2)',
                                background: 'rgba(15,23,42,0.4)',
                                color: 'var(--text-primary)', fontSize: 14,
                                resize: 'none', outline: 'none', fontFamily: 'inherit',
                                minHeight: 42, maxHeight: 120,
                            }}
                            onFocus={e => e.target.style.borderColor = '#7C3AED55'}
                            onBlur={e => e.target.style.borderColor = 'rgba(148,163,184,0.2)'}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || sending}
                            style={{
                                width: 42, height: 42, borderRadius: 12, border: 'none',
                                background: input.trim() ? 'linear-gradient(135deg, #7C3AED, #2563EB)' : 'rgba(148,163,184,0.1)',
                                color: input.trim() ? 'white' : '#64748B',
                                cursor: input.trim() ? 'pointer' : 'not-allowed',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.15s',
                            }}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>

                {/* Audit trail slide-out */}
                {showHistory && (
                    <div style={{
                        position: 'fixed', top: 0, right: 0, bottom: 0, width: 440,
                        background: 'rgba(10,15,30,0.98)', borderLeft: '1px solid rgba(148,163,184,0.12)',
                        zIndex: 100, display: 'flex', flexDirection: 'column',
                        boxShadow: '-4px 0 20px rgba(0,0,0,0.4)',
                    }}>
                        <div style={{
                            padding: '16px 20px', borderBottom: '1px solid rgba(148,163,184,0.1)',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <History size={18} color="#A78BFA" />
                                <span style={{ fontWeight: 600, fontSize: 16 }}>Audit Trail</span>
                            </div>
                            <button
                                onClick={() => setShowHistory(false)}
                                style={{
                                    background: 'none', border: 'none', color: 'var(--text-muted)',
                                    cursor: 'pointer', fontSize: 20, padding: 4,
                                }}
                            >✕</button>
                        </div>

                        {/* Filters */}
                        <div style={{ padding: '10px 20px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <select value={historyFilter.risk_level} onChange={e => setHistoryFilter(f => ({ ...f, risk_level: e.target.value }))}
                                style={filterSelectStyle}>
                                <option value="">All Risk</option>
                                <option value="LOW">Low</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HIGH">High</option>
                            </select>
                            <select value={historyFilter.operation_type} onChange={e => setHistoryFilter(f => ({ ...f, operation_type: e.target.value }))}
                                style={filterSelectStyle}>
                                <option value="">All Ops</option>
                                <option value="READ">Read</option>
                                <option value="CREATE">Create</option>
                                <option value="UPDATE">Update</option>
                                <option value="DELETE">Delete</option>
                                <option value="ANALYZE">Analyze</option>
                            </select>
                            <button onClick={loadHistory} style={{
                                padding: '4px 10px', borderRadius: 6, border: '1px solid rgba(148,163,184,0.2)',
                                background: 'rgba(124,58,237,0.12)', color: '#A78BFA',
                                cursor: 'pointer', fontSize: 12,
                            }}>
                                {loadingHistory ? <Loader size={12} className="spin" /> : <RefreshCw size={12} />}
                            </button>
                        </div>

                        {/* History list */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px 16px' }}>
                            {history.length === 0 && (
                                <div style={{ textAlign: 'center', color: '#64748B', padding: 20, fontSize: 13 }}>
                                    No audit entries found
                                </div>
                            )}
                            {history.map((h, i) => {
                                const risk = RISK_BADGE[h.risk_level] || RISK_BADGE.LOW;
                                const evtColor = h.event_type === 'executed' ? '#00E676'
                                    : h.event_type === 'failed' ? '#FF5252'
                                    : h.event_type === 'rollback' ? '#FFB300'
                                    : '#94A3B8';
                                return (
                                    <div key={i} style={{
                                        padding: '10px 12px', borderRadius: 8, marginBottom: 6,
                                        border: '1px solid rgba(148,163,184,0.08)',
                                        background: 'rgba(15,23,42,0.4)',
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                            <span style={{ fontSize: 12, color: evtColor, fontWeight: 600 }}>
                                                {h.event_type}
                                            </span>
                                            <span style={{ fontSize: 11, color: '#64748B' }}>
                                                {h.created_at ? new Date(h.created_at).toLocaleString() : ''}
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                            <span style={{
                                                fontSize: 11, padding: '1px 6px', borderRadius: 4,
                                                background: `${INTENT_COLOR[h.operation_type] || '#94A3B8'}22`,
                                                color: INTENT_COLOR[h.operation_type] || '#94A3B8',
                                            }}>{h.operation_type}</span>
                                            <span style={{
                                                fontSize: 11, padding: '1px 6px', borderRadius: 4,
                                                background: risk.bg, color: risk.color,
                                            }}>{h.risk_level}</span>
                                            <span style={{ fontSize: 11, color: '#94A3B8' }}>{h.module}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </main>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                .spin { animation: spin 1s linear infinite; }
            `}</style>
        </div>
    );
}

// ─── Sub-components ─────────────────────────────────────────────────────────

const filterSelectStyle = {
    padding: '4px 8px', borderRadius: 6, fontSize: 12,
    border: '1px solid rgba(148,163,184,0.2)',
    background: 'rgba(15,23,42,0.6)', color: 'var(--text-muted)',
    outline: 'none',
};

function DataTable({ rows }) {
    if (!rows || rows.length === 0) return null;
    const headers = Object.keys(rows[0]).filter(h => h !== 'hashed_password');
    const display = rows.slice(0, 50);

    return (
        <div style={{ overflowX: 'auto', marginTop: 8, borderRadius: 8, border: '1px solid rgba(148,163,184,0.1)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                    <tr>
                        {headers.map(h => (
                            <th key={h} style={{
                                padding: '6px 10px', textAlign: 'left', fontWeight: 600,
                                borderBottom: '1px solid rgba(148,163,184,0.15)',
                                color: '#94A3B8', whiteSpace: 'nowrap',
                                position: 'sticky', top: 0,
                                background: 'rgba(15,23,42,0.95)',
                            }}>{h.replace(/_/g, ' ')}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {display.map((row, i) => (
                        <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(148,163,184,0.03)' }}>
                            {headers.map(h => (
                                <td key={h} style={{
                                    padding: '5px 10px', borderBottom: '1px solid rgba(148,163,184,0.06)',
                                    color: 'var(--text-primary)', whiteSpace: 'nowrap',
                                    maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis',
                                }}>{String(row[h] ?? '')}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {rows.length > 50 && (
                <div style={{ padding: 8, textAlign: 'center', fontSize: 12, color: '#94A3B8' }}>
                    Showing 50 of {rows.length} records
                </div>
            )}
        </div>
    );
}

function AnalysisSummary({ analysis }) {
    if (!analysis) return null;
    const { count, aggregations = {}, sample = [] } = analysis;

    return (
        <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 13, color: '#CE93D8', marginBottom: 6 }}>
                <Activity size={14} style={{ display: 'inline', verticalAlign: -2 }} /> {count} records analyzed
            </div>
            {Object.entries(aggregations).map(([field, stats]) => (
                <div key={field} style={{
                    padding: '6px 10px', borderRadius: 6, marginBottom: 4,
                    background: 'rgba(206,147,216,0.06)', border: '1px solid rgba(206,147,216,0.1)',
                    fontSize: 12,
                }}>
                    <strong style={{ color: '#CE93D8' }}>{field}</strong>:
                    <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>
                        avg {stats.avg} · min {stats.min} · max {stats.max} · sum {stats.sum}
                    </span>
                </div>
            ))}
            {sample.length > 0 && <DataTable rows={sample} />}
        </div>
    );
}

function DiffView({ before, after }) {
    const [show, setShow] = useState(false);
    if (!before || !after || before.length === 0) return null;

    return (
        <div style={{ marginTop: 8 }}>
            <button onClick={() => setShow(s => !s)} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '4px 10px', borderRadius: 6,
                border: '1px solid rgba(148,163,184,0.15)',
                background: 'transparent', color: '#64B5F6',
                cursor: 'pointer', fontSize: 12,
            }}>
                {show ? <EyeOff size={12} /> : <Eye size={12} />}
                {show ? 'Hide' : 'Show'} Changes
            </button>
            {show && (
                <div style={{ marginTop: 6, overflowX: 'auto' }}>
                    {before.map((b, i) => {
                        const a = after[i] || {};
                        const changed = Object.keys(b).filter(k => b[k] !== a[k] && k !== 'id');
                        if (changed.length === 0) return null;
                        return (
                            <div key={i} style={{
                                padding: '6px 10px', borderRadius: 6, marginBottom: 4,
                                border: '1px solid rgba(148,163,184,0.1)', fontSize: 12,
                            }}>
                                <span style={{ color: '#94A3B8' }}>ID {b.id}: </span>
                                {changed.map(k => (
                                    <span key={k} style={{ marginRight: 12 }}>
                                        {k}: <span style={{ color: '#EF9A9A' }}>{String(b[k])}</span>
                                        {' → '}
                                        <span style={{ color: '#A5D6A7' }}>{String(a[k])}</span>
                                    </span>
                                ))}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
