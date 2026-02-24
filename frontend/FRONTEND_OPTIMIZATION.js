"""
CampusIQ — Frontend Performance Optimizations
Code splitting, lazy loading, and memoization best practices.
"""

// ─── 1. CODE SPLITTING WITH LAZY LOADING ────────────────────────────

// Before: Everything bundled together (~1.2MB JS)
import AdminPanel from './pages/AdminPanel';
import StudentDashboard from './pages/StudentDashboard';
import CopilotPanel from './pages/CopilotPanel';
import AttendanceDetails from './pages/AttendanceDetails';

// After: Load routes on-demand (400KB initial, load rest as needed)
import { Suspense, lazy } from 'react';

const AdminPanel = lazy(() => import('./pages/AdminPanel'));
const StudentDashboard = lazy(() => import('./pages/StudentDashboard'));
const CopilotPanel = lazy(() => import('./pages/CopilotPanel'));
const AttendanceDetails = lazy(() => import('./pages/AttendanceDetails'));

const Loading = () => (
    <div className="loading-spinner">
        <div className="spinner"></div>
        <p>Loading...</p>
    </div>
);

// Use in routes:
<Suspense fallback={<Loading />}>
    <Routes>
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/dashboard" element={<StudentDashboard />} />
        <Route path="/copilot" element={<CopilotPanel />} />
        <Route path="/attendance" element={<AttendanceDetails />} />
    </Routes>
</Suspense>


// ─── 2. MEMOIZATION FOR STATS CARDS ─────────────────────────────────

// Before: Re-renders on every parent state change
const StatsCard = ({ label, value, icon: Icon }) => (
    <div className="stats-card">
        <div className="icon-wrapper"><Icon size={22} /></div>
        <div className="stats-label">{label}</div>
        <div className="stats-value">{value}</div>
    </div>
);

// After: Memoized to prevent unnecessary re-renders
const StatsCard = React.memo(({ label, value, icon: Icon }) => (
    <div className="stats-card">
        <div className="icon-wrapper"><Icon size={22} /></div>
        <div className="stats-label">{label}</div>
        <div className="stats-value">{value}</div>
    </div>
));

// Use memoization for expensive data transformations:
export default function AdminPanel() {
    const [data, setData] = useState(null);
    
    // Memoize KPI calculations
    const memoizedKPIs = useMemo(() => {
        if (!data) return null;
        return {
            avgAttendance: (data.campus_avg_attendance * 100).toFixed(1),
            riskPercentage: (data.campus_high_risk_pct * 100).toFixed(1),
            totalStudents: data.total_students,
        };
    }, [data]);  // Only recompute if data changes

    return (
        <div className="dashboard">
            <StatsCard 
                label="Campus Avg Attendance" 
                value={memoizedKPIs?.avgAttendance}
                icon={Activity}
            />
        </div>
    );
}


// ─── 3. CALLBACK MEMOIZATION ────────────────────────────────────────

// Before: New function created on every render
export default function AdminPanel() {
    const handleRefresh = () => {
        api.getAdminDashboard().then(setData);
    };
    
    return <button onClick={handleRefresh}>Refresh</button>;
}

// After: Function memoized
export default function AdminPanel() {
    const handleRefresh = useCallback(() => {
        api.getAdminDashboard().then(setData);
    }, []);  // Empty deps = function never recreated
    
    return <button onClick={handleRefresh}>Refresh</button>;
}


// ─── 4. PARALLEL DATA FETCHING ──────────────────────────────────────

// Before: Sequential fetches (slow)
useEffect(() => {
    api.getAdminDashboard()
        .then(dashboard => {
            setDashboard(dashboard);
            return api.getDepartmentKPIs();
        })
        .then(kpis => {
            setKPIs(kpis);
            return api.getRecentAlerts();
        })
        .then(alerts => setAlerts(alerts));
}, []);

// After: Parallel fetches (faster)
useEffect(() => {
    Promise.all([
        api.getAdminDashboard(),
        api.getDepartmentKPIs(),
        api.getRecentAlerts(),
    ])
        .then(([dashboard, kpis, alerts]) => {
            setDashboard(dashboard);
            setKPIs(kpis);
            setAlerts(alerts);
        });
}, []);

// Even better: Use React Query for caching + automatic refetch
import { useQuery } from '@tanstack/react-query';

const useAdminDashboard = () => {
    return useQuery({
        queryKey: ['admin', 'dashboard'],
        queryFn: () => api.getAdminDashboard(),
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
    });
};


// ─── 5. VIRTUAL SCROLLING FOR LARGE LISTS ───────────────────────────

// Before: Render all 1000 rows (hang!)
export default function TimetableView() {
    const [schedule, setSchedule] = useState([]);
    
    return (
        <div className="timetable">
            {schedule.map(entry => (
                <ClassCard key={entry.id} {...entry} />
            ))}
        </div>
    );
}

// After: Only render visible rows (smooth even with 10K items)
import { FixedSizeList } from 'react-window';

