import { useState, useEffect } from "react";
import "./BookingPage.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8010";

export default function BookingPage({ onBack }) {
    const [checkIn, setCheckIn] = useState("");
    const [checkOut, setCheckOut] = useState("");
    const [roomType, setRoomType] = useState("");
    const [availableRooms, setAvailableRooms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searching, setSearching] = useState(false);

    // Booking form state
    const [selectedRoom, setSelectedRoom] = useState(null);
    const [guestName, setGuestName] = useState("");
    const [guestEmail, setGuestEmail] = useState("");
    const [guestPhone, setGuestPhone] = useState("");
    const [specialRequests, setSpecialRequests] = useState("");
    const [bookingSuccess, setBookingSuccess] = useState(null);

    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];

    const searchRooms = async () => {
        if (!checkIn || !checkOut) {
            setError("Please select both check-in and check-out dates");
            return;
        }

        if (new Date(checkIn) >= new Date(checkOut)) {
            setError("Check-out date must be after check-in date");
            return;
        }

        setSearching(true);
        setError(null);
        setLoading(true);

        try {
            const params = new URLSearchParams({
                check_in: checkIn,
                check_out: checkOut
            });

            if (roomType) {
                params.append('room_type', roomType);
            }

            const response = await fetch(`${API_BASE}/catalog/rooms?${params}`, {
                headers: {
                    "x-tenant-id": "default-tenant-0000"
                }
            });

            if (!response.ok) {
                throw new Error("Failed to search rooms");
            }

            const data = await response.json();
            setAvailableRooms(data.rooms);
            setSearching(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleBookRoom = async (room) => {
        if (!guestName || !guestEmail) {
            setError("Please fill in your name and email");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const bookingData = {
                room_id: room.id,
                guest_name: guestName,
                guest_email: guestEmail,
                guest_phone: guestPhone,
                check_in_date: checkIn,
                check_out_date: checkOut,
                special_requests: specialRequests
            };

            const response = await fetch(`${API_BASE}/catalog/rooms/book`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-tenant-id": "default-tenant-0000"
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to book room");
            }

            const result = await response.json();
            setBookingSuccess(result);
            setSelectedRoom(null);

            // Refresh available rooms
            searchRooms();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const getRoomTypeDisplay = (type) => {
        const types = {
            'standard': 'Standard Room',
            'deluxe': 'Deluxe Room',
            'suite': 'Luxury Suite'
        };
        return types[type] || type;
    };

    const calculateNights = () => {
        if (!checkIn || !checkOut) return 0;
        const start = new Date(checkIn);
        const end = new Date(checkOut);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    };

    return (
        <div className="booking-page">
            {/* Navigation Bar - Luxury Style */}
            <nav className="navbar" style={{ background: 'var(--primary)', position: 'fixed' }}>
                <div className="container">
                    <div className="navbar-brand">Southern Horizons</div>
                    <div className="navbar-nav">
                        <button
                            className="btn-ghost"
                            onClick={onBack}
                            style={{
                                background: 'transparent',
                                border: '1px solid rgba(255,255,255,0.3)',
                                color: 'white',
                                padding: '0.5rem 1.5rem',
                                cursor: 'pointer'
                            }}
                        >
                            Return to Home
                        </button>
                    </div>
                </div>
            </nav>

            <div className="booking-container">
                {/* Back button removed in favor of Navbar */}


                <h1>Book Your Perfect Room</h1>

                {/* Search Section */}
                <div className="search-section">
                    <h2>Search Available Rooms</h2>

                    <div className="search-form">
                        <div className="form-group">
                            <label htmlFor="checkIn">Check-in Date</label>
                            <input
                                type="date"
                                id="checkIn"
                                value={checkIn}
                                min={today}
                                onChange={(e) => setCheckIn(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="checkOut">Check-out Date</label>
                            <input
                                type="date"
                                id="checkOut"
                                value={checkOut}
                                min={checkIn || today}
                                onChange={(e) => setCheckOut(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="roomType">Room Type (Optional)</label>
                            <select
                                id="roomType"
                                value={roomType}
                                onChange={(e) => setRoomType(e.target.value)}
                            >
                                <option value="">All Types</option>
                                <option value="standard">Standard Room</option>
                                <option value="deluxe">Deluxe Room</option>
                                <option value="suite">Luxury Suite</option>
                            </select>
                        </div>

                        <button
                            className="btn btn-primary search-btn"
                            onClick={searchRooms}
                            disabled={loading}
                        >
                            {loading ? "Searching..." : "Search Available Rooms"}
                        </button>
                    </div>

                    {checkIn && checkOut && (
                        <div className="trip-summary">
                            <p>Your stay: <strong>{calculateNights()}</strong> night(s)</p>
                            <p>From <strong>{new Date(checkIn).toLocaleDateString()}</strong> to <strong>{new Date(checkOut).toLocaleDateString()}</strong></p>
                        </div>
                    )}
                </div>

                {error && (
                    <div className="error-message">
                        ⚠️ {error}
                    </div>
                )}

                {bookingSuccess && (
                    <div className="success-message">
                        <h3>✅ Booking Confirmed!</h3>
                        <p><strong>Reservation ID:</strong> {bookingSuccess.reservation_id}</p>
                        <p><strong>Room:</strong> {bookingSuccess.details.room_number}</p>
                        <p><strong>Type:</strong> {getRoomTypeDisplay(bookingSuccess.details.room_type)}</p>
                        <p><strong>Guest:</strong> {bookingSuccess.details.guest_name}</p>
                        <p>A confirmation email has been sent to your email address.</p>
                        <button className="btn btn-outline" onClick={() => setBookingSuccess(null)}>
                            Close
                        </button>
                    </div>
                )}

                {/* Available Rooms Section */}
                {searching && (
                    <div className="results-section">
                        <h2>Available Rooms ({availableRooms.length})</h2>

                        {availableRooms.length === 0 ? (
                            <div className="no-rooms">
                                <p>No rooms available for the selected dates.</p>
                                <p>Please try different dates or contact us for assistance.</p>
                            </div>
                        ) : (
                            <div className="rooms-grid">
                                {availableRooms.map((room) => (
                                    <div key={room.id} className="room-card">
                                        <div className="room-header">
                                            <h3>{getRoomTypeDisplay(room.room_type)}</h3>
                                            <span className="room-number">Room {room.room_number}</span>
                                        </div>

                                        <div className="room-details">
                                            <p><strong>Floor:</strong> {room.floor}</p>
                                            <p><strong>Capacity:</strong> {room.capacity} guests</p>
                                            <p><strong>Amenities:</strong> {room.amenities || "Standard amenities"}</p>
                                            <div className="availability-badge">
                                                ✓ Available
                                            </div>
                                        </div>

                                        <button
                                            className="btn btn-primary"
                                            onClick={() => setSelectedRoom(room)}
                                        >
                                            Book This Room
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Booking Form Modal */}
                {selectedRoom && (
                    <div className="modal-overlay" onClick={() => setSelectedRoom(null)}>
                        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                            <button className="modal-close" onClick={() => setSelectedRoom(null)}>×</button>

                            <h2>Complete Your Booking</h2>
                            <div className="booking-summary">
                                <p><strong>Room:</strong> {getRoomTypeDisplay(selectedRoom.room_type)} - Room {selectedRoom.room_number}</p>
                                <p><strong>Check-in:</strong> {new Date(checkIn).toLocaleDateString()}</p>
                                <p><strong>Check-out:</strong> {new Date(checkOut).toLocaleDateString()}</p>
                                <p><strong>Duration:</strong> {calculateNights()} night(s)</p>
                            </div>

                            <div className="booking-form">
                                <div className="form-group">
                                    <label htmlFor="guestName">Full Name *</label>
                                    <input
                                        type="text"
                                        id="guestName"
                                        value={guestName}
                                        onChange={(e) => setGuestName(e.target.value)}
                                        placeholder="John Doe"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="guestEmail">Email Address *</label>
                                    <input
                                        type="email"
                                        id="guestEmail"
                                        value={guestEmail}
                                        onChange={(e) => setGuestEmail(e.target.value)}
                                        placeholder="john@example.com"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="guestPhone">Phone Number</label>
                                    <input
                                        type="tel"
                                        id="guestPhone"
                                        value={guestPhone}
                                        onChange={(e) => setGuestPhone(e.target.value)}
                                        placeholder="+1 (555) 123-4567"
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="specialRequests">Special Requests</label>
                                    <textarea
                                        id="specialRequests"
                                        value={specialRequests}
                                        onChange={(e) => setSpecialRequests(e.target.value)}
                                        placeholder="Any special requests or requirements..."
                                        rows="3"
                                    />
                                </div>

                                <div className="modal-actions">
                                    <button
                                        className="btn btn-outline"
                                        onClick={() => setSelectedRoom(null)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => handleBookRoom(selectedRoom)}
                                        disabled={loading || !guestName || !guestEmail}
                                    >
                                        {loading ? "Booking..." : "Confirm Booking"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
