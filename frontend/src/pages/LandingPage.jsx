import { useState } from "react";
import { Bot, Zap, Shield, BarChart3, ChevronRight, MessageSquare, ArrowRight, Network } from "lucide-react";

const FEATURES = [
  { icon: Network, title: "Agent-to-Agent Protocol", desc: "8 specialized AI agents communicate in real-time to handle every guest interaction end-to-end.", color: "#38BDF8" },
  { icon: Bot, title: "AI-Powered Concierge", desc: "Gemini-powered natural language understanding for bookings, inquiries, and personalized service.", color: "#A78BFA" },
  { icon: Zap, title: "Live Decision Engine", desc: "Watch agent decisions happen in real-time on the A2A dashboard — complete transparency.", color: "#F59E0B" },
  { icon: Shield, title: "Idempotent Transactions", desc: "Double-click protection, atomic bookings, and enterprise-grade payment processing.", color: "#22C55E" },
  { icon: BarChart3, title: "Analytics & Insights", desc: "Revenue trends, occupancy rates, and agent performance metrics in one unified dashboard.", color: "#FB923C" },
  { icon: MessageSquare, title: "Multi-Tenant Ready", desc: "Run multiple hotel properties with complete data isolation under one platform.", color: "#60A5FA" },
];

const AGENTS = [
  { id: "guest_agent",       name: "Guest Agent",       role: "NLP & Intent",     color: "#38BDF8" },
  { id: "booking_agent",     name: "Booking Agent",     role: "Availability",     color: "#22C55E" },
  { id: "pricing_agent",     name: "Pricing Agent",     role: "Dynamic Pricing",  color: "#F59E0B" },
  { id: "negotiation_agent", name: "Negotiation Agent", role: "Discounts",        color: "#A78BFA" },
  { id: "payment_agent",     name: "Payment Agent",     role: "Transactions",     color: "#34D399" },
  { id: "inventory_agent",   name: "Inventory Agent",   role: "Room Stock",       color: "#60A5FA" },
  { id: "operations_agent",  name: "Operations Agent",  role: "Housekeeping",     color: "#FB923C" },
  { id: "orchestrator",      name: "Orchestrator",      role: "Coordinator",      color: "#F472B6" },
];

