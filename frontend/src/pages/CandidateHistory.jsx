import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

export default function CandidateHistory() {
    const { phone } = useParams()
    const [searchPhone, setSearchPhone] = useState(phone || '')
    const [candidate, setCandidate] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    useEffect(() => {
        if (phone) loadCandidate(phone)
    }, [phone])

    const loadCandidate = async (p) => {
        setLoading(true)
        setError('')
        setCandidate(null)
        try {
            const res = await fetch(`/dashboard/candidate/${encodeURIComponent(p)}`)
            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Not found')
            }
            const data = await res.json()
            setCandidate(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = (e) => {
        e.preventDefault()
        if (searchPhone.trim()) loadCandidate(searchPhone.trim())
    }

    const getScoreClass = (score) => {
        if (score >= 80) return 'score-high'
        if (score >= 50) return 'score-medium'
        return 'score-low'
    }

    return (
        <div>
            <div className="page-header">
                <h1>Candidate History</h1>
                <p>Look up a candidate's full journey across all roles</p>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="lookup-bar">
                <input className="form-input" type="text" value={searchPhone}
                    onChange={e => setSearchPhone(e.target.value)}
                    placeholder="Enter phone number (e.g. +91-9876543210)" />
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </form>

            {error && <div className="alert alert-error">{error}</div>}

            {loading && <div className="loading"><div className="spinner" /></div>}

            {candidate && (
                <div style={{ animation: 'slideUp 0.3s ease' }}>
                    {/* Candidate Info */}
                    <div className="card" style={{ marginBottom: '24px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                            <div style={{
                                width: '56px', height: '56px', borderRadius: '50%',
                                background: 'var(--accent-gradient)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                fontSize: '22px', fontWeight: 700, color: 'white'
                            }}>
                                {candidate.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <h2 style={{ fontSize: '22px', fontWeight: 700 }}>{candidate.name}</h2>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                                    📞 {candidate.phone} &nbsp;•&nbsp; {candidate.applications.length} application(s)
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Applications */}
                    {candidate.applications.map(app => (
                        <div key={app.id} className="card" style={{ marginBottom: '20px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
                                <div>
                                    <h3 style={{ fontSize: '17px', fontWeight: 600, marginBottom: '4px' }}>
                                        {app.role_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </h3>
                                    <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                                        Applied {new Date(app.created_at).toLocaleDateString()} &nbsp;•&nbsp; ID: {app.id}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    {app.llm_score !== null && (
                                        <span className={`score-pill ${getScoreClass(app.llm_score)}`}>
                                            Score: {app.llm_score}
                                        </span>
                                    )}
                                    {app.bucket && <span className={`badge badge-${app.bucket}`}>{app.bucket}</span>}
                                </div>
                            </div>

                            {/* Details Grid */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Location</div>
                                    <div style={{ fontSize: '14px' }}>{app.location}</div>
                                </div>
                                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Experience</div>
                                    <div style={{ fontSize: '14px' }}>{app.years_experience} years</div>
                                </div>
                                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Stage</div>
                                    <div style={{ fontSize: '14px' }}>{app.current_stage}</div>
                                </div>
                            </div>

                            {/* Skills */}
                            <div style={{ marginBottom: '16px' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>Skills</div>
                                <div className="skills-container">
                                    {app.skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
                                </div>
                            </div>

                            {/* Pitch */}
                            <div style={{ marginBottom: '16px', padding: '14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>Pitch</div>
                                <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>{app.pitch}</p>
                            </div>

                            {/* LLM Reasoning */}
                            {app.llm_reasoning && (
                                <div style={{ marginBottom: '16px', padding: '14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>AI Reasoning</div>
                                    <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>{app.llm_reasoning}</p>
                                </div>
                            )}

                            {/* Stage Transitions */}
                            {app.stage_transitions && app.stage_transitions.length > 0 && (
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase' }}>Pipeline Journey</div>
                                    <div className="timeline">
                                        {app.stage_transitions.map((t, i) => (
                                            <div key={i} className="timeline-item">
                                                <div className="timeline-dot" />
                                                <div className="timeline-content">
                                                    <div className="timeline-header">
                                                        <span className="timeline-stage">
                                                            {t.from_stage ? `${t.from_stage} → ${t.to_stage}` : t.to_stage}
                                                        </span>
                                                        <span className="timeline-time">
                                                            {new Date(t.timestamp).toLocaleString()}
                                                        </span>
                                                    </div>
                                                    <p className="timeline-reason">{t.reason}</p>
                                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                        by {t.triggered_by}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Bucket Overrides */}
                            {app.bucket_overrides && app.bucket_overrides.length > 0 && (
                                <div style={{ marginTop: '16px', padding: '14px', background: 'rgba(245, 158, 11, 0.05)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.15)' }}>
                                    <div style={{ fontSize: '11px', color: 'var(--warning)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>
                                        Bucket Overrides
                                    </div>
                                    {app.bucket_overrides.map((o, i) => (
                                        <div key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                            <span className={`badge badge-${o.old_bucket}`} style={{ fontSize: '11px' }}>{o.old_bucket}</span>
                                            <span style={{ margin: '0 6px' }}>→</span>
                                            <span className={`badge badge-${o.new_bucket}`} style={{ fontSize: '11px' }}>{o.new_bucket}</span>
                                            <span style={{ margin: '0 8px' }}>by {o.overridden_by}</span>
                                            <span style={{ color: 'var(--text-muted)' }}>— {o.reason}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {!loading && !candidate && !error && (
                <div className="empty-state">
                    <div className="icon">🔍</div>
                    <p>Enter a phone number to look up a candidate's history</p>
                </div>
            )}
        </div>
    )
}
