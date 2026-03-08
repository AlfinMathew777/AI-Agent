import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, ArrowLeft, Loader2, Zap } from "lucide-react";
import { marked } from "marked";

const SUGGESTIONS = [
  "What rooms are available tomorrow?",
  "Book 2 deluxe rooms for 3 nights",
  "Can I get a 10% discount on a 5-night stay?",
  "What amenities do you offer?",
];

export default function GuestChat({ onBack, embedded }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Welcome to **Southern Horizons Hotel**! 🌊\n\nI'm your AI concierge, powered by 8 specialized agents. I can help you with:\n- Room availability & bookings\n- Special rates & discounts\n- Hotel amenities & services\n\nHow can I assist you today?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2, 10));
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    setLoading(true);

    try {
      const res = await fetch("/api/a2a/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Tenant-ID": "default-tenant-0000" },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      });
      const data = await res.json();
      const answer = data.answer || data.response || "How can I assist you further?";
      setMessages(prev => [...prev, {
        role: "assistant",
        content: answer,
        action: data.action,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Our concierge desk is experiencing high volume. Please try again in a moment.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: embedded ? "calc(100vh - 60px)" : "100vh", background: embedded ? "transparent" : "#0F172A", display: "flex", flexDirection: "column", maxWidth: 900, margin: "0 auto", width: "100%" }}>
      {!embedded && (
        <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #1E293B", display: "flex", alignItems: "center", gap: 12 }}>
          {onBack && (
            <button data-testid="chat-back" onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", color: "#64748B", display: "flex" }}>
              <ArrowLeft size={20} />
            </button>
          )}
          <div style={{ width: 36, height: 36, borderRadius: 8, background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Bot size={18} color="#0F172A" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.95rem", fontFamily: "Chivo" }}>AI Concierge</div>
            <div style={{ fontSize: "0.7rem", color: "#22C55E", display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} className="status-dot-live" />
              8 Agents Active
            </div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 4, fontSize: "0.7rem", color: "#38BDF8", padding: "2px 8px", background: "rgba(56,189,248,0.08)", borderRadius: 4, border: "1px solid rgba(56,189,248,0.2)" }}>
            <Zap size={10} />A2A Powered
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", gap: 10, justifyContent: msg.role === "user" ? "flex-end" : "flex-start", alignItems: "flex-start" }}>
            {msg.role === "assistant" && (
              <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(56,189,248,0.15)", border: "1px solid rgba(56,189,248,0.2)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 2 }}>
                <Bot size={16} color="#38BDF8" />
              </div>
            )}
            <div style={{ maxWidth: "72%", display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
              {msg.role === "assistant" && msg.action === "booking_confirmed" && (
                <span style={{ fontSize: "0.65rem", color: "#22C55E", marginBottom: 4, padding: "1px 6px", background: "rgba(34,197,94,0.1)", borderRadius: 4, border: "1px solid rgba(34,197,94,0.2)", width: "fit-content" }}>
                  BOOKING CONFIRMED
                </span>
              )}
              <div
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: msg.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
                  background: msg.role === "user" ? "rgba(56,189,248,0.85)" : "rgba(30,41,59,0.9)",
                  color: msg.role === "user" ? "#0F172A" : "#E2E8F0",
                  fontSize: "0.875rem",
                  lineHeight: 1.6,
                  border: msg.role === "assistant" ? "1px solid rgba(255,255,255,0.06)" : "none",
                }}
                dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || "") }}
              />
              <span style={{ fontSize: "0.65rem", color: "#475569", marginTop: 4 }}>{msg.time}</span>
            </div>
            {msg.role === "user" && (
              <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(56,189,248,0.1)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 2 }}>
                <User size={16} color="#38BDF8" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(56,189,248,0.15)", border: "1px solid rgba(56,189,248,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={16} color="#38BDF8" />
            </div>
            <div style={{ padding: "0.75rem 1rem", borderRadius: "12px 12px 12px 4px", background: "rgba(30,41,59,0.9)", border: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", gap: 8 }}>
              <Loader2 size={14} color="#38BDF8" style={{ animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: "0.8rem", color: "#64748B", fontFamily: "JetBrains Mono, monospace" }}>agents processing...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div style={{ padding: "0 1.5rem 0.75rem", display: "flex", gap: 6, flexWrap: "wrap" }}>
          {SUGGESTIONS.map(s => (
            <button key={s} data-testid={`suggestion-${s.slice(0,10)}`} onClick={() => send(s)} style={{ fontSize: "0.75rem", padding: "0.4rem 0.75rem", background: "rgba(56,189,248,0.06)", border: "1px solid rgba(56,189,248,0.15)", borderRadius: 20, color: "#94A3B8", cursor: "pointer" }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: "1rem 1.5rem", borderTop: "1px solid #1E293B", display: "flex", gap: 10 }}>
        <input
          data-testid="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about rooms, bookings, amenities..."
          style={{ flex: 1, padding: "0.75rem 1rem", background: "rgba(0,0,0,0.3)", border: "1px solid #334155", borderRadius: 10, color: "#F1F5F9", fontSize: "0.875rem", outline: "none" }}
        />
        <button
          data-testid="chat-send"
          onClick={() => send()}
          disabled={loading || !input.trim()}
          style={{ padding: "0.75rem 1.25rem", background: loading || !input.trim() ? "rgba(56,189,248,0.3)" : "rgba(56,189,248,0.9)", border: "none", borderRadius: 10, color: "#0F172A", cursor: loading || !input.trim() ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 12px rgba(56,189,248,0.25)" }}>
          <Send size={18} strokeWidth={2} />
        </button>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