export default function LandingPage({ onNavigate, onLogin, VIEWS }) {
  const [demoMsg, setDemoMsg] = useState("");
  const [demoReply, setDemoReply] = useState("");
  const [demoLoading, setDemoLoading] = useState(false);

  const sendDemo = async () => {
    if (!demoMsg.trim()) return;
    setDemoLoading(true);
    setDemoReply("");
    try {
      const res = await fetch("/api/ask/guest", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Tenant-ID": "default-tenant-0000" },
        body: JSON.stringify({ question: demoMsg }),
      });
      const data = await res.json();
      setDemoReply(data.answer || "Welcome to Southern Horizons Hotel. How may I assist you?");
    } catch {
      setDemoReply("Our concierge is here to help. Please try the full chat interface.");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0F172A", color: "#F1F5F9" }}>
      {/* NAV */}
      <nav style={{ position: "sticky", top: 0, zIndex: 50, background: "rgba(15,23,42,0.9)", backdropFilter: "blur(12px)", borderBottom: "1px solid rgba(255,255,255,0.05)", padding: "0 2rem", height: 64, display: "flex", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Bot size={18} color="#0F172A" />
          </div>
          <span style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1rem" }}>A2A Nexus</span>
          <span style={{ fontSize: "0.65rem", color: "#38BDF8", marginLeft: 2, letterSpacing: "0.08em", textTransform: "uppercase", padding: "1px 6px", background: "rgba(56,189,248,0.1)", borderRadius: 4, border: "1px solid rgba(56,189,248,0.2)" }}>Hotel AI</span>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button data-testid="nav-guest-chat" onClick={() => onNavigate(VIEWS.CHAT)} style={{ padding: "0.5rem 1rem", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#94A3B8", cursor: "pointer", fontSize: "0.875rem" }}>
            Guest Chat
          </button>
          <button data-testid="nav-staff-login" onClick={onLogin} style={{ padding: "0.5rem 1.25rem", background: "rgba(56,189,248,0.9)", border: "none", borderRadius: 8, color: "#0F172A", cursor: "pointer", fontWeight: 700, fontSize: "0.875rem", boxShadow: "0 0 16px rgba(56,189,248,0.3)" }}>
            Staff Login
          </button>
        </div>
      </nav>

      {/* HERO */}
      <section style={{ padding: "6rem 2rem 4rem", maxWidth: 1100, margin: "0 auto", position: "relative" }}>
        <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", width: 600, height: 400, background: "radial-gradient(ellipse at center, rgba(56,189,248,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />
        <div style={{ textAlign: "center", position: "relative" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 14px", borderRadius: 20, background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.2)", marginBottom: "1.5rem" }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} className="status-dot-live" />
            <span style={{ fontSize: "0.75rem", color: "#38BDF8", fontWeight: 500, fontFamily: "JetBrains Mono, monospace" }}>8 Agents Online</span>
          </div>
          <h1 style={{ fontFamily: "Chivo", fontWeight: 900, fontSize: "clamp(2.5rem, 6vw, 4.5rem)", lineHeight: 1.05, letterSpacing: "-0.03em", marginBottom: "1.5rem" }}>
            The Future of<br />
            <span style={{ color: "#38BDF8" }}>Hotel Intelligence</span>
          </h1>
          <p style={{ fontSize: "1.1rem", color: "#94A3B8", maxWidth: 600, margin: "0 auto 2.5rem", lineHeight: 1.7 }}>
            A2A Nexus deploys 8 specialized AI agents that communicate in real-time to handle every booking, negotiation, and operation autonomously.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <button data-testid="hero-cta-dashboard" onClick={() => onLogin()} style={{ display: "flex", alignItems: "center", gap: 8, padding: "0.875rem 2rem", background: "rgba(56,189,248,0.9)", border: "none", borderRadius: 10, color: "#0F172A", fontWeight: 700, fontSize: "0.95rem", cursor: "pointer", boxShadow: "0 0 24px rgba(56,189,248,0.35)" }}>
              <LayoutDashboard size={18} /> Launch Dashboard <ArrowRight size={16} />
            </button>
            <button data-testid="hero-cta-chat" onClick={() => onNavigate(VIEWS.CHAT)} style={{ display: "flex", alignItems: "center", gap: 8, padding: "0.875rem 2rem", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, color: "#F1F5F9", fontWeight: 600, fontSize: "0.95rem", cursor: "pointer" }}>
              <MessageSquare size={18} /> Try Guest Chat
            </button>
          </div>
        </div>
      </section>

      {/* AGENT GRID */}
      <section style={{ padding: "2rem 2rem 4rem", maxWidth: 1100, margin: "0 auto" }}>
        <h2 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1.5rem", textAlign: "center", marginBottom: "2rem", color: "#E2E8F0" }}>8 Specialized AI Agents</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
          {AGENTS.map(agent => (
            <div key={agent.id} className="glass-card" style={{ padding: "1.25rem", display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 8, background: `${agent.color}18`, border: `1px solid ${agent.color}33`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Bot size={16} color={agent.color} />
              </div>
              <div>
                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#E2E8F0" }}>{agent.name}</div>
                <div style={{ fontSize: "0.7rem", color: "#64748B" }}>{agent.role}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section style={{ padding: "2rem 2rem 4rem", maxWidth: 1100, margin: "0 auto" }}>
        <h2 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1.5rem", textAlign: "center", marginBottom: "2.5rem", color: "#E2E8F0" }}>Enterprise-Grade Features</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
          {FEATURES.map(f => (
            <div key={f.title} className="glass-card" style={{ padding: "1.5rem" }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: `${f.color}15`, border: `1px solid ${f.color}25`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1rem" }}>
                <f.icon size={20} color={f.color} strokeWidth={1.5} />
              </div>
              <h3 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1rem", marginBottom: "0.5rem", color: "#E2E8F0" }}>{f.title}</h3>
              <p style={{ fontSize: "0.85rem", color: "#64748B", lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DEMO CHAT */}
      <section style={{ padding: "2rem 2rem 5rem", maxWidth: 680, margin: "0 auto" }}>
        <h2 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1.5rem", textAlign: "center", marginBottom: "1rem", color: "#E2E8F0" }}>Try the AI Concierge</h2>
        <p style={{ textAlign: "center", color: "#64748B", marginBottom: "1.5rem", fontSize: "0.875rem" }}>Ask anything about the hotel</p>
        <div className="glass-card" style={{ padding: "1.5rem" }}>
          {demoReply && (
            <div style={{ marginBottom: "1rem", padding: "0.875rem 1rem", background: "rgba(56,189,248,0.06)", borderRadius: 8, borderLeft: "3px solid #38BDF8", fontSize: "0.875rem", color: "#CBD5E1", lineHeight: 1.6 }}>
              {demoReply}
            </div>
          )}
          <div style={{ display: "flex", gap: 8 }}>
            <input
              data-testid="demo-chat-input"
              value={demoMsg}
              onChange={e => setDemoMsg(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendDemo()}
              placeholder="What amenities do you offer?"
              style={{ flex: 1, padding: "0.625rem 1rem", background: "rgba(0,0,0,0.3)", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.875rem", outline: "none" }}
            />
            <button data-testid="demo-chat-send" onClick={sendDemo} disabled={demoLoading} style={{ padding: "0.625rem 1.25rem", background: "rgba(56,189,248,0.85)", border: "none", borderRadius: 8, color: "#0F172A", fontWeight: 700, cursor: "pointer", fontSize: "0.85rem" }}>
              {demoLoading ? "..." : "Ask"}
            </button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid #1E293B", padding: "2rem", textAlign: "center", color: "#64748B", fontSize: "0.8rem" }}>
        A2A Nexus — Southern Horizons Hotel AI Platform
      </footer>
    </div>
  );
}

function LayoutDashboard({ size, ...props }) {
  return <Network size={size} {...props} />;
}
