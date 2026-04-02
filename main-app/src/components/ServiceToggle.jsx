import './ServiceToggle.css'

function ServiceToggle({ label, enabled, onToggle }) {
    return (
        <div className="toggle-container" onClick={onToggle}>
            <span className="toggle-label">{label}</span>
            <div className={`toggle-switch ${enabled ? 'active' : ''}`}>
                <div className="toggle-knob" />
            </div>
            <span className={`toggle-status ${enabled ? 'on' : 'off'}`}>
                {enabled ? 'ON' : 'OFF'}
            </span>
        </div>
    )
}

export default ServiceToggle