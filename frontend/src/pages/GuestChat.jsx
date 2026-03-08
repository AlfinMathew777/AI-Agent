import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User, ArrowLeft, Loader2, Zap, Calendar, Users, 
  BedDouble, Check, X, CreditCard, ChevronRight, Coffee, Car,
  Clock, Plus, Minus, Sparkles, ShoppingCart
} from "lucide-react";
import { marked } from "marked";

const API_URL = process.env.REACT_APP_BACKEND_URL || "";

// Booking flow steps
const STEPS = {
  WELCOME: "welcome",
  DATES: "dates",
  GUESTS: "guests",
  ROOMS: "rooms",
  SERVICES: "services",
  SUMMARY: "summary",
  PAYMENT: "payment",
  CONFIRMED: "confirmed"
};

// Add-on service icons
const SERVICE_ICONS = {
  breakfast: Coffee,
  airport_pickup: Car,
  late_checkout: Clock,
  extra_bed: BedDouble,
  parking: Car,
  spa_access: Sparkles
};

export default function GuestChat({ onBack, embedded }) {
  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2, 10));
  const bottomRef = useRef(null);
  
  // Booking flow state
  const [bookingStep, setBookingStep] = useState(STEPS.WELCOME);
  const [bookingData, setBookingData] = useState({
    checkIn: "",
    checkOut: "",
    guests: 2,
    selectedRoom: null,
    selectedServices: [],
    guestName: "",
    guestEmail: "",
    summary: null
  });
  const [availableRooms, setAvailableRooms] = useState([]);
  const [availableServices, setAvailableServices] = useState([]);
  const [roomsLoading, setRoomsLoading] = useState(false);

  // Initialize with welcome message
  useEffect(() => {
    setMessages([{
      role: "assistant",
      content: "Welcome to **Southern Horizons Hotel**! 🌊\n\nI'm your AI booking assistant. I'll guide you through a simple booking process.\n\nWould you like to **book a room** or ask me anything about the hotel?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      showBookingButton: true
    }]);
    fetchServices();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, bookingStep]);

  // Check for payment return
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const bookingStatus = params.get("booking_status");
    const bookingId = params.get("booking_id");
    const sessionIdParam = params.get("session_id");
    
    if (bookingStatus === "success" && bookingId) {
      setBookingStep(STEPS.CONFIRMED);
      pollPaymentStatus(bookingId, sessionIdParam);
      // Clear URL params
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (bookingStatus === "cancelled") {
      addAssistantMessage("Your payment was cancelled. No worries! Your booking is saved. Would you like to try again?");
      setBookingStep(STEPS.SUMMARY);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const fetchServices = async () => {
    try {
      const res = await fetch(`${API_URL}/api/booking/services`);
      const data = await res.json();
      setAvailableServices(data.services || []);
    } catch (err) {
      console.error("Failed to fetch services:", err);
    }
  };

  const pollPaymentStatus = async (bookingId, sessionId, attempts = 0) => {
    const maxAttempts = 5;
    
    if (attempts >= maxAttempts) {
      addAssistantMessage("Payment verification is taking longer than expected. Please check your email for confirmation or contact the front desk.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/booking/status/${bookingId}?session_id=${sessionId}`, {
        headers: { "X-Tenant-ID": "default-tenant-0000" }
      });
      const data = await res.json();
      
      if (data.status === "confirmed") {
        addAssistantMessage(`🎉 **Booking Confirmed!**\n\n**Confirmation #**: ${bookingId.slice(0, 8).toUpperCase()}\n**Guest**: ${data.guest_name}\n**Room**: ${data.room_number}\n**Check-in**: ${data.check_in}\n**Check-out**: ${data.check_out}\n**Total Paid**: $${parseFloat(data.total).toFixed(2)}\n\nA confirmation email has been sent. We look forward to welcoming you!`);
        return;
      }
      
      // Continue polling
      setTimeout(() => pollPaymentStatus(bookingId, sessionId, attempts + 1), 2000);
    } catch (err) {
      console.error("Error polling status:", err);
    }
  };

  const addAssistantMessage = (content, extras = {}) => {
    setMessages(prev => [...prev, {
      role: "assistant",
      content,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      ...extras
    }]);
  };

  const addUserMessage = (content) => {
    setMessages(prev => [...prev, {
      role: "user",
      content,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }]);
  };

  // ============================================================
  // Booking Flow Handlers
  // ============================================================

  const startBooking = () => {
    addUserMessage("I'd like to book a room");
    addAssistantMessage("Great choice! Let's find you the perfect room.\n\n**When would you like to stay?**", { showDatePicker: true });
    setBookingStep(STEPS.DATES);
  };

  const handleDateSelection = async (checkIn, checkOut) => {
    setBookingData(prev => ({ ...prev, checkIn, checkOut }));
    addUserMessage(`Check-in: ${checkIn}, Check-out: ${checkOut}`);
    addAssistantMessage("Perfect! **How many guests** will be staying?", { showGuestPicker: true });
    setBookingStep(STEPS.GUESTS);
  };

  const handleGuestSelection = async (guests) => {
    setBookingData(prev => ({ ...prev, guests }));
    addUserMessage(`${guests} guest${guests > 1 ? 's' : ''}`);
    
    // Fetch available rooms
    setRoomsLoading(true);
    addAssistantMessage("Searching for available rooms...", { isLoading: true });
    
    try {
      const res = await fetch(`${API_URL}/api/booking/rooms/available`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Tenant-ID": "default-tenant-0000"
        },
        body: JSON.stringify({
          check_in: bookingData.checkIn,
          check_out: bookingData.checkOut,
          guests
        })
      });
      const data = await res.json();
      
      if (data.room_types && data.room_types.length > 0) {
        setAvailableRooms(data.room_types);
        // Remove loading message and add room selection
        setMessages(prev => prev.filter(m => !m.isLoading));
        addAssistantMessage(
          `Found **${data.total_available} rooms** available for ${data.nights} night${data.nights > 1 ? 's' : ''}!\n\nSelect your preferred room type:`,
          { showRoomSelector: true, roomData: data }
        );
        setBookingStep(STEPS.ROOMS);
      } else {
        setMessages(prev => prev.filter(m => !m.isLoading));
        addAssistantMessage("Sorry, no rooms are available for those dates. Would you like to try different dates?", { showDatePicker: true });
        setBookingStep(STEPS.DATES);
      }
    } catch (err) {
      console.error("Error fetching rooms:", err);
      setMessages(prev => prev.filter(m => !m.isLoading));
      addAssistantMessage("Sorry, I had trouble checking availability. Please try again.");
    } finally {
      setRoomsLoading(false);
    }
  };

  const handleRoomSelection = (roomType) => {
    const room = availableRooms.find(r => r.room_type === roomType.room_type);
    if (!room || !room.rooms || room.rooms.length === 0) return;
    
    const selectedRoom = room.rooms[0]; // Select first available room of this type
    setBookingData(prev => ({ ...prev, selectedRoom: { ...selectedRoom, ...roomType } }));
    addUserMessage(`Selected: ${roomType.room_type} - $${roomType.price_per_night}/night`);
    addAssistantMessage("Excellent choice! Would you like to add any **services** to enhance your stay?", { showServiceSelector: true });
    setBookingStep(STEPS.SERVICES);
  };

  const handleServiceToggle = (serviceId) => {
    setBookingData(prev => {
      const services = prev.selectedServices.includes(serviceId)
        ? prev.selectedServices.filter(s => s !== serviceId)
        : [...prev.selectedServices, serviceId];
      return { ...prev, selectedServices: services };
    });
  };

  const handleServicesDone = async () => {
    const serviceNames = bookingData.selectedServices.length > 0
      ? bookingData.selectedServices.map(id => availableServices.find(s => s.id === id)?.name).filter(Boolean).join(", ")
      : "No additional services";
    
    addUserMessage(`Services: ${serviceNames}`);
    
    // Generate summary
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/booking/summary`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Tenant-ID": "default-tenant-0000"
        },
        body: JSON.stringify({
          room_id: bookingData.selectedRoom.id,
          check_in: bookingData.checkIn,
          check_out: bookingData.checkOut,
          guests: bookingData.guests,
          services: bookingData.selectedServices
        })
      });
      const summary = await res.json();
      setBookingData(prev => ({ ...prev, summary }));
      addAssistantMessage("Here's your **booking summary**:", { showSummary: true, summary });
      setBookingStep(STEPS.SUMMARY);
    } catch (err) {
      console.error("Error generating summary:", err);
      addAssistantMessage("Sorry, I had trouble generating your summary. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleProceedToPayment = async () => {
    if (!bookingData.guestName || !bookingData.guestEmail) {
      addAssistantMessage("Please enter your name and email to continue.", { showGuestInfo: true });
      return;
    }
    
    addUserMessage(`Guest: ${bookingData.guestName} (${bookingData.guestEmail})`);
    setLoading(true);
    
    try {
      const res = await fetch(`${API_URL}/api/booking/checkout`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Tenant-ID": "default-tenant-0000"
        },
        body: JSON.stringify({
          booking_summary: bookingData.summary,
          guest_name: bookingData.guestName,
          guest_email: bookingData.guestEmail
        })
      });
      const data = await res.json();
      
      if (data.checkout_url) {
        addAssistantMessage("Redirecting you to secure payment...");
        setTimeout(() => {
          window.location.href = data.checkout_url;
        }, 1000);
      } else {
        addAssistantMessage("Sorry, I couldn't create the checkout session. Please try again.");
      }
    } catch (err) {
      console.error("Error creating checkout:", err);
      addAssistantMessage("Sorry, there was an error processing your request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Free-form chat (fallback to A2A)
  const sendChat = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    addUserMessage(msg);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/a2a/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Tenant-ID": "default-tenant-0000" },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      });
      const data = await res.json();
      addAssistantMessage(data.answer || data.response || "How can I assist you?");
    } catch {
      addAssistantMessage("I apologize, I'm having trouble connecting. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Render
  // ============================================================

  return (
    <div 
      data-testid="guest-chat"
      style={{
        height: embedded ? "100%" : "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#0F172A",
        position: "relative"
      }}
    >
      {/* Header */}
      {!embedded && (
        <div style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid #1E293B",
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: "rgba(15,23,42,0.9)",
          backdropFilter: "blur(8px)"
        }}>
          <button onClick={onBack} style={{ background: "none", border: "none", color: "#64748B", cursor: "pointer", display: "flex" }}>
            <ArrowLeft size={20} />
          </button>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Bot size={20} color="#0F172A" />
          </div>
          <div>
            <div style={{ color: "#F1F5F9", fontWeight: 600, fontSize: "0.95rem" }}>Southern Horizons Hotel</div>
            <div style={{ color: "#38BDF8", fontSize: "0.7rem", display: "flex", alignItems: "center", gap: 4 }}>
              <Zap size={10} /> AI Booking Assistant
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.map((msg, idx) => (
          <MessageBubble 
            key={idx} 
            message={msg}
            onStartBooking={startBooking}
            onDateSelect={handleDateSelection}
            onGuestSelect={handleGuestSelection}
            onRoomSelect={handleRoomSelection}
            onServiceToggle={handleServiceToggle}
            onServicesDone={handleServicesDone}
            onProceedToPayment={handleProceedToPayment}
            bookingData={bookingData}
            setBookingData={setBookingData}
            availableRooms={availableRooms}
            availableServices={availableServices}
          />
        ))}
        {loading && (
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={16} color="#0F172A" />
            </div>
            <div style={{ padding: "0.75rem 1rem", borderRadius: 12, background: "#1E293B", display: "flex", alignItems: "center", gap: 8 }}>
              <Loader2 size={14} className="spin" color="#38BDF8" />
              <span style={{ color: "#94A3B8", fontSize: "0.85rem" }}>Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      {bookingStep === STEPS.WELCOME && (
        <div style={{ padding: "1rem 1.5rem", borderTop: "1px solid #1E293B", background: "rgba(15,23,42,0.9)" }}>
          <div style={{ display: "flex", gap: 10 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === "Enter" && sendChat()}
              placeholder="Ask me anything about the hotel..."
              data-testid="guest-chat-input"
              style={{ flex: 1, padding: "0.75rem 1rem", borderRadius: 10, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.9rem", outline: "none" }}
            />
            <button
              onClick={() => sendChat()}
              disabled={loading || !input.trim()}
              data-testid="guest-chat-send"
              style={{ width: 44, height: 44, borderRadius: 10, background: input.trim() ? "linear-gradient(135deg,#38BDF8,#0EA5E9)" : "#334155", border: "none", cursor: input.trim() ? "pointer" : "not-allowed", display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <Send size={18} color={input.trim() ? "#0F172A" : "#64748B"} />
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}


// ============================================================
// Message Bubble Component
// ============================================================

function MessageBubble({ 
  message, 
  onStartBooking, 
  onDateSelect, 
  onGuestSelect,
  onRoomSelect,
  onServiceToggle,
  onServicesDone,
  onProceedToPayment,
  bookingData,
  setBookingData,
  availableRooms,
  availableServices
}) {
  const isUser = message.role === "user";
  
  return (
    <div style={{ display: "flex", gap: 10, flexDirection: isUser ? "row-reverse" : "row", alignItems: "flex-start" }}>
      <div style={{
        width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
        background: isUser ? "linear-gradient(135deg,#A78BFA,#8B5CF6)" : "linear-gradient(135deg,#0EA5E9,#38BDF8)",
        display: "flex", alignItems: "center", justifyContent: "center"
      }}>
        {isUser ? <User size={16} color="#0F172A" /> : <Bot size={16} color="#0F172A" />}
      </div>
      
      <div style={{ maxWidth: "80%", display: "flex", flexDirection: "column", gap: 12 }}>
        {/* Message content */}
        <div style={{
          padding: "0.75rem 1rem",
          borderRadius: 12,
          background: isUser ? "rgba(167,139,250,0.15)" : "#1E293B",
          border: isUser ? "1px solid rgba(167,139,250,0.3)" : "1px solid #334155",
          color: "#F1F5F9",
          fontSize: "0.9rem",
          lineHeight: 1.6
        }}>
          <div dangerouslySetInnerHTML={{ __html: marked.parse(message.content || "") }} />
        </div>

        {/* Book Now Button */}
        {message.showBookingButton && (
          <button
            onClick={onStartBooking}
            data-testid="start-booking-btn"
            style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "0.75rem 1.25rem",
              background: "linear-gradient(135deg,#38BDF8,#0EA5E9)",
              border: "none", borderRadius: 10,
              color: "#0F172A", fontWeight: 600, fontSize: "0.9rem",
              cursor: "pointer", width: "fit-content"
            }}
          >
            <BedDouble size={18} /> Book a Room
          </button>
        )}

        {/* Date Picker */}
        {message.showDatePicker && (
          <DatePicker onSelect={onDateSelect} />
        )}

        {/* Guest Picker */}
        {message.showGuestPicker && (
          <GuestPicker onSelect={onGuestSelect} />
        )}

        {/* Room Selector */}
        {message.showRoomSelector && (
          <RoomSelector 
            roomData={message.roomData} 
            onSelect={onRoomSelect}
          />
        )}

        {/* Service Selector */}
        {message.showServiceSelector && (
          <ServiceSelector 
            services={availableServices}
            selected={bookingData.selectedServices}
            onToggle={onServiceToggle}
            onDone={onServicesDone}
            nights={bookingData.summary?.nights || 1}
          />
        )}

        {/* Booking Summary */}
        {message.showSummary && message.summary && (
          <BookingSummary 
            summary={message.summary}
            bookingData={bookingData}
            setBookingData={setBookingData}
            onProceed={onProceedToPayment}
          />
        )}

        {/* Guest Info Form */}
        {message.showGuestInfo && (
          <GuestInfoForm 
            bookingData={bookingData}
            setBookingData={setBookingData}
            onProceed={onProceedToPayment}
          />
        )}
      </div>
    </div>
  );
}


// ============================================================
// Date Picker Component
// ============================================================

function DatePicker({ onSelect }) {
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [error, setError] = useState("");
  
  const today = new Date().toISOString().split("T")[0];
  const maxDate = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  const currentYear = new Date().getFullYear();

  // Validate and normalize a date string (fixes malformed years like 0026 -> 2026)
  const normalizeDate = (dateStr) => {
    if (!dateStr) return "";
    
    // Parse the date parts
    const parts = dateStr.split("-");
    if (parts.length !== 3) return dateStr;
    
    let [year, month, day] = parts;
    
    // Fix malformed years (e.g., "0026" should become "2026")
    const yearNum = parseInt(year, 10);
    if (yearNum < 100) {
      // Assume 20XX for years under 100
      year = `20${year.slice(-2).padStart(2, "0")}`;
    } else if (yearNum < 1000) {
      // Year like 026 should become 2026
      year = `2${year.padStart(3, "0")}`;
    }
    
    return `${year}-${month}-${day}`;
  };

  // Validate date is within acceptable range
  const isValidDate = (dateStr) => {
    if (!dateStr) return false;
    const normalized = normalizeDate(dateStr);
    const parts = normalized.split("-");
    if (parts.length !== 3) return false;
    
    const year = parseInt(parts[0], 10);
    // Valid year range: current year to current year + 2
    return year >= currentYear && year <= currentYear + 2;
  };

  const handleCheckInChange = (e) => {
    const value = e.target.value;
    const normalized = normalizeDate(value);
    setCheckIn(normalized);
    setError("");
    
    if (value && !isValidDate(normalized)) {
      setError("Please select a valid date");
    }
  };

  const handleCheckOutChange = (e) => {
    const value = e.target.value;
    const normalized = normalizeDate(value);
    setCheckOut(normalized);
    setError("");
    
    if (value && !isValidDate(normalized)) {
      setError("Please select a valid date");
    }
  };

  const handleSubmit = () => {
    const normalizedIn = normalizeDate(checkIn);
    const normalizedOut = normalizeDate(checkOut);
    
    // Final validation
    if (!isValidDate(normalizedIn) || !isValidDate(normalizedOut)) {
      setError("Please select valid dates");
      return;
    }
    
    if (normalizedIn >= normalizedOut) {
      setError("Check-out must be after check-in");
      return;
    }
    
    onSelect(normalizedIn, normalizedOut);
  };

  const isValid = checkIn && checkOut && isValidDate(checkIn) && isValidDate(checkOut) && checkIn < checkOut;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "1rem", background: "rgba(56,189,248,0.08)", borderRadius: 12, border: "1px solid rgba(56,189,248,0.2)" }}>
      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", color: "#94A3B8", fontSize: "0.75rem", marginBottom: 6 }}>Check-in</label>
          <input
            type="date"
            value={checkIn}
            min={today}
            max={maxDate}
            onChange={handleCheckInChange}
            data-testid="checkin-date"
            style={{ width: "100%", padding: "0.6rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", color: "#94A3B8", fontSize: "0.75rem", marginBottom: 6 }}>Check-out</label>
          <input
            type="date"
            value={checkOut}
            min={checkIn || today}
            max={maxDate}
            onChange={handleCheckOutChange}
            data-testid="checkout-date"
            style={{ width: "100%", padding: "0.6rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
          />
        </div>
      </div>
      {error && (
        <div style={{ color: "#EF4444", fontSize: "0.75rem", textAlign: "center" }}>
          {error}
        </div>
      )}
      <button
        onClick={handleSubmit}
        disabled={!isValid}
        data-testid="confirm-dates-btn"
        style={{
          padding: "0.7rem",
          background: isValid ? "linear-gradient(135deg,#38BDF8,#0EA5E9)" : "#334155",
          border: "none", borderRadius: 8,
          color: isValid ? "#0F172A" : "#64748B",
          fontWeight: 600, fontSize: "0.85rem",
          cursor: isValid ? "pointer" : "not-allowed"
        }}
      >
        Confirm Dates
      </button>
    </div>
  );
}


// ============================================================
// Guest Picker Component  
// ============================================================

function GuestPicker({ onSelect }) {
  const [guests, setGuests] = useState(2);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "1rem", background: "rgba(56,189,248,0.08)", borderRadius: 12, border: "1px solid rgba(56,189,248,0.2)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 20 }}>
        <button
          onClick={() => setGuests(Math.max(1, guests - 1))}
          style={{ width: 40, height: 40, borderRadius: "50%", border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <Minus size={18} />
        </button>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#F1F5F9", fontSize: "2rem", fontWeight: 700, fontFamily: "Chivo" }}>{guests}</div>
          <div style={{ color: "#94A3B8", fontSize: "0.75rem" }}>Guest{guests > 1 ? "s" : ""}</div>
        </div>
        <button
          onClick={() => setGuests(Math.min(10, guests + 1))}
          style={{ width: 40, height: 40, borderRadius: "50%", border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <Plus size={18} />
        </button>
      </div>
      <button
        onClick={() => onSelect(guests)}
        data-testid="confirm-guests-btn"
        style={{
          padding: "0.7rem",
          background: "linear-gradient(135deg,#38BDF8,#0EA5E9)",
          border: "none", borderRadius: 8,
          color: "#0F172A", fontWeight: 600, fontSize: "0.85rem",
          cursor: "pointer"
        }}
      >
        Continue
      </button>
    </div>
  );
}


// ============================================================
// Room Selector Component
// ============================================================

function RoomSelector({ roomData, onSelect }) {
  if (!roomData?.room_types) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {roomData.room_types.map((room, idx) => (
        <div
          key={idx}
          data-testid={`room-option-${room.room_type.toLowerCase().replace(" ", "-")}`}
          style={{
            padding: "1rem",
            background: "#1E293B",
            border: "1px solid #334155",
            borderRadius: 12,
            cursor: "pointer",
            transition: "all 0.15s ease"
          }}
          onClick={() => onSelect(room)}
          onMouseEnter={e => { e.currentTarget.style.borderColor = "#38BDF8"; e.currentTarget.style.background = "rgba(56,189,248,0.08)"; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = "#334155"; e.currentTarget.style.background = "#1E293B"; }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
            <div>
              <div style={{ color: "#F1F5F9", fontSize: "1rem", fontWeight: 600, marginBottom: 4 }}>{room.room_type}</div>
              <div style={{ color: "#64748B", fontSize: "0.75rem" }}>Up to {room.capacity} guests • {room.available_count} available</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ color: "#38BDF8", fontSize: "1.1rem", fontWeight: 700 }}>${room.price_per_night}</div>
              <div style={{ color: "#64748B", fontSize: "0.7rem" }}>per night</div>
            </div>
          </div>
          <div style={{ color: "#94A3B8", fontSize: "0.8rem", marginBottom: 12 }}>{room.description}</div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ color: "#22C55E", fontSize: "0.8rem", fontWeight: 500 }}>
              Total: ${room.total_price} for {roomData.nights} night{roomData.nights > 1 ? "s" : ""}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4, color: "#38BDF8", fontSize: "0.8rem" }}>
              Select <ChevronRight size={14} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}


// ============================================================
// Service Selector Component
// ============================================================

function ServiceSelector({ services, selected, onToggle, onDone, nights }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {services.map((service) => {
          const isSelected = selected.includes(service.id);
          const Icon = SERVICE_ICONS[service.id] || Plus;
          const price = service.per_night ? service.price * nights : service.price;
          
          return (
            <div
              key={service.id}
              data-testid={`service-${service.id}`}
              onClick={() => onToggle(service.id)}
              style={{
                padding: "0.75rem",
                background: isSelected ? "rgba(34,197,94,0.15)" : "#1E293B",
                border: isSelected ? "1px solid rgba(34,197,94,0.4)" : "1px solid #334155",
                borderRadius: 10,
                cursor: "pointer",
                transition: "all 0.15s ease"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <Icon size={16} color={isSelected ? "#22C55E" : "#64748B"} />
                {isSelected && <Check size={16} color="#22C55E" />}
              </div>
              <div style={{ color: "#F1F5F9", fontSize: "0.8rem", fontWeight: 500, marginBottom: 2 }}>{service.name}</div>
              <div style={{ color: "#64748B", fontSize: "0.7rem", marginBottom: 4 }}>{service.description}</div>
              <div style={{ color: isSelected ? "#22C55E" : "#38BDF8", fontSize: "0.75rem", fontWeight: 600 }}>
                +${price.toFixed(2)} {service.per_night && `(${nights} nights)`}
              </div>
            </div>
          );
        })}
      </div>
      <button
        onClick={onDone}
        data-testid="confirm-services-btn"
        style={{
          padding: "0.75rem",
          background: "linear-gradient(135deg,#38BDF8,#0EA5E9)",
          border: "none", borderRadius: 8,
          color: "#0F172A", fontWeight: 600, fontSize: "0.85rem",
          cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8
        }}
      >
        <ShoppingCart size={16} /> Continue to Summary
      </button>
    </div>
  );
}


// ============================================================
// Booking Summary Component
// ============================================================

function BookingSummary({ summary, bookingData, setBookingData, onProceed }) {
  return (
    <div style={{ background: "#1E293B", border: "1px solid #334155", borderRadius: 12, overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "1rem", background: "rgba(56,189,248,0.1)", borderBottom: "1px solid #334155" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#38BDF8", fontSize: "0.9rem", fontWeight: 600 }}>
          <ShoppingCart size={18} /> Booking Summary
        </div>
      </div>
      
      {/* Details */}
      <div style={{ padding: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #334155" }}>
          <div>
            <div style={{ color: "#F1F5F9", fontSize: "0.95rem", fontWeight: 600 }}>{summary.room?.room_type}</div>
            <div style={{ color: "#64748B", fontSize: "0.75rem" }}>Room {summary.room?.room_number}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ color: "#94A3B8", fontSize: "0.75rem" }}>{summary.check_in} → {summary.check_out}</div>
            <div style={{ color: "#94A3B8", fontSize: "0.75rem" }}>{summary.nights} night{summary.nights > 1 ? "s" : ""}, {summary.guests} guest{summary.guests > 1 ? "s" : ""}</div>
          </div>
        </div>
        
        {/* Breakdown */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
          {summary.breakdown?.map((item, idx) => (
            <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
              <span style={{ color: "#94A3B8" }}>{item.item}</span>
              <span style={{ color: "#F1F5F9" }}>${item.price.toFixed(2)}</span>
            </div>
          ))}
        </div>
        
        {/* Total */}
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0.75rem", background: "rgba(34,197,94,0.1)", borderRadius: 8, marginBottom: 16 }}>
          <span style={{ color: "#22C55E", fontWeight: 600 }}>Total</span>
          <span style={{ color: "#22C55E", fontWeight: 700, fontSize: "1.1rem" }}>${summary.total.toFixed(2)}</span>
        </div>
        
        {/* Guest Info */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
          <input
            type="text"
            placeholder="Full Name"
            value={bookingData.guestName}
            onChange={e => setBookingData(prev => ({ ...prev, guestName: e.target.value }))}
            data-testid="guest-name-input"
            style={{ padding: "0.7rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
          />
          <input
            type="email"
            placeholder="Email Address"
            value={bookingData.guestEmail}
            onChange={e => setBookingData(prev => ({ ...prev, guestEmail: e.target.value }))}
            data-testid="guest-email-input"
            style={{ padding: "0.7rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
          />
        </div>
        
        {/* Payment Button */}
        <button
          onClick={onProceed}
          disabled={!bookingData.guestName || !bookingData.guestEmail}
          data-testid="proceed-to-payment-btn"
          style={{
            width: "100%",
            padding: "0.85rem",
            background: (bookingData.guestName && bookingData.guestEmail) 
              ? "linear-gradient(135deg,#22C55E,#16A34A)" 
              : "#334155",
            border: "none", borderRadius: 8,
            color: (bookingData.guestName && bookingData.guestEmail) ? "#fff" : "#64748B",
            fontWeight: 600, fontSize: "0.9rem",
            cursor: (bookingData.guestName && bookingData.guestEmail) ? "pointer" : "not-allowed",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 8
          }}
        >
          <CreditCard size={18} /> Proceed to Payment
        </button>
      </div>
    </div>
  );
}


// Guest Info Form (standalone if needed)
function GuestInfoForm({ bookingData, setBookingData, onProceed }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "1rem", background: "rgba(56,189,248,0.08)", borderRadius: 12, border: "1px solid rgba(56,189,248,0.2)" }}>
      <input
        type="text"
        placeholder="Full Name"
        value={bookingData.guestName}
        onChange={e => setBookingData(prev => ({ ...prev, guestName: e.target.value }))}
        style={{ padding: "0.7rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
      />
      <input
        type="email"
        placeholder="Email Address"
        value={bookingData.guestEmail}
        onChange={e => setBookingData(prev => ({ ...prev, guestEmail: e.target.value }))}
        style={{ padding: "0.7rem", borderRadius: 8, border: "1px solid #334155", background: "#0F172A", color: "#F1F5F9", fontSize: "0.85rem" }}
      />
      <button
        onClick={onProceed}
        disabled={!bookingData.guestName || !bookingData.guestEmail}
        style={{
          padding: "0.75rem",
          background: (bookingData.guestName && bookingData.guestEmail) ? "linear-gradient(135deg,#38BDF8,#0EA5E9)" : "#334155",
          border: "none", borderRadius: 8,
          color: (bookingData.guestName && bookingData.guestEmail) ? "#0F172A" : "#64748B",
          fontWeight: 600, fontSize: "0.85rem",
          cursor: (bookingData.guestName && bookingData.guestEmail) ? "pointer" : "not-allowed"
        }}
      >
        Continue
      </button>
    </div>
  );
}
