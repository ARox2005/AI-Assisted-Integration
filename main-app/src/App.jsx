import { useState } from 'react'
import ServiceToggle from './components/ServiceToggle'
import RequestButton from './components/RequestButton'
import ResponsePanel from './components/ResponsePanel'
import './App.css'

const MIDDLEWARE_BASE = import.meta.env.VITE_MIDDLEWARE_URL || 'http://localhost:8002/api/gateway/execute'
const ORCHESTRATOR_RESET_URL = import.meta.env.VITE_ORCHESTRATOR_RESET_URL || 'http://localhost:8003/api/orchestrator/reset-configs'

// Static test payloads for each service
const PAYLOADS = {
  kyc_provider: {
    applicant_data: {
      firstName: 'John',
      lastName: 'Doe',
      dateOfBirth: '1990-05-15',
      panNumber: 'ABCDE1234F',
      aadhaarLast4: '5678',
    },
  },
  gst_service: {
    business_data: {
      gstin: '29ABCDE1234F1Z5',
      businessName: 'Acme Corp Pvt Ltd',
      panNumber: 'ABCDE1234F',
    },
  },
}

const TENANTS = [
  { id: 'default', label: 'Default Tenant' },
  { id: 'tenant_a', label: 'Tenant A — Acme Corp' },
  { id: 'tenant_b', label: 'Tenant B — Beta Finance' },
]

function App() {
  const [kycEnabled, setKycEnabled] = useState(false)
  const [gstEnabled, setGstEnabled] = useState(false)
  const [responses, setResponses] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [tenantId, setTenantId] = useState('default')

  const handleSendRequest = async () => {
    // Determine which services are toggled on
    const services = []
    if (kycEnabled) services.push('kyc_provider')
    if (gstEnabled) services.push('gst_service')
    if (services.length === 0) {
      setError('Please enable at least one service (KYC or GST)')
      return
    }
    setLoading(true)
    setError(null)
    setResponses([])
    const results = []
    for (const service of services) {
      try {
        const res = await fetch(`${MIDDLEWARE_BASE}/${service}?tenant_id=${tenantId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(PAYLOADS[service]),
        })
        const data = await res.json()
        results.push({
          service,
          status: res.ok ? 'success' : 'error',
          statusCode: res.status,
          data,
        })
      } catch (err) {
        results.push({
          service,
          status: 'error',
          statusCode: null,
          data: { message: err.message },
        })
      }
    }
    setResponses(results)
    setLoading(false)
  }

  const handleResetConfigs = async () => {
    if (!confirm('Delete all deployed configs from middleware?')) return
    try {
      const res = await fetch(ORCHESTRATOR_RESET_URL, { method: 'POST' })
      const data = await res.json()
      alert(`Cleared ${data.count} config(s): ${data.deleted.join(', ') || 'none found'}`)
    } catch (err) {
      alert(`Reset failed: ${err.message}`)
    }
  }

  return (
    <div className="app-container">
      <h1 className="app-title">FinSpark Integration Tester</h1>
      <p className="app-subtitle">
        Toggle the services below and hit Send to test the middleware pipeline.
      </p>
      <div className="tenant-bar">
        <label htmlFor="tenant">🏢 Tenant:</label>
        <select id="tenant" value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
          {TENANTS.map((t) => (
            <option key={t.id} value={t.id}>{t.label}</option>
          ))}
        </select>
      </div>
      <div className="toggles-section">
        <ServiceToggle
          label="KYC Provider"
          enabled={kycEnabled}
          onToggle={() => setKycEnabled(!kycEnabled)}
        />
        <ServiceToggle
          label="GST Service"
          enabled={gstEnabled}
          onToggle={() => setGstEnabled(!gstEnabled)}
        />
      </div>
      <RequestButton
        onClick={handleSendRequest}
        loading={loading}
        disabled={loading}
      />
      <button className="btn-reset" onClick={handleResetConfigs}>
        Reset Configs
      </button>
      {error && <p className="error-text">{error}</p>}
      {responses.length > 0 && <ResponsePanel responses={responses} />}
    </div>
  )
}
export default App