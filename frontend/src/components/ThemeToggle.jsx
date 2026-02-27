import { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle() {
    const [theme, setTheme] = useState(() => localStorage.getItem('campusiq-theme') || 'dark');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('campusiq-theme', theme);
    }, [theme]);

    const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

    return (
        <button onClick={toggle} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: 6,
                color: 'var(--text-secondary)', display: 'flex', alignItems: 'center',
                transition: 'color 0.2s',
            }}
            onMouseOver={e => e.currentTarget.style.color = 'var(--primary)'}
            onMouseOut={e => e.currentTarget.style.color = 'var(--text-secondary)'}
        >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
    );
}
