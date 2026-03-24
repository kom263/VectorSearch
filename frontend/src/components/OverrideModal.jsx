import { useState } from 'react'

export default function OverrideModal({ application, onClose, onOverride }) {
    const [newBucket, setNewBucket] = useState('')
    const [reason, setReason] = useState('')
    const [recruiterName, setRecruiterName] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const bucketOptions = ['advance', 'hold', 'reject'].filter(b => b !== application?.bucket)

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!newBucket || !reason || !recruiterName) {
            setError('All fields are required')
            return
        }
        setLoading(true)
        setError('')
        try {
            const res = await fetch('/dashboard/override', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    application_id: application.application_id,
                    new_bucket: newBucket,
                    reason,
                    overridden_by: recruiterName
                })
            })
            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Override failed')
            }
            onOverride()
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <h2>Override Bucket Decision</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '20px', fontSize: '14px' }}>
                    <strong>{application.name}</strong> — Currently in <span className={`badge badge-${application.bucket}`}>{application.bucket}</span>
                </p>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">New Bucket</label>
                        <select className="form-select" value={newBucket} onChange={e => setNewBucket(e.target.value)} required>
                            <option value="">Select new bucket...</option>
                            {bucketOptions.map(b => (
                                <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Recruiter Name</label>
                        <input className="form-input" type="text" value={recruiterName}
                            onChange={e => setRecruiterName(e.target.value)}
                            placeholder="Your name" required />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Reason (mandatory)</label>
                        <textarea className="form-textarea" value={reason}
                            onChange={e => setReason(e.target.value)}
                            placeholder="Provide a clear reason for this override..."
                            required minLength={5} />
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Overriding...' : 'Confirm Override'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
