import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

export default function ContentEditor() {
    const { id } = useParams()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [editedContent, setEditedContent] = useState('')

    const { data: content, isLoading } = useQuery({
        queryKey: ['content', id],
        queryFn: () => axios.get(`/api/content/${id}`).then(res => {
            setEditedContent(res.data.content)
            return res.data
        })
    })

    const updateMutation = useMutation({
        mutationFn: (data) => axios.put(`/api/content/${id}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries(['content', id])
        }
    })

    const approveMutation = useMutation({
        mutationFn: () => axios.post(`/api/content/${id}/approve`, { approved_by: 'admin' }),
        onSuccess: () => {
            navigate('/approval')
            queryClient.invalidateQueries(['pendingContent'])
        }
    })

    const rejectMutation = useMutation({
        mutationFn: () => axios.post(`/api/content/${id}/reject`),
        onSuccess: () => {
            navigate('/approval')
            queryClient.invalidateQueries(['pendingContent'])
        }
    })

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--spacing-xl)' }}>
                <div className="spinner"></div>
            </div>
        )
    }

    const handleSave = () => {
        updateMutation.mutate({ content: editedContent })
    }

    const handleApprove = () => {
        if (confirm('Approve and publish this content?')) {
            approveMutation.mutate()
        }
    }

    const handleReject = () => {
        if (confirm('Reject this content?')) {
            rejectMutation.mutate()
        }
    }

    return (
        <div className="fade-in">
            <button
                onClick={() => navigate('/approval')}
                className="btn-secondary"
                style={{ marginBottom: 'var(--spacing-md)' }}
            >
                ← Back to Queue
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)' }}>
                {/* Original Video Info */}
                <div className="glass-card">
                    <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: 'var(--spacing-md)' }}>
                        Source Video
                    </h2>
                    <h3 style={{ fontSize: '1rem', marginBottom: 'var(--spacing-sm)' }}>
                        {content?.video_title || 'Untitled'}
                    </h3>
                    {content?.video_url && (
                        <a
                            href={content.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: 'var(--accent-primary)', fontSize: '0.875rem' }}
                        >
                            View on YouTube →
                        </a>
                    )}

                    <div style={{ marginTop: 'var(--spacing-md)' }}>
                        <span className={`status-badge status-${content?.approval_status || 'pending'}`}>
                            {content?.platform?.toUpperCase()}
                        </span>
                    </div>
                </div>

                {/* Content Editor */}
                <div className="glass-card">
                    <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: 'var(--spacing-md)' }}>
                        Generated Content
                    </h2>

                    <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        rows={15}
                        style={{
                            minHeight: '300px',
                            marginBottom: 'var(--spacing-md)',
                            fontFamily: 'monospace'
                        }}
                    />

                    <div style={{
                        display: 'flex',
                        gap: 'var(--spacing-sm)',
                        justifyContent: 'space-between'
                    }}>
                        <button
                            onClick={handleSave}
                            className="btn-secondary"
                            disabled={updateMutation.isPending}
                        >
                            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                        </button>

                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                            <button
                                onClick={handleReject}
                                className="btn-secondary"
                                disabled={rejectMutation.isPending}
                                style={{ color: 'var(--error)' }}
                            >
                                Reject
                            </button>
                            <button
                                onClick={handleApprove}
                                className="btn-primary"
                                disabled={approveMutation.isPending}
                            >
                                {approveMutation.isPending ? 'Publishing...' : 'Approve & Publish'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Preview */}
            <div className="glass-card" style={{ marginTop: 'var(--spacing-lg)' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: 'var(--spacing-md)' }}>
                    Preview
                </h2>
                <div style={{
                    background: 'var(--bg-primary)',
                    padding: 'var(--spacing-md)',
                    borderRadius: 'var(--radius-sm)',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word'
                }}>
                    {editedContent}
                </div>
            </div>
        </div>
    )
}
