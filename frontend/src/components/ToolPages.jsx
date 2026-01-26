/* src/components/ToolPages.jsx */
import React from 'react';

// --- Shared Styles ---
const pageStyle = {
    padding: '2rem',
    maxWidth: '800px',
    margin: '0 auto',
    fontFamily: "'Inter', sans-serif",
    color: '#1f2937'
};

const headerStyle = {
    fontSize: '2rem',
    marginBottom: '1rem',
    color: '#4f46e5', // INDIGO-600
    fontWeight: 'bold'
};

const cardStyle = {
    background: 'white',
    padding: '2rem',
    borderRadius: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    marginBottom: '1.5rem',
    border: '1px solid #f3f4f6'
};

const btnStyle = {
    background: '#4f46e5',
    color: 'white',
    border: 'none',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: '500'
};

// --- Pages ---

export function BookingPage() {
    return (
        <div style={pageStyle}>
            <h1 style={headerStyle}>📅 Book Your Stay</h1>
            <div style={cardStyle}>
                <h3>Check Availability</h3>
                <p style={{ marginBottom: '1rem', color: '#6b7280' }}>Find the perfect room for your next escape.</p>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '1rem' }}>
                    <input type="date" style={{ padding: '10px', borderRadius: '8px', border: '1px solid #d1d5db' }} />
                    <input type="date" style={{ padding: '10px', borderRadius: '8px', border: '1px solid #d1d5db' }} />
                    <button style={btnStyle}>Search Rooms</button>
                </div>
            </div>

            <div style={cardStyle}>
                <h3>Current Offers</h3>
                <ul style={{ paddingLeft: '1.5rem', color: '#4b5563' }}>
                    <li><strong>Weekend Escape:</strong> Stay 2 nights, save 15%.</li>
                    <li><strong>Romance Package:</strong> Includes champagne & late checkout.</li>
                </ul>
            </div>
        </div>
    );
}

export function GuidePage() {
    return (
        <div style={pageStyle}>
            <h1 style={headerStyle}>🗺️ Hobart Insider Guide</h1>

            <div style={cardStyle}>
                <h3>🎨 MONA (Museum of Old and New Art)</h3>
                <p>The "Subversive Adult Disneyland". A must-see.</p>
                <p><strong>Top Tip:</strong> Take the "Posh Pit" ferry for free champagne.</p>
                <button style={{ ...btnStyle, background: '#1c1917', marginTop: '10px' }}>View Ferry Schedule</button>
            </div>

            <div style={cardStyle}>
                <h3>🛒 Salamanca Market</h3>
                <p><strong>When:</strong> Saturdays, 8:30 AM - 3:00 PM.</p>
                <p>Famous for Tasmanian timber, hand-blown glass, and the legendary <strong>Scallop Pies</strong>.</p>
            </div>

            <div style={cardStyle}>
                <h3>🌦️ Weather Warning</h3>
                <p>"Four seasons in one day." Always bring a jacket!</p>
            </div>
        </div>
    );
}

export function WiFiPage() {
    return (
        <div style={pageStyle}>
            <h1 style={headerStyle}>📶 WiFi Connection</h1>

            <div style={{ ...cardStyle, textAlign: 'center' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📲</div>
                <h3>Free High-Speed Internet</h3>
                <p style={{ fontSize: '1.2rem', margin: '1rem 0' }}>Network: <strong>SouthernHorizons_Guest</strong></p>
                <p style={{ fontSize: '1.2rem' }}>Password: <strong>(No Password Required)</strong></p>
                <button style={{ ...btnStyle, marginTop: '1rem' }}>Connect Now</button>
            </div>

            <div style={cardStyle}>
                <h3>Troubleshooting</h3>
                <p>If you cannot connect, please try forgetting the network and re-joining, or contact Reception.</p>
            </div>
        </div>
    );
}

export function ReceptionPage() {
    return (
        <div style={pageStyle}>
            <h1 style={headerStyle}>🛎️ Reception & Concierge</h1>

            <div style={cardStyle}>
                <h3>We are here 24/7</h3>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                    <button style={btnStyle}>📞 Call Front Desk</button>
                    <button style={{ ...btnStyle, background: '#10b981' }}>💬 Chat with Staff</button>
                </div>
            </div>

            {/* New Instant Service Requests Section */}
            <div style={cardStyle}>
                <h3>🛎️ Instant Service Requests</h3>
                <p style={{ marginBottom: '1rem', color: '#6b7280' }}>Tap to request immediately. Estimated time: 10 mins.</p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <button style={{ ...btnStyle, background: 'white', color: '#1f2937', border: '1px solid #d1d5db', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => alert("Request sent: Fresh Towels 🧖\nHousekeeping has been notified.")}>
                        🧖 Towels
                    </button>
                    <button style={{ ...btnStyle, background: 'white', color: '#1f2937', border: '1px solid #d1d5db', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => alert("Request sent: Bottled Water 💧\nRoom Service is on the way.")}>
                        💧 Water
                    </button>
                    <button style={{ ...btnStyle, background: 'white', color: '#1f2937', border: '1px solid #d1d5db', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => alert("Request sent: Valet Retrieval 🚗\nYour car will be ready in 15 mins.")}>
                        🚗 My Car
                    </button>
                    <button style={{ ...btnStyle, background: 'white', color: '#1f2937', border: '1px solid #d1d5db', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => alert("Request sent: Late Checkout 🕐\nReception will confirm availability shortly.")}>
                        🕐 Checkout
                    </button>
                </div>
            </div>

            <div style={cardStyle}>
                <h3>Services</h3>
                <ul style={{ paddingLeft: '1.5rem', color: '#4b5563', lineHeight: '1.8' }}>
                    <li>🧳 Luggage Storage</li>
                    <li>🚕 Taxi Booking</li>
                    <li>⏰ Wake-up Calls</li>
                </ul>
            </div>
        </div>
    );
}
