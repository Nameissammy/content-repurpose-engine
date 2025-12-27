import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function Dashboard() {
    const { data, isLoading } = useQuery({
        queryKey: ['dashboardStats'],
        queryFn: () => axios.get('/api/dashboard/stats').then(res => res.data)
    })

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--spacing-xl)' }}>
                <div className="spinner"></div>
            </div>
        )
    }

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: 'var(--spacing-lg)' }}>
                Dashboard
            </h1>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: 'var(--spacing-md)',
                marginBottom: 'var(--spacing-xl)'
            }}>
                <StatCard
                    title="Total Videos"
                    value={data?.videos?.total || 0}
                    subtitle={`${data?.videos?.processing || 0} processing`}
                />
                <StatCard
                    title="Generated Content"
                    value={data?.content?.total || 0}
                    subtitle={`${data?.content?.published || 0} published`}
                />
                <StatCard
                    title="Pending Approval"
                    value={data?.content?.pending_approval || 0}
                    subtitle="Needs review"
                    highlight
                />
                <StatCard
                    title="Success Rate"
                    value={`${calculateSuccessRate(data)}%`}
                    subtitle="Content approved"
                />
            </div>

            <div className="glass-card">
                <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: 'var(--spacing-md)' }}>
                    Quick Stats
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
                    <div>
                        <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--spacing-xs)' }}>
                            Videos
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <StatusRow label="Completed" value={data?.videos?.completed || 0} color="var(--success)" />
                            <StatusRow label="Processing" value={data?.videos?.processing || 0} color="var(--warning)" />
                            <StatusRow label="Pending" value={data?.videos?.pending || 0} color="var(--text-muted)" />
                        </div>
                    </div>
                    <div>
                        <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--spacing-xs)' }}>
                            Content
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <StatusRow label="Published" value={data?.content?.published || 0} color="var(--accent-primary)" />
                            <StatusRow label="Approved" value={data?.content?.approved || 0} color="var(--success)" />
                            <StatusRow label="Pending" value={data?.content?.pending_approval || 0} color="var(--warning)" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

function StatCard({ title, value, subtitle, highlight }) {
    return (
        <div className="glass-card" style={{
            borderColor: highlight ? 'var(--accent-primary)' : 'var(--border-color)'
        }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                {title}
            </div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.25rem' }}>
                {value}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                {subtitle}
            </div>
        </div>
    )
}

function StatusRow({ label, value, color }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{label}</span>
            <span style={{ color, fontWeight: '600' }}>{value}</span>
        </div>
    )
}

function calculateSuccessRate(data) {
    if (!data?.content) return 0
    const total = data.content.total || 0
    const successful = (data.content.approved || 0) + (data.content.published || 0)
    return total > 0 ? Math.round((successful / total) * 100) : 0
}
