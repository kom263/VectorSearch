import { useState, useEffect } from 'react'

export default function CandidateApply() {
    const [roles, setRoles] = useState([])
    const [form, setForm] = useState({
        name: '', phone: '', skills: [], years_experience: '',
        location: '', pitch: '', role_id: ''
    })
    const [skillInput, setSkillInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        fetch('/api/roles').then(r => r.json()).then(setRoles).catch(() => { })
    }, [])

    const addSkill = () => {
        const s = skillInput.trim()
        if (s && !form.skills.includes(s)) {
            setForm({ ...form, skills: [...form.skills, s] })
            setSkillInput('')
        }
    }

    const removeSkill = (skill) => {
        setForm({ ...form, skills: form.skills.filter(s => s !== skill) })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        setResult(null)
        try {
            const payload = { ...form, years_experience: parseInt(form.years_experience) }
            const res = await fetch('/api/candidates/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || 'Application failed')
            setResult(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const getScoreClass = (score) => {
        if (score >= 80) return 'score-high'
        if (score >= 50) return 'score-medium'
        return 'score-low'
    }

    return (
        <div>
            <div className="page-header">
                <h1>Apply for a Role</h1>
                <p>Submit your profile and get AI-evaluated in seconds</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: '32px', maxWidth: '1100px' }}>
                {/* Application Form */}
                <div className="card">
                    {error && <div className="alert alert-error">{error}</div>}

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label className="form-label">Role</label>
                            <select className="form-select" value={form.role_id}
                                onChange={e => setForm({ ...form, role_id: e.target.value })} required>
                                <option value="">Select a role...</option>
                                {roles.map(r => (
                                    <option key={r.role_id} value={r.role_id}>{r.title}</option>
                                ))}
                            </select>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div className="form-group">
                                <label className="form-label">Full Name</label>
                                <input className="form-input" type="text" value={form.name}
                                    onChange={e => setForm({ ...form, name: e.target.value })}
                                    placeholder="John Doe" required />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Phone</label>
                                <input className="form-input" type="tel" value={form.phone}
                                    onChange={e => setForm({ ...form, phone: e.target.value })}
                                    placeholder="+91-9876543210" required />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div className="form-group">
                                <label className="form-label">Years of Experience</label>
                                <input className="form-input" type="number" min="0" value={form.years_experience}
                                    onChange={e => setForm({ ...form, years_experience: e.target.value })}
                                    placeholder="5" required />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Location</label>
                                <input className="form-input" type="text" value={form.location}
                                    onChange={e => setForm({ ...form, location: e.target.value })}
                                    placeholder="Mumbai" required />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Skills</label>
                            <div className="skills-container" style={{ marginBottom: '8px' }}>
                                {form.skills.map(skill => (
                                    <span key={skill} className="skill-tag">
                                        {skill}
                                        <span className="remove" onClick={() => removeSkill(skill)}>×</span>
                                    </span>
                                ))}
                            </div>
                            <div className="skill-input-wrapper">
                                <input className="form-input" type="text" value={skillInput}
                                    onChange={e => setSkillInput(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill() } }}
                                    placeholder="Type a skill and press Enter" />
                                <button type="button" className="btn btn-secondary" onClick={addSkill}>Add</button>
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Pitch (2-3 sentences)</label>
                            <textarea className="form-textarea" value={form.pitch}
                                onChange={e => setForm({ ...form, pitch: e.target.value })}
                                placeholder="Why are you a great fit for this role? Highlight your relevant experience and what excites you about the opportunity..."
                                required minLength={10} maxLength={1000} />
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'right' }}>
                                {form.pitch.length}/1000
                            </div>
                        </div>

                        <button type="submit" className="btn btn-primary" disabled={loading || form.skills.length === 0}
                            style={{ width: '100%', padding: '14px' }}>
                            {loading ? '⏳ Evaluating with AI...' : '🚀 Submit Application'}
                        </button>
                    </form>
                </div>

                {/* Results Panel */}
                {result && (
                    <div style={{ animation: 'slideUp 0.4s ease' }}>
                        <div className="card" style={{ marginBottom: '16px' }}>
                            <h3 style={{ marginBottom: '16px', fontSize: '18px' }}>AI Evaluation Result</h3>

                            <div className="stats-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '20px' }}>
                                <div className="stat-card">
                                    <div className="stat-value">{result.llm_score}</div>
                                    <div className="stat-label">LLM Score</div>
                                </div>
                                <div className="stat-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                    <span className={`badge badge-${result.eligibility?.toLowerCase() === 'eligible' ? 'eligible' : 'ineligible'}`}
                                        style={{ fontSize: '16px', padding: '8px 16px' }}>
                                        {result.eligibility}
                                    </span>
                                    <div className="stat-label" style={{ marginTop: '8px' }}>Status</div>
                                </div>
                            </div>

                            {result.bucket && (
                                <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Bucket:</span>
                                    <span className={`badge badge-${result.bucket}`}>{result.bucket}</span>
                                </div>
                            )}

                            <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', padding: '16px', marginBottom: '16px' }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>
                                    AI Reasoning
                                </div>
                                <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                                    {result.reasoning}
                                </p>
                            </div>
                        </div>

                        {/* Constraint Results */}
                        {result.constraint_results && result.constraint_results.length > 0 && (
                            <div className="card" style={{ marginBottom: '16px' }}>
                                <h4 style={{ marginBottom: '12px', fontSize: '15px' }}>Constraint Checks</h4>
                                {result.constraint_results.map((c, i) => (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 0',
                                        borderBottom: i < result.constraint_results.length - 1 ? '1px solid var(--border-color)' : 'none'
                                    }}>
                                        <span style={{ fontSize: '18px' }}>{c.passed ? '✅' : '❌'}</span>
                                        <div>
                                            <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.constraint.replace(/_/g, ' ').toUpperCase()}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{c.detail}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Stage Transitions */}
                        {result.stage_transitions && result.stage_transitions.length > 0 && (
                            <div className="card">
                                <h4 style={{ marginBottom: '16px', fontSize: '15px' }}>Pipeline Journey</h4>
                                <div className="timeline">
                                    {result.stage_transitions.map((t, i) => (
                                        <div key={i} className="timeline-item">
                                            <div className="timeline-dot" />
                                            <div className="timeline-content">
                                                <div className="timeline-header">
                                                    <span className="timeline-stage">
                                                        {t.from_stage ? `${t.from_stage} → ${t.to_stage}` : t.to_stage}
                                                    </span>
                                                    <span className="timeline-time">
                                                        {new Date(t.timestamp).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                                <p className="timeline-reason">{t.reason}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
