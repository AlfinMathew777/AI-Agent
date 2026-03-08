import { useState, useEffect } from "react";
import "./LandingPage.css";

export default function LandingPage({ onNavigate, onStaffLogin }) {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div className="landing-page">
            {/* Navigation Bar */}
            <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
                <div className="container">
                    <div className="navbar-brand">Southern Horizons</div>
                    <ul className="navbar-nav">
                        <li><a href="#rooms">Rooms</a></li>
                        <li><a href="#amenities">Amenities</a></li>
                        <li><a href="#experiences">Experiences</a></li>
                        <li><a href="#contact">Contact</a></li>
                        <li><button className="btn btn-primary" onClick={() => onNavigate("book")}>Book Now</button></li>
                        <li><button className="btn btn-outline btn-staff-login" onClick={onStaffLogin}>🔐 Staff Login</button></li>
                    </ul>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="hero">
                <div className="hero-background">
                    <img src="/images/hero.png" alt="Luxury Resort" />
                </div>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <p className="hero-subtitle">Welcome To Paradise</p>
                    <h1>Experience Luxury<br />Beyond the Horizon</h1>
                    <p className="hero-description">
                        Discover an unparalleled blend of sophistication, world-class amenities,
                        and breathtaking ocean views at Southern Horizons Hotel & Casino
                    </p>
                    <div className="hero-buttons">
                        <button className="btn btn-primary" onClick={() => onNavigate("book")}>
                            Reserve Your Stay
                        </button>
                        <button className="btn btn-ghost" onClick={() => document.getElementById('rooms').scrollIntoView({ behavior: 'smooth' })}>
                            Explore Rooms
                        </button>
                    </div>
                </div>
                <div className="scroll-indicator">
                    <span></span>
                </div>
            </section>

            {/* Rooms Section */}
            <section id="rooms" className="rooms-section">
                <div className="container">
                    <div className="section-header">
                        <p className="section-label">Accommodations</p>
                        <h2>Luxury Rooms & Suites</h2>
                        <p>Each room is meticulously designed to provide the ultimate comfort and elegance, featuring modern amenities and stunning views</p>
                    </div>

                    <div className="rooms-grid">
                        <div className="room-card">
                            <div className="room-image">
                                <img src="/images/suite.png" alt="Deluxe Ocean Suite" />
                                <div className="room-overlay"></div>
                            </div>
                            <div className="room-content">
                                <h3>Deluxe Ocean Suite</h3>
                                <div className="room-features">
                                    <span>👥 2 Guests</span>
                                    <span>🛏️ King Bed</span>
                                    <span>📐 65 m²</span>
                                </div>
                                <p>Spacious suite with floor-to-ceiling windows, private balcony, and breathtaking ocean panoramas. Premium furnishings and marble bathroom.</p>
                                <div className="room-footer">
                                    <div className="room-price">
                                        $450<span>/night</span>
                                    </div>
                                    <button className="btn btn-outline" onClick={() => onNavigate("book")}>Book Now</button>
                                </div>
                            </div>
                        </div>

                        <div className="room-card">
                            <div className="room-image">
                                <img src="/images/suite.png" alt="Grand Presidential Suite" />
                                <div className="room-overlay"></div>
                            </div>
                            <div className="room-content">
                                <h3>Grand Presidential Suite</h3>
                                <div className="room-features">
                                    <span>👥 4 Guests</span>
                                    <span>🛏️ 2 King Beds</span>
                                    <span>📐 120 m²</span>
                                </div>
                                <p>Our crown jewel featuring separate living room, dining area, private terrace, and exclusive butler service. Ultimate luxury awaits.</p>
                                <div className="room-footer">
                                    <div className="room-price">
                                        $1,200<span>/night</span>
                                    </div>
                                    <button className="btn btn-outline" onClick={() => onNavigate("book")}>Book Now</button>
                                </div>
                            </div>
                        </div>

                        <div className="room-card">
                            <div className="room-image">
                                <img src="/images/suite.png" alt="Garden View Room" />
                                <div className="room-overlay"></div>
                            </div>
                            <div className="room-content">
                                <h3>Garden View Room</h3>
                                <div className="room-features">
                                    <span>👥 2 Guests</span>
                                    <span>🛏️ Queen Bed</span>
                                    <span>📐 45 m²</span>
                                </div>
                                <p>Elegant room overlooking lush tropical gardens, featuring contemporary design, premium bedding, and modern entertainment system.</p>
                                <div className="room-footer">
                                    <div className="room-price">
                                        $320<span>/night</span>
                                    </div>
                                    <button className="btn btn-outline" onClick={() => onNavigate("book")}>Book Now</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Amenities Section */}
            <section id="amenities" className="amenities-section">
                <div className="container">
                    <div className="section-header">
                        <p className="section-label">World-Class Facilities</p>
                        <h2>Exceptional Amenities</h2>
                        <p>Indulge in our comprehensive range of luxury amenities designed to elevate your stay</p>
                    </div>

                    <div className="amenities-grid">
                        <div className="amenity-card">
                            <div className="amenity-icon">🏊</div>
                            <h3>Infinity Pool</h3>
                            <p>Multiple temperature-controlled pools with swim-up bars and stunning ocean views. Open 24/7 for your convenience.</p>
                        </div>

                        <div className="amenity-card">
                            <div className="amenity-icon">💆</div>
                            <h3>Luxury Spa</h3>
                            <p>Award-winning spa featuring holistic treatments, sauna, steam room, and expert therapists for ultimate relaxation.</p>
                        </div>

                        <div className="amenity-card">
                            <div className="amenity-icon">🏋️</div>
                            <h3>Fitness Center</h3>
                            <p>State-of-the-art gym with latest equipment, personal trainers, yoga studio, and panoramic ocean views.</p>
                        </div>

                        <div className="amenity-card">
                            <div className="amenity-icon">🎰</div>
                            <h3>Grand Casino</h3>
                            <p>24/7 gaming floor with slot machines, table games, VIP salons, and exclusive high-roller lounges.</p>
                        </div>

                        <div className="amenity-card">
                            <div className="amenity-icon">🍽️</div>
                            <h3>Fine Dining</h3>
                            <p>Five signature restaurants featuring Michelin-star chefs, international cuisine, and exquisite wine cellars.</p>
                        </div>

                        <div className="amenity-card">
                            <div className="amenity-icon">🎪</div>
                            <h3>Event Spaces</h3>
                            <p>Elegant ballrooms and conference facilities for weddings, corporate events, and exclusive gatherings.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Experiences Section */}
            <section id="experiences" className="experience-section">
                <div className="container">
                    <div className="section-header">
                        <p className="section-label">Discover More</p>
                        <h2>Unforgettable Experiences</h2>
                        <p>Create lasting memories with our curated selection of premium experiences</p>
                    </div>

                    <div className="experience-grid">
                        <div className="experience-card">
                            <img src="/images/dining.png" alt="Fine Dining Experience" />
                            <div className="experience-overlay">
                                <h3>Culinary Excellence</h3>
                                <p>Embark on a gastronomic journey with world-renowned chefs and sommelier-curated wine pairings</p>
                            </div>
                        </div>

                        <div className="experience-card">
                            <img src="/images/spa.png" alt="Spa & Wellness" />
                            <div className="experience-overlay">
                                <h3>Wellness & Relaxation</h3>
                                <p>Rejuvenate your mind and body with our signature spa treatments and wellness programs</p>
                            </div>
                        </div>

                        <div className="experience-card">
                            <img src="/images/hero.png" alt="Beach Activities" />
                            <div className="experience-overlay">
                                <h3>Ocean Adventures</h3>
                                <p>Explore pristine beaches, water sports, yacht excursions, and private island getaways</p>
                            </div>
                        </div>

                        <div className="experience-card">
                            <img src="/images/dining.png" alt="Nightlife & Entertainment" />
                            <div className="experience-overlay">
                                <h3>Nightlife & Entertainment</h3>
                                <p>Experience vibrant nightlife with live performances, rooftop lounges, and exclusive VIP clubs</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section">
                <div className="container">
                    <h2>Your Luxury Escape Awaits</h2>
                    <p>Book your stay today and discover why Southern Horizons is the premier destination for discerning travelers</p>
                    <button className="btn btn-primary" onClick={() => onNavigate("book")}>
                        Reserve Now
                    </button>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer" id="contact">
                <div className="container">
                    <div className="footer-content">
                        <div className="footer-section">
                            <h4>Southern Horizons</h4>
                            <p>Experience luxury beyond the horizon at our world-class resort and casino destination.</p>
                        </div>

                        <div className="footer-section">
                            <h4>Quick Links</h4>
                            <ul>
                                <li><a href="#rooms">Rooms & Suites</a></li>
                                <li><a href="#amenities">Amenities</a></li>
                                <li><a href="#experiences">Experiences</a></li>
                                <li><a href="#" onClick={() => onNavigate("book")}>Book Now</a></li>
                            </ul>
                        </div>

                        <div className="footer-section">
                            <h4>Services</h4>
                            <ul>
                                <li><a href="#">Spa & Wellness</a></li>
                                <li><a href="#">Dining</a></li>
                                <li><a href="#">Casino</a></li>
                                <li><a href="#">Events</a></li>
                            </ul>
                        </div>

                        <div className="footer-section">
                            <h4>Contact</h4>
                            <ul>
                                <li>📍 1 Ocean Boulevard, Paradise Bay</li>
                                <li>📞 +1 (800) 555-LUXURY</li>
                                <li>✉️ reservations@southernhorizons.com</li>
                                <li>🕐 24/7 Concierge Service</li>
                            </ul>
                        </div>
                    </div>

                    {/* Staff & Admin Portal Access */}
                    <div className="footer-staff-section">
                        <div className="staff-access-box">
                            <h4>🔐 Staff & Admin Access</h4>
                            <p>Hotel employees: Access your staff portal, admin dashboard, and internal tools</p>
                            <button className="btn btn-outline" onClick={onStaffLogin}>
                                Login to Portal
                            </button>
                        </div>
                    </div>

                    <div className="footer-bottom">
                        <p>&copy; 2026 Southern Horizons Hotel & Casino. All rights reserved. | Privacy Policy | Terms of Service</p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
