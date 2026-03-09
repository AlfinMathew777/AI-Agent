import { useState } from "react";
import { 
  Sparkles, Calendar, Users, ArrowRight, ChevronRight, 
  MapPin, Phone, Mail, Star, Utensils, Waves, Wine, 
  Bed, Coffee, Car, Clock
} from "lucide-react";

// Luxury Hotel Images
const IMAGES = {
  hero: "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1920&q=80",
  lobby: "https://images.unsplash.com/photo-1768396747960-ae6ba3c855bc?w=800&q=80",
  suite1: "https://images.unsplash.com/photo-1609602126247-4ab7188b4aa1?w=800&q=80",
  suite2: "https://images.unsplash.com/photo-1709187516056-d4929b67e89f?w=800&q=80",
  dining: "https://images.unsplash.com/photo-1703565426315-4209c2e88eea?w=800&q=80",
  spa: "https://images.unsplash.com/photo-1758973470049-4514352776eb?w=800&q=80",
  pool: "https://images.unsplash.com/photo-1711714956204-e1d84e4d8879?w=800&q=80",
};

const EXPERIENCES = [
  { 
    title: "Suites & Rooms", 
    subtitle: "Refined comfort", 
    image: IMAGES.suite1,
    link: "/rooms" 
  },
  { 
    title: "Fine Dining", 
    subtitle: "Culinary excellence", 
    image: IMAGES.dining,
    link: "/dining" 
  },
  { 
    title: "Wellness & Spa", 
    subtitle: "Rejuvenation awaits", 
    image: IMAGES.spa,
    link: "/wellness" 
  },
  { 
    title: "Local Experiences", 
    subtitle: "Curated journeys", 
    image: IMAGES.pool,
    link: "/experiences" 
  },
];

const ROOMS = [
  { 
    type: "Deluxe Room", 
    price: 260, 
    image: IMAGES.suite2, 
    features: ["King Bed", "City View", "40 sqm"],
    aiRecommended: false
  },
  { 
    type: "Ocean View Suite", 
    price: 420, 
    image: IMAGES.suite1, 
    features: ["King Bed", "Ocean View", "65 sqm", "Living Area"],
    aiRecommended: true
  },
  { 
    type: "Penthouse", 
    price: 780, 
    image: IMAGES.lobby, 
    features: ["King Bed", "Panoramic View", "120 sqm", "Private Terrace"],
    aiRecommended: false
  },
];

