import { useState, useEffect } from 'react'
import OverrideModal from '../components/OverrideModal'

export default function Dashboard() {
    const [roles, setRoles] = useState([])
    const [selectedRole, setSelectedRole] = useState('')
    const [dashboardData, setDashboardData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [overrideTarget, setOverrideTarget] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        fetch('/api/roles').then(r => r.json()).then(data => {
            setRoles(data)
            if (data.length > 0) setSelectedRole(data[0].role_id)
        }).catch(() => { })
    }, [])

    useEffect(() => {
        if (selectedRole) loadDashboard()
    }, [selectedRole])

    const loadDashboard = async () => {
        setLoading(true)
        setError('')
        try {
            const res = await fetch(`/dashboard/role/${selectedRole}`)
            if (!res.ok) throw new Error('Failed to load dashboard')
            const data = await res.json()
            setDashboardData(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const totalCandidates = dashboardData
        ? dashboardData.advance.length + dashboardData.hold.length + dashboardData.reject.length + dashboardData.pending.length
        : 0

    const getScoreClass = (score) => {
        if (score >= 80) return 'score-high'
        if (score >= 50) return 'score-medium'
        return 'score-low'
    }

    const renderBucketSection = (title, candidates, badgeClass) => (
        <div className="bucket-section">
            <div className="bucket-header">
                <span className={`badge badge-${badgeClass}`} style={{ fontSize: '13px' }}>{title}</span>
                <span className="bucket-count">{candidates.length}</span>
            </div>
            {candidates.length === 0 ? (
                <div className="empty-state" style={{ padding: '24px' }}>
                    <p>No candidates in this bucket</p>
                </div>
            ) : (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Phone</th>
                                <th>Score</th>
                                <th>Eligibility</th>
                                <th>Reasoning</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {candidates.map(c => (
                                <tr key={c.application_id}>
                                    <td style={{ fontWeight: 600 }}>{c.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{c.phone}</td>
                                    <td>
                                        {c.llm_score !== null ? (
                                            <span className={`score-pill ${getScoreClass(c.llm_score)}`}>{c.llm_score}</span>
                                        ) : '—'}
                                    </td>
                                    <td>
                                        {c.eligibility && (
                                            <span className={`badge badge-${c.eligibility.toLowerCase() === 'eligible' ? 'eligible' : 'ineligible'}`}>
                                                {c.eligibility}
                                            </span>
                                        )}
                                    </td>
                                    <td style={{ maxWidth: '300px', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                                        {c.llm_reasoning ? (c.llm_reasoning.length > 120 ? c.llm_reasoning.slice(0, 120) + '...' : c.llm_reasoning) : '—'}
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button className="btn btn-secondary btn-sm" onClick={() => setOverrideTarget(c)}>
                                                Override
                                            </button>
                                            <a href={`/candidate/${c.phone}`} className="btn btn-secondary btn-sm"
                                                style={{ textDecoration: 'none' }}>
                                                History
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )

    return (
        <div>
            <div className="page-header">
                <h1>Recruiter Dashboard</h1>
                <p>View candidates, scores, and manage bucket assignments</p>
            </div>

            {/* Role Selector */}
            <div style={{ marginBottom: '24px' }}>
                <select className="form-select" style={{ maxWidth: '400px' }}
                    value={selectedRole} onChange={e => setSelectedRole(e.target.value)}>
                    {roles.map(r => (
                        <option key={r.role_id} value={r.role_id}>{r.title}</option>
                    ))}
                </select>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            {loading ? (
                <div className="loading"><div className="spinner" /></div>
            ) : dashboardData && (
                <>
                    {/* Stats */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">{totalCandidates}</div>
                            <div className="stat-label">Total Candidates</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ background: 'linear-gradient(135deg, #10b981, #34d399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                {dashboardData.advance.length}
                            </div>
                            <div className="stat-label">Advance</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ background: 'linear-gradient(135deg, #f59e0b, #fbbf24)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                {dashboardData.hold.length}
                            </div>
                            <div className="stat-label">Hold</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ background: 'linear-gradient(135deg, #ef4444, #f87171)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                {dashboardData.reject.length}
                            </div>
                            <div className="stat-label">Reject</div>
                        </div>
                    </div>

                    {/* Bucket Sections */}
                    {renderBucketSection('Advance', dashboardData.advance, 'advance')}
                    {renderBucketSection('Hold', dashboardData.hold, 'hold')}
                    {renderBucketSection('Reject', dashboardData.reject, 'reject')}
                    {dashboardData.pending.length > 0 && renderBucketSection('Pending', dashboardData.pending, 'pending')}
                </>
            )}

            {/* Override Modal */}
            {overrideTarget && (
                <OverrideModal
                    application={overrideTarget}
                    onClose={() => setOverrideTarget(null)}
                    onOverride={() => { setOverrideTarget(null); loadDashboard() }}
                />
            )}
        </div>
    )
}
