import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Bot, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function ChatWidget() {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            text: "👋 Hi! I'm **CampusIQ AI**. Ask me about your attendance, predictions, grades, or anything academic!",
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
                    text: "Sorry, I couldn't process that right now. Try asking about your attendance, grades, or predictions!",
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

    // Format markdown-like bold text
    const formatText = (text) => {
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    };

    return (
        <div className="chat-widget">
            {open && (
                <div className="chat-panel">
                    <div className="chat-header">
                        <Sparkles size={18} />
                        <h3>CampusIQ AI Assistant</h3>
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
                                <span dangerouslySetInnerHTML={{ __html: formatText(msg.text) }} />
                                {msg.actions && msg.actions.length > 0 && (
                                    <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                        {msg.actions.map((action, j) => (
                                            <button
                                                key={j}
                                                onClick={() => {
                                                    setInput(action);
                                                }}
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
                            placeholder="Ask about attendance, grades..."
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
