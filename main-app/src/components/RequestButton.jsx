import './RequestButton.css'

function RequestButton({ onClick, loading, disabled }) {
    return (
        <button
            className="request-btn"
            onClick={onClick}
            disabled={disabled}
        >
            {loading ? 'Sending...' : 'Send Request'}
        </button>
    )
}

export default RequestButton
