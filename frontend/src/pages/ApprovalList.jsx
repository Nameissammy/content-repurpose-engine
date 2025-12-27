import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function ApprovalList() {
    const navigate = useNavigate()

    const { data: content, isLoading, refetch } = useQuery({
        queryKey: ['pendingContent'],
        queryFn: () => axios.get('/api/content/pending').then(res => res.data)
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
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 'var(--spacing-lg)'
            }}>
                <h1 style={{ fontSize: '2rem', fontWeight: '700' }}>
                    Approval Queue
                </h1>
                <span className="status-badge status-pending">
                    {content?.length || 0} Pending
                </span>
            </div>

            {!content || content.length === 0 ? (
                <div className="glass-card" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        No content pending approval
                    </p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                    {content.map((item) => (
                        <ContentCard
                            key={item.id}
                            content={item}
                            onClick={() => navigate(`/approval/${item.id}`)}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

function ContentCard({ content, onClick }) {
    const platformColors = {
        twitter: '#1DA1F2',
        linkedin: '#0A66C2',
        instagram: '#E4405F',
        newsletter: '#10b981'
    }

    const platformIcons = {
        twitter: '𝕏',
        linkedin: 'in',
        instagram: '📷',
        newsletter: '📧'
    }

    return (
        <div
            className="glass-card"
            onClick={onClick}
            style={{
                cursor: 'pointer',
                transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)'
                e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-color)'
                e.currentTarget.style.transform = 'translateY(0)'
            }}
        >
            <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'flex-start' }}>
                {/* Platform Icon */}
                <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    background: platformColors[content.platform] || 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    flexShrink: 0
                }}>
                    {platformIcons[content.platform] || '📱'}
                </div>

                {/* Content Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>
                            {content.platform.charAt(0).toUpperCase() + content.platform.slice(1)} Post
                        </h3>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                            {new Date(content.created_at).toLocaleDateString()}
                        </span>
                    </div>

                    {content.video_title && (
                        <p style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.875rem',
                            marginBottom: '0.5rem'
                        }}>
                            From: {content.video_title}
                        </p>
                    )}

                    <p style={{
                        color: 'var(--text-secondary)',
                        marginBottom: '0.75rem',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical'
                    }}>
                        {content.content}
                    </p>

                    <button className="btn-primary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                        Review & Approve →
                    </button>
                </div>
            </div>
        </div>
    )
}
