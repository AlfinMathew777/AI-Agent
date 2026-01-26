
import "./LandingPage.css";

export default function LandingPage({ onNavigate }) {
    return (
        <div className="landing-page">
            {/* Hero Section */}
            <header className="hero">
                <div className="hero-content">
                    <h1>Experience Luxury Beyond Horizon</h1>
                    <p>Southern Horizons Hotel & Casino</p>
                    <button className="book-btn" onClick={() => onNavigate("book")}>Book Your Stay</button>
                </div>
            </header>

            {/* Featured Section */}
            <section className="features">
                <div className="feature-card">
                    <h3>🎰 World Class Casino</h3>
                    <p>Experience the thrill in our 24/7 Grand Horizon Casino.</p>
                </div>
                <div className="feature-card">
                    <h3>🍽️ Exquisite Dining</h3>
                    <p>From fresh seafood at Azure to authentic Teppanyaki.</p>
                </div>
                <div className="feature-card">
                    <h3>🍸 Nightlife</h3>
                    <p>Rooftop cocktails at sunset or dancing at Velvet Underground.</p>
                </div>
            </section>

            {/* Content Spacer */}
            <section className="about-section">
                <h2>A Sanctuary of Style</h2>
                <p>
                    Located on the pristine coastline, Southern Horizons brings you an
                    unparalleled blend of relaxation and excitement. Whether you are here
                    for business, our high-stakes poker rooms, or just a weekend getaway,
                    we promise an unforgettable experience.
                </p>
            </section>
        </div>
    );
}
