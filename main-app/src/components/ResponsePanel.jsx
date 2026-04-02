import { useState } from 'react'
import './ResponsePanel.css'

// Determine display style for a value
function getValueType(key, value) {
    if (value === true) return 'positive'
    if (value === false) return 'negative'
    if (typeof value === 'number') return 'number'
    if (
        typeof value === 'string' &&
        ['ACTIVE', 'EXACT', 'completed', 'APPROVE'].includes(value)
    )
        return 'positive'
    if (
        typeof value === 'string' &&
        ['INACTIVE', 'REJECT', 'FAILED', 'NONE'].includes(value)
    )
        return 'negative'
    return 'neutral'
}

// Pretty-print a key like "kyc_verified" → "KYC Verified"
function formatKey(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase())
}

// Format boolean for display
function formatValue(value) {
    if (value === true) return '✓ Yes'
    if (value === false) return '✗ No'
    return String(value)
}

function ResponseCard({ res }) {
    const [showRaw, setShowRaw] = useState(false)

    const entries = Object.entries(res.data).filter(
        ([, v]) => typeof v !== 'object'
    )

    return (
        <div className={`response-card ${res.status === 'success' ? 'success' : 'failure'}`}>
            <div className="response-header">
                <span className="response-service">{formatKey(res.service)}</span>
                <span className={`response-badge ${res.status}`}>
                    {res.status === 'success'
                        ? `✓ ${res.statusCode}`
                        : `✗ ${res.statusCode || 'NETWORK ERROR'}`}
                </span>
            </div>

            {res.status === 'success' ? (
                <div className="response-fields">
                    {entries.map(([key, value]) => (
                        <div className="field-row" key={key}>
                            <span className="field-key">{formatKey(key)}</span>
                            <span className={`field-value ${getValueType(key, value)}`}>
                                {formatValue(value)}
                            </span>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="response-error-body">
                    {res.data.message || JSON.stringify(res.data, null, 2)}
                </div>
            )}

            <button className="raw-toggle" onClick={() => setShowRaw(!showRaw)}>
                {showRaw ? '▲ Hide Raw JSON' : '▼ Show Raw JSON'}
            </button>

            {showRaw && (
                <pre className="response-body">
                    {JSON.stringify(res.data, null, 2)}
                </pre>
            )}
        </div>
    )
}

function ResponsePanel({ responses }) {
    return (
        <div className="response-panel">
            <h2 className="response-title">Responses</h2>
            {responses.map((res, index) => (
                <ResponseCard key={index} res={res} />
            ))}
        </div>
    )
}

export default ResponsePanel