export default function TimetableView() {
    const [schedule, setSchedule] = useState([]);
    
    return (
        <FixedSizeList
            height={600}
            itemCount={schedule.length}
            itemSize={100}
            width="100%"
        >
            {({ index, style }) => (
                <div style={style}>
                    <ClassCard {...schedule[index]} />
                </div>
            )}
        </FixedSizeList>
    );
}

// Install: npm install react-window


// ─── 6. DEBOUNCED SEARCH INPUT ──────────────────────────────────────

import { useCallback } from 'react';

function useDebouncedValue(value, delay = 500) {
    const [debouncedValue, setDebouncedValue] = useCallback(
        value,
        delay,
    );
    
    useEffect(() => {
        const handler = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(handler);
    }, [value, delay, setDebouncedValue]);
    
    return debouncedValue;
}

export default function StudentSearch() {
    const [search, setSearch] = useState('');
    const debouncedSearch = useDebouncedValue(search, 300);  // Only search every 300ms
    
    useEffect(() => {
        if (debouncedSearch) {
            api.searchStudents(debouncedSearch).then(setResults);
        }
    }, [debouncedSearch]);
    
    return <input value={search} onChange={e => setSearch(e.target.value)} />;
}


// ─── 7. IMAGE OPTIMIZATION ─────────────────────────────────────────

// Before: Load full resolution
<img src="/logos/campusiq.png" alt="Logo" />

// After: Use dynamic import or lazy loading
<img 
    loading="lazy"
    src="/logos/campusiq-small.webp"  // Use WebP format
    srcSet="/logos/campusiq-small.webp 500w, /logos/campusiq-large.webp 1000w"
    alt="Logo"
/>


// ─── 8. DYNAMIC IMPORTS FOR HEAVY LIBRARIES ─────────────────────────

// Before: Chart library bundled with main app
import { LineChart, Line, XAxis, YAxis } from 'recharts';

// After: Load chart only when needed
const ChartComponent = lazy(() => import('recharts').then(mod => ({
    default: () => <mod.LineChart>...</mod.LineChart>
})));


// ─── 9. OPTIMIZE BUNDLE SIZE ───────────────────────────────────────

// Install bundle analyzer:
// npm install --save-dev vite-plugin-visualizer

// In vite.config.js:
import { visualizer } from 'vite-plugin-visualizer';

export default {
    plugins: [
        react(),
        visualizer({
            open: true,  // Opens HTML report after build
        })
    ]
};

// Run: npm run build


// ─── 10. SERVICE WORKER FOR OFFLINE SUPPORT ──────────────────────────

// frontend/src/serviceWorker.js
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(reg => {
            console.log('✅ Service Worker registered');
        });
    });
}

// Caches API responses for offline access
// frontend/public/sw.js
self.addEventListener('fetch', event => {
    if (event.request.method === 'GET') {
        event.respondWith(
            caches.match(event.request).then(response => {
                return response || fetch(event.request).then(res => {
                    return caches.open('v1').then(cache => {
                        cache.put(event.request, res.clone());
                        return res;
                    });
                });
            })
        );
    }
});


// ─── 11. REQUEST INTERCEPTOR WITH RETRY ────────────────────────────

// frontend/src/services/api.js
async request(endpoint, options = {}, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers: this.getHeaders(),
            });
            
            if (!response.ok && response.status >= 500 && i < retries - 1) {
                // Retry on server errors
                await new Promise(r => setTimeout(r, 1000 * (i + 1)));
                continue;
            }
            
            return response;
        } catch (err) {
            if (i === retries - 1) throw err;
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
}


// ─── 12. BATCHED API REQUESTS ──────────────────────────────────────

// frontend/src/services/api.js
async getCourseWithDetails(courseId) {
    // Before: 3 separate requests (200 + 150 + 100ms = 450ms)
    // await api.getCourse(courseId);
    // await api.getCourseStudents(courseId);
    // await api.getCoursePredictions(courseId);
    
    // After: Batch into single request
    return this.request(`/courses/${courseId}?details=true`);
}


// ─── PERFORMANCE CHECKLIST ─────────────────────────────────────────

/*
✅ Code Splitting
  ☐ Lazy load all route components
  ☐ Chunk size < 100KB per route
  
✅ Data Fetching
  ☐ Use React Query for caching
  ☐ Parallel fetch unrelated data
  ☐ Implement pagination for large lists
  
✅ Rendering Optimization
  ☐ Memoize expensive components
  ☐ Use useCallback for event handlers
  ☐ Use useMemo for computed values
  
✅ UI/UX
  ☐ Virtual scrolling for lists
  ☐ Debounced search/filters
  ☐ Skeleton loaders during fetch
  
✅ Bundle Size
  ☐ Tree-shaking enabled
  ☐ No duplicate dependencies
  ☐ Bundle < 500KB gzipped
  
✅ Network
  ☐ GZIP compression enabled
  ☐ Cache-Control headers set
  ☐ CDN configured for static assets
*/
