import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Bot, Sparkles, Database } from 'lucide-react';
import api from '../services/api';

// Parse markdown-like text with bold, newlines, bullet points, and tables
function formatMarkdown(text) {
    if (!text) return '';

    // Check if text has a markdown table
    const lines = text.split('\n');
    let html = '';
    let inTable = false;
    let tableHtml = '';
    let isHeaderDone = false;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Detect table rows (contain |)
        if (line.startsWith('|') || (line.includes(' | ') && !line.startsWith('*') && !line.startsWith('•'))) {
            if (!inTable) {
                inTable = true;
                tableHtml = '<div style="overflow-x:auto;margin:8px 0"><table style="width:100%;border-collapse:collapse;font-size:0.75rem">';
                isHeaderDone = false;
            }

            // Skip separator row (--- | ---)
            if (line.replace(/[\s|:-]/g, '').length === 0) {
                isHeaderDone = true;
                continue;
            }

            const cells = line.split('|').map(c => c.trim()).filter(c => c.length > 0);
            const tag = !isHeaderDone ? 'th' : 'td';
            const bgStyle = !isHeaderDone
                ? 'background:rgba(108,99,255,0.15);font-weight:600;'
                : '';
            tableHtml += '<tr>' + cells.map(c =>
                `<${tag} style="padding:4px 8px;border:1px solid rgba(255,255,255,0.1);${bgStyle}">${c}</${tag}>`
            ).join('') + '</tr>';

            if (!isHeaderDone) isHeaderDone = true;
        } else {
            // Close table if we were in one
            if (inTable) {
                tableHtml += '</table></div>';
                html += tableHtml;
                inTable = false;
                tableHtml = '';
            }

            // Process non-table line
            let processed = line
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/^• /, '<span style="margin-left:8px">• </span>')
                .replace(/^- /, '<span style="margin-left:8px">• </span>');

            if (processed.length > 0) {
                html += processed + '<br/>';
            } else if (i > 0) {
                html += '<br/>';
            }
        }
    }

    // Close any open table
    if (inTable) {
        tableHtml += '</table></div>';
        html += tableHtml;
    }

    return html;
}

export default function ChatWidget() {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            text: "👋 Hi! I'm **CampusIQ AI**. I can help with attendance, predictions, grades — and now you can **query & manage data** using natural language!\n\nTry: *\"Show all students\"* or *\"How many courses in CS?\"*",
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setLoading(true);

        try {
            const res = await api.chatQuery(userMsg);
            setMessages(prev => [
                ...prev,
                {
                    role: 'bot',
                    text: res.response,
                    actions: res.suggested_actions,
                },
            ]);
        } catch (err) {
            setMessages(prev => [
                ...prev,
                {
                    role: 'bot',
                    text: "Sorry, I couldn't process that right now. Try asking about your attendance, grades, or data queries!",
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleActionClick = (action) => {
        setInput(action);
    };

    return (
        <div className="chat-widget">
            {open && (
                <div className="chat-panel">
                    <div className="chat-header">
                        <Sparkles size={18} />
                        <h3>CampusIQ AI Assistant</h3>
                        <span style={{
                            fontSize: '0.6rem',
                            background: 'rgba(108,99,255,0.3)',
                            padding: '2px 6px',
                            borderRadius: 8,
                            marginLeft: 8,
                        }}>
                            <Database size={10} style={{ marginRight: 3, verticalAlign: 'middle' }} />
                            NLP
                        </span>
                        <button
                            onClick={() => setOpen(false)}
                            style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
                        >
                            <X size={18} />
                        </button>
                    </div>

                    <div className="chat-messages">
                        {messages.map((msg, i) => (
                            <div key={i} className={`chat-message ${msg.role}`}>
                                <span dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.text) }} />
                                {msg.actions && msg.actions.length > 0 && (
                                    <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                        {msg.actions.map((action, j) => (
                                            <button
                                                key={j}
                                                onClick={() => handleActionClick(action)}
                                                style={{
                                                    padding: '4px 10px',
                                                    fontSize: '0.7rem',
                                                    background: 'rgba(108, 99, 255, 0.2)',
                                                    border: '1px solid rgba(108, 99, 255, 0.3)',
                                                    borderRadius: 12,
                                                    color: '#8B83FF',
                                                    cursor: 'pointer',
                                                }}
                                            >
                                                {action}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                        {loading && (
                            <div className="chat-message bot">
                                <span style={{ display: 'flex', gap: 4 }}>
                                    <span className="skeleton" style={{ width: 8, height: 8, borderRadius: '50%' }} />
                                    <span className="skeleton" style={{ width: 8, height: 8, borderRadius: '50%', animationDelay: '0.2s' }} />
                                    <span className="skeleton" style={{ width: 8, height: 8, borderRadius: '50%', animationDelay: '0.4s' }} />
                                </span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-input-wrapper">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about data, attendance, grades..."
                            disabled={loading}
                        />
                        <button onClick={handleSend} disabled={loading || !input.trim()}>
                            <Send size={16} />
                        </button>
                    </div>
                </div>
            )}

            <button className="chat-toggle" onClick={() => setOpen(!open)}>
                {open ? <X size={24} /> : <MessageCircle size={24} />}
            </button>
        </div>
    );
}
