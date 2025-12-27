import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ApprovalList from './pages/ApprovalList'
import ContentEditor from './pages/ContentEditor'

function App() {
    return (
        <BrowserRouter>
            <div style={{ display: 'flex', minHeight: '100vh' }}>
                {/* Sidebar */}
                <nav style={{
                    width: '250px',
                    background: 'var(--bg-secondary)',
                    padding: 'var(--spacing-lg)',
                    borderRight: '1px solid var(--border-color)'
                }}>
                    <h1 style={{
                        fontSize: '1.5rem',
                        fontWeight: '700',
                        marginBottom: 'var(--spacing-xl)',
                        background: 'var(--accent-gradient)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent'
                    }}>
                        Content AI
                    </h1>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
                        <NavLink to="/">Dashboard</NavLink>
                        <NavLink to="/approval">Approval Queue</NavLink>
                    </div>
                </nav>

                {/* Main Content */}
                <main style={{ flex: 1, padding: 'var(--spacing-xl)', overflow: 'auto' }}>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/approval" element={<ApprovalList />} />
                        <Route path="/approval/:id" element={<ContentEditor />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    )
}

function NavLink({ to, children }) {
    return (
        <Link
            to={to}
            style={{
                color: 'var(--text-secondary)',
                textDecoration: 'none',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                transition: 'all 0.3s ease',
                display: 'block'
            }}
            onMouseEnter={(e) => {
                e.target.style.background = 'var(--bg-tertiary)'
                e.target.style.color = 'var(--text-primary)'
            }}
            onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = 'var(--text-secondary)'
            }}
        >
            {children}
        </Link>
    )
}

export default App
