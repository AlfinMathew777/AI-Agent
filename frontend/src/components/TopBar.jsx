import { Menu, Wifi, WifiOff, Bell, Search } from "lucide-react";
import { useState, useEffect } from "react";

const VIEW_TITLES = {
  a2a:        { title: "A2A Dashboard",     subtitle: "Live Agent-to-Agent Operations" },
  chat:       { title: "Guest Chat",        subtitle: "AI Concierge Interface" },
  admin:      { title: "Admin Panel",       subtitle: "Hotel Management" },
  operations: { title: "Operations",        subtitle: "Daily Hotel Operations" },
  analytics:  { title: "Analytics",         subtitle: "Performance Metrics & Insights" },
};

export default function TopBar({ user, view, sidebarOpen, setSidebarOpen, onLogout }) {
  const [wsConnected, setWsConnected] = useState(false);
  const info = VIEW_TITLES[view] || { title: "Dashboard", subtitle: "" };

  useEffect(() => {
    // Reflect WebSocket connection via a custom event from A2ADashboard
    const handler = (e) => setWsConnected(e.detail?.connected ?? false);
    window.addEventListener("a2a-ws-status", handler);
    return () => window.removeEventListener("a2a-ws-status", handler);
  }, []);

  return (
    <header
      data-testid="topbar"
      style={{
        height: 60,
        background: "rgba(15,23,42,0.9)",
        borderBottom: "1px solid #1E293B",
        display: "flex",
        alignItems: "center",
        padding: "0 1.5rem",
        gap: 16,
        backdropFilter: "blur(8px)",
        flexShrink: 0,
      }}
    >
      <button
        data-testid="topbar-menu"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{ background: "none", border: "none", cursor: "pointer", color: "#64748B", padding: 4, borderRadius: 6, display: "flex" }}
      >
        <Menu size={20} />
      </button>

      <div style={{ flex: 1 }}>
        <h1 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1rem", color: "#F1F5F9", lineHeight: 1 }}>{info.title}</h1>
        <p style={{ fontSize: "0.7rem", color: "#64748B", marginTop: 2 }}>{info.subtitle}</p>
      </div>

      {/* WS Status */}
      {view === "a2a" && (
        <div
          data-testid="ws-status"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "4px 10px",
            borderRadius: 20,
            background: wsConnected ? "rgba(34,197,94,0.1)" : "rgba(100,116,139,0.1)",
            border: `1px solid ${wsConnected ? "rgba(34,197,94,0.3)" : "rgba(100,116,139,0.3)"}`,
            fontSize: "0.7rem",
            fontFamily: "JetBrains Mono, monospace",
            color: wsConnected ? "#22C55E" : "#64748B",
          }}
        >
          {wsConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          {wsConnected ? "LIVE" : "OFFLINE"}
        </div>
      )}

      {/* Time */}
      <Clock />
    </header>
  );
}

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ fontSize: "0.72rem", fontFamily: "JetBrains Mono, monospace", color: "#64748B", textAlign: "right" }}>
      <div style={{ color: "#94A3B8" }}>{time.toLocaleTimeString()}</div>
      <div>{time.toLocaleDateString()}</div>
    </div>
  );
}