export default function LuxuryLanding({ onNavigate, onLogin, VIEWS }) {
  const [showConcierge, setShowConcierge] = useState(false);
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(2);

  const today = new Date().toISOString().split("T")[0];

  const handleBookNow = () => {
    onNavigate(VIEWS.CHAT);
  };

  const handleConcierge = () => {
    onNavigate(VIEWS.CHAT);
  };

  return (
    <div style={{ background: "#F7F3EE", color: "#0F1115", minHeight: "100vh" }}>
      {/* Navigation */}
      <nav style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        padding: "0 2rem",
        height: 80,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(247,243,238,0.9)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(217,210,199,0.5)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ 
            fontFamily: "'Cormorant Garamond', serif", 
            fontSize: "1.5rem", 
            fontWeight: 400,
            letterSpacing: "-0.02em",
            color: "#0F1115"
          }}>
            Southern Horizons
          </span>
          <span style={{ 
            fontSize: "0.6rem", 
            letterSpacing: "0.2em", 
            textTransform: "uppercase",
            color: "#8C6A43",
            fontWeight: 500
          }}>
            Hotel
          </span>
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: 32, fontFamily: "'Manrope', sans-serif", fontSize: "0.8rem", letterSpacing: "0.05em" }}>
          <a href="#rooms" style={{ color: "#5A5A5A", textDecoration: "none", transition: "color 0.2s" }}>Rooms</a>
          <a href="#dining" style={{ color: "#5A5A5A", textDecoration: "none", transition: "color 0.2s" }}>Dining</a>
          <a href="#experiences" style={{ color: "#5A5A5A", textDecoration: "none", transition: "color 0.2s" }}>Experiences</a>
          <a href="#contact" style={{ color: "#5A5A5A", textDecoration: "none", transition: "color 0.2s" }}>Contact</a>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button 
            onClick={onLogin}
            data-testid="nav-staff-login"
            style={{
              padding: "0.6rem 1.25rem",
              background: "transparent",
              border: "1px solid #D9D2C7",
              color: "#5A5A5A",
              fontSize: "0.75rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              cursor: "pointer",
              fontFamily: "'Manrope', sans-serif",
              transition: "all 0.2s"
            }}
          >
            Staff Portal
          </button>
          <button 
            onClick={handleBookNow}
            data-testid="nav-book-now"
            style={{
              padding: "0.6rem 1.5rem",
              background: "#C6A66B",
              border: "none",
              color: "#0F1115",
              fontSize: "0.75rem",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              cursor: "pointer",
              fontFamily: "'Manrope', sans-serif",
              fontWeight: 500,
              transition: "all 0.2s"
            }}
          >
            Reserve Now
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        position: "relative",
        height: "100vh",
        minHeight: 700,
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-end"
      }}>
        {/* Hero Background */}
        <div style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `url(${IMAGES.hero})`,
          backgroundSize: "cover",
          backgroundPosition: "center"
        }} />
        <div style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(to top, rgba(15,17,21,0.8) 0%, rgba(15,17,21,0.2) 50%, transparent 100%)"
        }} />

        {/* Hero Content */}
        <div style={{
          position: "relative",
          zIndex: 2,
          padding: "0 2rem 8rem",
          maxWidth: 1400,
          margin: "0 auto",
          width: "100%"
        }}>
          <div className="animate-fade-in-up" style={{ maxWidth: 700 }}>
            <p style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "0.75rem",
              letterSpacing: "0.25em",
              textTransform: "uppercase",
              color: "#C6A66B",
              marginBottom: "1.5rem"
            }}>
              Experience Refined Hospitality
            </p>
            <h1 style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: "clamp(3rem, 7vw, 5.5rem)",
              fontWeight: 300,
              lineHeight: 1,
              color: "#F7F3EE",
              marginBottom: "1.5rem",
              letterSpacing: "-0.02em"
            }}>
              Where Luxury Meets
              <br />
              <span style={{ fontStyle: "italic", color: "#C6A66B" }}>Intelligence</span>
            </h1>
            <p style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "1rem",
              color: "#D9D2C7",
              lineHeight: 1.8,
              maxWidth: 500,
              marginBottom: "2.5rem"
            }}>
              An exquisite coastal retreat enhanced by AI-powered service. 
              Let our intelligent concierge craft your perfect stay.
            </p>
            
            <div style={{ display: "flex", gap: 16 }}>
              <button 
                onClick={handleBookNow}
                data-testid="hero-reserve-btn"
                className="btn-gold"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10
                }}
              >
                Reserve Your Stay <ArrowRight size={16} />
              </button>
              <button 
                onClick={handleConcierge}
                data-testid="hero-concierge-btn"
                className="btn-ghost"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10
                }}
              >
                <Sparkles size={16} /> Ask AI Concierge
              </button>
            </div>
          </div>
        </div>

        {/* Floating Booking Bar */}
        <div style={{
          position: "absolute",
          bottom: 0,
          left: "50%",
          transform: "translateX(-50%) translateY(50%)",
          zIndex: 10,
          width: "90%",
          maxWidth: 1000
        }}>
          <div className="booking-bar" style={{
            display: "flex",
            alignItems: "center",
            gap: 0,
            padding: "0.5rem",
            borderRadius: 2
          }}>
            <div style={{ flex: 1, padding: "1rem 1.5rem", borderRight: "1px solid #D9D2C7" }}>
              <label style={{ 
                display: "block", 
                fontSize: "0.65rem", 
                letterSpacing: "0.15em", 
                textTransform: "uppercase", 
                color: "#8C6A43", 
                marginBottom: 6,
                fontWeight: 500
              }}>Check-in</label>
              <input 
                type="date" 
                value={checkIn}
                min={today}
                onChange={(e) => setCheckIn(e.target.value)}
                data-testid="booking-checkin"
                style={{
                  width: "100%",
                  border: "none",
                  background: "transparent",
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: "0.9rem",
                  color: "#0F1115",
                  outline: "none"
                }}
              />
            </div>
            <div style={{ flex: 1, padding: "1rem 1.5rem", borderRight: "1px solid #D9D2C7" }}>
              <label style={{ 
                display: "block", 
                fontSize: "0.65rem", 
                letterSpacing: "0.15em", 
                textTransform: "uppercase", 
                color: "#8C6A43", 
                marginBottom: 6,
                fontWeight: 500
              }}>Check-out</label>
              <input 
                type="date" 
                value={checkOut}
                min={checkIn || today}
                onChange={(e) => setCheckOut(e.target.value)}
                data-testid="booking-checkout"
                style={{
                  width: "100%",
                  border: "none",
                  background: "transparent",
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: "0.9rem",
                  color: "#0F1115",
                  outline: "none"
                }}
              />
            </div>
            <div style={{ flex: 1, padding: "1rem 1.5rem", borderRight: "1px solid #D9D2C7" }}>
              <label style={{ 
                display: "block", 
                fontSize: "0.65rem", 
                letterSpacing: "0.15em", 
                textTransform: "uppercase", 
                color: "#8C6A43", 
                marginBottom: 6,
                fontWeight: 500
              }}>Guests</label>
              <select 
                value={guests}
                onChange={(e) => setGuests(Number(e.target.value))}
                data-testid="booking-guests"
                style={{
                  width: "100%",
                  border: "none",
                  background: "transparent",
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: "0.9rem",
                  color: "#0F1115",
                  outline: "none",
                  cursor: "pointer"
                }}
              >
                {[1,2,3,4,5,6].map(n => (
                  <option key={n} value={n}>{n} {n === 1 ? 'Guest' : 'Guests'}</option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", gap: 8, padding: "0.5rem" }}>
              <button 
                onClick={handleBookNow}
                data-testid="booking-check-btn"
                style={{
                  padding: "1rem 2rem",
                  background: "#C6A66B",
                  border: "none",
                  color: "#0F1115",
                  fontSize: "0.7rem",
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  cursor: "pointer",
                  fontFamily: "'Manrope', sans-serif",
                  fontWeight: 600,
                  whiteSpace: "nowrap"
                }}
              >
                Check Availability
              </button>
              <button 
                onClick={handleConcierge}
                data-testid="booking-ai-btn"
                style={{
                  padding: "1rem",
                  background: "transparent",
                  border: "1px solid #D9D2C7",
                  color: "#8C6A43",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: "0.7rem",
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  fontFamily: "'Manrope', sans-serif",
                  whiteSpace: "nowrap"
                }}
              >
                <Sparkles size={14} /> AI Help
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Intro Section */}
      <section style={{ 
        padding: "10rem 2rem 6rem", 
        maxWidth: 900, 
        margin: "0 auto", 
        textAlign: "center" 
      }}>
        <p style={{
          fontFamily: "'Manrope', sans-serif",
          fontSize: "0.7rem",
          letterSpacing: "0.25em",
          textTransform: "uppercase",
          color: "#C6A66B",
          marginBottom: "1.5rem"
        }}>
          Welcome to Southern Horizons
        </p>
        <h2 style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontSize: "clamp(2rem, 4vw, 3rem)",
          fontWeight: 300,
          lineHeight: 1.2,
          color: "#0F1115",
          marginBottom: "1.5rem"
        }}>
          Where every moment is crafted with intention
        </h2>
        <div className="divider-gold" style={{ margin: "1.5rem auto" }} />
        <p style={{
          fontFamily: "'Manrope', sans-serif",
          fontSize: "1rem",
          color: "#5A5A5A",
          lineHeight: 1.9,
          maxWidth: 650,
          margin: "0 auto"
        }}>
          Nestled along pristine shores, Southern Horizons offers an unparalleled blend of 
          timeless elegance and intelligent hospitality. Our AI concierge anticipates your 
          every desire, ensuring a seamless and deeply personalized experience.
        </p>
      </section>

      {/* Experiences Section */}
      <section id="experiences" style={{ padding: "4rem 2rem 8rem" }}>
        <div style={{ maxWidth: 1400, margin: "0 auto" }}>
          <div style={{ marginBottom: "3rem" }}>
            <p style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "0.7rem",
              letterSpacing: "0.25em",
              textTransform: "uppercase",
              color: "#C6A66B",
              marginBottom: "0.75rem"
            }}>
              Signature Experiences
            </p>
            <h2 style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
              fontWeight: 300,
              color: "#0F1115"
            }}>
              Discover Your Perfect Stay
            </h2>
          </div>

          {/* Bento Grid */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(12, 1fr)",
            gap: "1rem"
          }}>
            {/* Large Experience Card */}
            <div 
              className="experience-card"
              style={{ gridColumn: "span 8", aspectRatio: "16/9", borderRadius: 2, cursor: "pointer" }}
            >
              <img src={EXPERIENCES[0].image} alt={EXPERIENCES[0].title} loading="lazy" />
              <div className="experience-card-overlay">
                <p style={{ 
                  fontSize: "0.65rem", 
                  letterSpacing: "0.2em", 
                  textTransform: "uppercase", 
                  color: "#C6A66B", 
                  marginBottom: 8 
                }}>
                  {EXPERIENCES[0].subtitle}
                </p>
                <h3 style={{ 
                  fontFamily: "'Cormorant Garamond', serif", 
                  fontSize: "2rem", 
                  fontWeight: 300, 
                  color: "#F7F3EE",
                  marginBottom: 12
                }}>
                  {EXPERIENCES[0].title}
                </h3>
                <span style={{ 
                  display: "inline-flex", 
                  alignItems: "center", 
                  gap: 8, 
                  fontSize: "0.75rem", 
                  color: "#C6A66B",
                  fontFamily: "'Manrope', sans-serif",
                  letterSpacing: "0.1em"
                }}>
                  Explore <ChevronRight size={14} />
                </span>
              </div>
            </div>

            {/* Small Experience Cards */}
            <div style={{ gridColumn: "span 4", display: "flex", flexDirection: "column", gap: "1rem" }}>
              {EXPERIENCES.slice(1, 3).map((exp, idx) => (
                <div 
                  key={idx}
                  className="experience-card"
                  style={{ flex: 1, borderRadius: 2, cursor: "pointer" }}
                >
                  <img src={exp.image} alt={exp.title} loading="lazy" />
                  <div className="experience-card-overlay">
                    <p style={{ 
                      fontSize: "0.6rem", 
                      letterSpacing: "0.2em", 
                      textTransform: "uppercase", 
                      color: "#C6A66B", 
                      marginBottom: 4 
                    }}>
                      {exp.subtitle}
                    </p>
                    <h3 style={{ 
                      fontFamily: "'Cormorant Garamond', serif", 
                      fontSize: "1.25rem", 
                      fontWeight: 300, 
                      color: "#F7F3EE" 
                    }}>
                      {exp.title}
                    </h3>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* AI Concierge Section */}
      <section style={{ 
        padding: "6rem 2rem", 
        background: "#0F1115",
        color: "#F7F3EE"
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", textAlign: "center" }}>
          <div className="ai-badge" style={{ margin: "0 auto 1.5rem", display: "inline-flex" }}>
            <Sparkles size={12} /> AI-Powered
          </div>
          <h2 style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: "clamp(2rem, 4vw, 3rem)",
            fontWeight: 300,
            marginBottom: "1rem"
          }}>
            An Intelligent Concierge
            <br />
            <span style={{ fontStyle: "italic", color: "#C6A66B" }}>for Every Guest</span>
          </h2>
          <p style={{
            fontFamily: "'Manrope', sans-serif",
            fontSize: "0.95rem",
            color: "#94A3B8",
            lineHeight: 1.8,
            maxWidth: 600,
            margin: "0 auto 3rem"
          }}>
            Our AI concierge understands your preferences and curates personalized 
            recommendations — from the perfect suite to bespoke dining experiences.
          </p>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "2rem",
            maxWidth: 900,
            margin: "0 auto 3rem"
          }}>
            {[
              { icon: Bed, title: "Choose Your Suite", desc: "Intelligent room matching based on your preferences" },
              { icon: Coffee, title: "Add Premium Services", desc: "Breakfast, transfers, spa — seamlessly integrated" },
              { icon: Clock, title: "Book in Minutes", desc: "Complete your reservation with secure payment" }
            ].map((item, idx) => (
              <div key={idx} style={{ textAlign: "center", padding: "1.5rem" }}>
                <div style={{
                  width: 60,
                  height: 60,
                  border: "1px solid #C6A66B",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 1rem"
                }}>
                  <item.icon size={24} color="#C6A66B" strokeWidth={1} />
                </div>
                <h4 style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: "1.25rem",
                  fontWeight: 400,
                  marginBottom: "0.5rem"
                }}>
                  {item.title}
                </h4>
                <p style={{
                  fontFamily: "'Manrope', sans-serif",
                  fontSize: "0.85rem",
                  color: "#94A3B8"
                }}>
                  {item.desc}
                </p>
              </div>
            ))}
          </div>

          <button 
            onClick={handleConcierge}
            data-testid="ai-section-btn"
            style={{
              padding: "1rem 2.5rem",
              background: "#C6A66B",
              border: "none",
              color: "#0F1115",
              fontSize: "0.75rem",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              cursor: "pointer",
              fontFamily: "'Manrope', sans-serif",
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: 10
            }}
          >
            <Sparkles size={16} /> Start Planning Your Stay
          </button>
        </div>
      </section>

      {/* Rooms Preview */}
      <section id="rooms" style={{ padding: "8rem 2rem", background: "#F7F3EE" }}>
        <div style={{ maxWidth: 1400, margin: "0 auto" }}>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "flex-end", 
            marginBottom: "3rem" 
          }}>
            <div>
              <p style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.7rem",
                letterSpacing: "0.25em",
                textTransform: "uppercase",
                color: "#C6A66B",
                marginBottom: "0.75rem"
              }}>
                Accommodations
              </p>
              <h2 style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
                fontWeight: 300,
                color: "#0F1115"
              }}>
                Suites & Rooms
              </h2>
            </div>
            <a href="#" style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: "0.8rem",
              color: "#8C6A43",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: 8,
              letterSpacing: "0.05em"
            }}>
              View All Rooms <ArrowRight size={16} />
            </a>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "1.5rem"
          }}>
            {ROOMS.map((room, idx) => (
              <div 
                key={idx} 
                className="room-card"
                style={{ borderRadius: 2, overflow: "hidden", cursor: "pointer" }}
              >
                <div style={{ position: "relative", aspectRatio: "4/3", overflow: "hidden" }}>
                  <img 
                    src={room.image} 
                    alt={room.type}
                    style={{ width: "100%", height: "100%", objectFit: "cover", transition: "transform 0.6s" }}
                    loading="lazy"
                  />
                  {room.aiRecommended && (
                    <div className="ai-badge" style={{ 
                      position: "absolute", 
                      top: 16, 
                      left: 16,
                      background: "rgba(247,243,238,0.95)"
                    }}>
                      <Sparkles size={10} /> AI Recommended
                    </div>
                  )}
                </div>
                <div style={{ padding: "1.5rem" }}>
                  <h3 style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: "1.5rem",
                    fontWeight: 400,
                    color: "#0F1115",
                    marginBottom: "0.75rem"
                  }}>
                    {room.type}
                  </h3>
                  <div style={{ 
                    display: "flex", 
                    flexWrap: "wrap", 
                    gap: "0.5rem", 
                    marginBottom: "1rem" 
                  }}>
                    {room.features.map((f, i) => (
                      <span key={i} style={{
                        fontSize: "0.7rem",
                        color: "#5A5A5A",
                        padding: "0.25rem 0.5rem",
                        background: "#E5E0D8",
                        borderRadius: 2,
                        fontFamily: "'Manrope', sans-serif"
                      }}>
                        {f}
                      </span>
                    ))}
                  </div>
                  <div style={{ 
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center" 
                  }}>
                    <div>
                      <span style={{ 
                        fontFamily: "'Cormorant Garamond', serif", 
                        fontSize: "1.5rem", 
                        color: "#0F1115" 
                      }}>
                        ${room.price}
                      </span>
                      <span style={{ 
                        fontSize: "0.75rem", 
                        color: "#8A8A8A", 
                        marginLeft: 4,
                        fontFamily: "'Manrope', sans-serif"
                      }}>
                        / night
                      </span>
                    </div>
                    <button style={{
                      padding: "0.5rem 1rem",
                      background: "transparent",
                      border: "1px solid #D9D2C7",
                      color: "#8C6A43",
                      fontSize: "0.7rem",
                      letterSpacing: "0.1em",
                      textTransform: "uppercase",
                      cursor: "pointer",
                      fontFamily: "'Manrope', sans-serif"
                    }}>
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section style={{ 
        padding: "5rem 2rem", 
        background: "#FDFCFA",
        borderTop: "1px solid #E5E0D8",
        borderBottom: "1px solid #E5E0D8"
      }}>
        <div style={{ 
          maxWidth: 1200, 
          margin: "0 auto", 
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "3rem",
          textAlign: "center"
        }}>
          {[
            { value: "5", label: "Star Rating" },
            { value: "86", label: "Luxury Suites" },
            { value: "24/7", label: "AI Concierge" },
            { value: "100%", label: "Guest Satisfaction" }
          ].map((stat, idx) => (
            <div key={idx}>
              <div style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: "3rem",
                fontWeight: 300,
                color: "#C6A66B",
                marginBottom: "0.5rem"
              }}>
                {stat.value}
              </div>
              <div style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.75rem",
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                color: "#5A5A5A"
              }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section style={{
        padding: "8rem 2rem",
        background: `linear-gradient(rgba(15,17,21,0.85), rgba(15,17,21,0.85)), url(${IMAGES.lobby})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        textAlign: "center"
      }}>
        <div style={{ maxWidth: 700, margin: "0 auto" }}>
          <h2 style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: "clamp(2rem, 5vw, 3.5rem)",
            fontWeight: 300,
            color: "#F7F3EE",
            marginBottom: "1.5rem"
          }}>
            Begin Your Journey
          </h2>
          <p style={{
            fontFamily: "'Manrope', sans-serif",
            fontSize: "1rem",
            color: "#D9D2C7",
            marginBottom: "2.5rem"
          }}>
            Let our intelligent concierge help you plan the perfect stay.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 16 }}>
            <button 
              onClick={handleBookNow}
              data-testid="cta-reserve-btn"
              style={{
                padding: "1rem 2.5rem",
                background: "#C6A66B",
                border: "none",
                color: "#0F1115",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Manrope', sans-serif",
                fontWeight: 600
              }}
            >
              Reserve Now
            </button>
            <button 
              onClick={handleConcierge}
              data-testid="cta-concierge-btn"
              style={{
                padding: "1rem 2.5rem",
                background: "transparent",
                border: "1px solid rgba(247,243,238,0.3)",
                color: "#F7F3EE",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                cursor: "pointer",
                fontFamily: "'Manrope', sans-serif",
                display: "flex",
                alignItems: "center",
                gap: 10
              }}
            >
              <Sparkles size={16} /> Ask Concierge
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="luxury-footer">
        <div style={{ maxWidth: 1400, margin: "0 auto", padding: "0 2rem" }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "2fr 1fr 1fr 1fr",
            gap: "4rem",
            marginBottom: "4rem"
          }}>
            <div>
              <h3 style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: "1.75rem",
                fontWeight: 300,
                marginBottom: "1rem"
              }}>
                Southern Horizons
              </h3>
              <p style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.9rem",
                color: "#94A3B8",
                lineHeight: 1.8,
                maxWidth: 300
              }}>
                An exquisite coastal retreat where luxury meets intelligent 
                hospitality. Experience the future of personalized service.
              </p>
            </div>
            <div>
              <h4 style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.7rem",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                marginBottom: "1.5rem",
                color: "#C6A66B"
              }}>
                Explore
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <li><a href="#">Rooms & Suites</a></li>
                <li><a href="#">Dining</a></li>
                <li><a href="#">Wellness</a></li>
                <li><a href="#">Experiences</a></li>
              </ul>
            </div>
            <div>
              <h4 style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.7rem",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                marginBottom: "1.5rem",
                color: "#C6A66B"
              }}>
                Information
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <li><a href="#">About Us</a></li>
                <li><a href="#">Offers</a></li>
                <li><a href="#">Contact</a></li>
                <li><a href="#">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.7rem",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                marginBottom: "1.5rem",
                color: "#C6A66B"
              }}>
                Contact
              </h4>
              <div style={{ 
                display: "flex", 
                flexDirection: "column", 
                gap: "0.75rem",
                fontFamily: "'Manrope', sans-serif",
                fontSize: "0.9rem",
                color: "#94A3B8"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <MapPin size={16} color="#C6A66B" />
                  <span>123 Coastal Drive, Paradise Bay</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Phone size={16} color="#C6A66B" />
                  <span>+1 (555) 123-4567</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Mail size={16} color="#C6A66B" />
                  <span>concierge@southernhorizons.com</span>
                </div>
              </div>
            </div>
          </div>

          <div style={{
            borderTop: "1px solid rgba(148,163,184,0.2)",
            paddingTop: "2rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontFamily: "'Manrope', sans-serif",
            fontSize: "0.8rem",
            color: "#64748B"
          }}>
            <span>© 2026 Southern Horizons Hotel. All rights reserved.</span>
            <div style={{ display: "flex", gap: "2rem" }}>
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
