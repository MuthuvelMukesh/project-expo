import { useState, useEffect, useRef } from 'react';
import { Bell, Check, CheckCheck, X } from 'lucide-react';
import api from '../services/api';

export default function NotificationBell() {
    const [open, setOpen] = useState(false);
    const [notifs, setNotifs] = useState([]);
    const [unread, setUnread] = useState(0);
    const ref = useRef(null);

    const load = async () => {
        try {
            const [list, count] = await Promise.all([
                api.getNotifications(), api.getUnreadCount()
            ]);
            setNotifs(list);
            setUnread(count.unread_count);
        } catch (e) { /* silent */ }
    };

    useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t); }, []);
    useEffect(() => {
        const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const markRead = async (id) => {
        await api.markNotificationRead(id);
        load();
    };
    const markAll = async () => {
        await api.markAllNotificationsRead();
        load();
    };

    const typeColors = { info: '#6c63ff', warning: '#ffaa00', critical: '#ff4b4b', success: '#00d278' };
    const typeIcons = { info: 'ℹ️', warning: '⚠️', critical: '🔴', success: '✅' };

    return (
        <div ref={ref} style={{ position: 'relative' }}>
            <button onClick={() => { setOpen(!open); if (!open) load(); }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', position: 'relative', padding: 6, color: 'var(--text-primary)' }}>
                <Bell size={20} />
                {unread > 0 && (
                    <span style={{ position: 'absolute', top: 0, right: 0, width: 18, height: 18, borderRadius: '50%', background: '#ff4b4b', color: 'white', fontSize: '0.6rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {unread > 9 ? '9+' : unread}
                    </span>
                )}
            </button>

            {open && (
                <div style={{ position: 'absolute', top: '100%', right: 0, width: 360, maxHeight: 440, background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.4)', zIndex: 100, overflow: 'hidden' }}>
                    <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Notifications</span>
                        <div style={{ display: 'flex', gap: 8 }}>
                            {unread > 0 && <button onClick={markAll} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 3 }}><CheckCheck size={13} /> Mark all read</button>}
                            <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={16} /></button>
                        </div>
                    </div>
                    <div style={{ maxHeight: 380, overflowY: 'auto' }}>
                        {notifs.length === 0 ? (
                            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No notifications</div>
                        ) : notifs.map(n => (
                            <div key={n.id} onClick={() => !n.is_read && markRead(n.id)}
                                style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.04))', cursor: 'pointer', background: n.is_read ? 'transparent' : 'rgba(108,99,255,0.04)', transition: 'background 0.15s' }}>
                                <div style={{ display: 'flex', gap: 10, alignItems: 'start' }}>
                                    <span style={{ fontSize: '1rem' }}>{typeIcons[n.type] || 'ℹ️'}</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: n.is_read ? 400 : 600, fontSize: '0.82rem', color: n.is_read ? 'var(--text-muted)' : 'var(--text-primary)' }}>{n.title}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>{n.message}</div>
                                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4, display: 'flex', gap: 8 }}>
                                            <span>{new Date(n.created_at).toLocaleDateString()}</span>
                                            <span style={{ padding: '1px 6px', borderRadius: 4, background: `${typeColors[n.type]}15`, color: typeColors[n.type], fontSize: '0.6rem' }}>{n.category}</span>
                                        </div>
                                    </div>
                                    {!n.is_read && <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary)', flexShrink: 0, marginTop: 4 }} />}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
