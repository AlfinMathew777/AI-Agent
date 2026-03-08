import { useState, useEffect, useRef, useCallback } from "react";
import { Bot, Wifi, WifiOff, Activity, Zap, RefreshCw, Terminal, Play, RotateCcw } from "lucide-react";

const AGENT_META = {
  guest_agent:       { name: "Guest Agent",       role: "NLP & Intent",     color: "#38BDF8", icon: "🧠" },
  booking_agent:     { name: "Booking Agent",     role: "Availability",     color: "#22C55E", icon: "📅" },
  pricing_agent:     { name: "Pricing Agent",     role: "Dynamic Pricing",  color: "#F59E0B", icon: "💰" },
  negotiation_agent: { name: "Negotiation Agent", role: "Discounts",        color: "#A78BFA", icon: "🤝" },
  payment_agent:     { name: "Payment Agent",     role: "Transactions",     color: "#34D399", icon: "💳" },
  inventory_agent:   { name: "Inventory Agent",   role: "Room Inventory",   color: "#60A5FA", icon: "🏨" },
  operations_agent:  { name: "Operations Agent",  role: "Housekeeping",     color: "#FB923C", icon: "🔧" },
  orchestrator:      { name: "Orchestrator",      role: "Coordinator",      color: "#F472B6", icon: "⚡" },
};

const STATUS_STYLES = {
  idle:       { bg: "rgba(100,116,139,0.12)", color: "#64748B", border: "rgba(100,116,139,0.2)", label: "IDLE" },
  processing: { bg: "rgba(245,158,11,0.12)",  color: "#F59E0B", border: "rgba(245,158,11,0.3)",  label: "PROC" },
  completed:  { bg: "rgba(34,197,94,0.12)",   color: "#22C55E", border: "rgba(34,197,94,0.3)",   label: "DONE" },
  error:      { bg: "rgba(239,68,68,0.12)",   color: "#EF4444", border: "rgba(239,68,68,0.3)",   label: "ERR"  },
  active:     { bg: "rgba(56,189,248,0.12)",  color: "#38BDF8", border: "rgba(56,189,248,0.3)",  label: "ACT"  },
};

const DEMO_PROMPTS = [
  "Book 2 deluxe rooms for 3 nights starting tomorrow",
  "I need a suite for 4 nights. Can I get 10% off?",
  "Is there an ocean view room available for the weekend?",
  "I want 5 rooms for a corporate event, can you negotiate a deal?",
];

export default function A2ADashboard() {
  const [agents, setAgents] = useState(() =>
    Object.entries(AGENT_META).map(([id, meta]) => ({ agent_id: id, ...meta, status: "idle" }))
  );
  const [feed, setFeed] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [activePrompt, setActivePrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [lastOutcome, setLastOutcome] = useState(null);
  const feedRef = useRef(null);
  const wsRef = useRef(null);
  const [stats, setStats] = useState({ total_runs: 0, confirmed: 0, avg_time: 0 });

  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = window.location.origin.replace("https://", "wss://").replace("http://", "ws://") + "/api/ws/a2a";
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      window.dispatchEvent(new CustomEvent("a2a-ws-status", { detail: { connected: true } }));
    };

    ws.onclose = () => {
      setWsConnected(false);
      window.dispatchEvent(new CustomEvent("a2a-ws-status", { detail: { connected: false } }));
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) connectWS();
      }, 3000);
    };

    ws.onerror = () => ws.close();

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "connected" || data.type === "agent_statuses") {
          if (data.agents) {
            setAgents(prev => prev.map(a => {
              const updated = data.agents.find(u => u.agent_id === a.agent_id);
              return updated ? { ...a, status: updated.status || "idle" } : a;
            }));
          }
        }
        if (data.type === "agent_event" && data.event) {
          const ev = data.event;
          const ts = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
          setFeed(prev => { const entry = { ...ev, ts, id: Date.now() + Math.random() }; return [...prev, entry].slice(-100); });
          setAgents(prev => prev.map(a => a.agent_id === ev.agent_id ? { ...a, status: ev.status || a.status } : a));
          if (ev.status === "completed" && ev.agent_id === "payment_agent" && ev.metadata?.confirmation) {
            setLastOutcome({ confirmation: ev.metadata.confirmation, total: ev.metadata.total_charged, room_type: ev.metadata.room_type, check_in: ev.metadata.check_in, check_out: ev.metadata.check_out });
            setStats(s => ({ ...s, confirmed: s.confirmed + 1 }));
            setRunning(false);
          }
        }
        if (data.type === "events_replay" && Array.isArray(data.events)) {
          const entries = data.events.filter(e => e.event).map(e => ({ ...e.event, ts: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }), id: Date.now() + Math.random() }));
          setFeed(entries.slice(-30));
        }
      } catch {}
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    connectWS();
    return () => wsRef.current?.close();
  }, [connectWS]);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [feed]);

  const runPipeline = async (prompt) => {
    const msg = prompt || activePrompt;
    if (!msg.trim() || running) return;
    setRunning(true);
    setLastOutcome(null);
    const sid = Math.random().toString(36).slice(2, 8);
    setSessionId(sid);
    setStats(s => ({ ...s, total_runs: s.total_runs + 1 }));

    // Add user message to feed
    setFeed(prev => [...prev, {
      agent_id: "user",
      agent_name: "User",
      action: "Input",
      content: msg,
      status: "active",
      color: "#F1F5F9",
      ts: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      id: Date.now(),
    }]);

    try {
      const start = Date.now();
      const res = await fetch("/api/a2a/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Tenant-ID": "default-tenant-0000" },
        body: JSON.stringify({ message: msg, session_id: sid }),
      });
      const data = await res.json();
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      setStats(s => ({ ...s, avg_time: elapsed }));

      if (data.data?.confirmation && !lastOutcome) {
        setLastOutcome({ confirmation: data.data.confirmation, total: data.data.total });
      }
    } catch (e) {
      console.error("Pipeline error:", e);
    } finally {
      setTimeout(() => setRunning(false), 2000);
      // Reset all agents to idle after pipeline
      setTimeout(() => setAgents(prev => prev.map(a => ({ ...a, status: "idle" }))), 4000);
    }
  };

  const clearFeed = () => {
    setFeed([]);
    setLastOutcome(null);
    setAgents(prev => prev.map(a => ({ ...a, status: "idle" })));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, minHeight: "100%", paddingBottom: 24 }}>
      {/* Header Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
        {[
          { label: "Pipeline Runs",     value: stats.total_runs, color: "#38BDF8" },
          { label: "Bookings Confirmed", value: stats.confirmed,  color: "#22C55E" },
          { label: "Avg Pipeline (s)",  value: stats.avg_time,   color: "#F59E0B" },
          { label: "Clients Connected", value: wsConnected ? 1 : 0, color: "#A78BFA" },
        ].map(s => (
          <div key={s.label} className="glass-card" style={{ padding: "1rem 1.25rem" }}>
            <div style={{ fontSize: "1.6rem", fontFamily: "Chivo", fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: "0.7rem", color: "#64748B", marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Pipeline Input */}
      <div className="glass-card" style={{ padding: "1.25rem" }}>
        <div style={{ fontSize: "0.75rem", color: "#64748B", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
          <Zap size={13} color="#F59E0B" />  TRIGGER A2A PIPELINE
        </div>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          <input
            data-testid="a2a-input"
            value={activePrompt}
            onChange={e => setActivePrompt(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runPipeline()}
            placeholder="e.g. Book 2 deluxe rooms for 3 nights..."
            style={{ flex: 1, padding: "0.625rem 1rem", background: "rgba(0,0,0,0.3)", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.875rem", outline: "none", fontFamily: "JetBrains Mono, monospace" }}
          />
          <button
            data-testid="a2a-run"
            onClick={() => runPipeline()}
            disabled={running || !activePrompt.trim()}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "0.625rem 1.25rem", background: running ? "rgba(56,189,248,0.3)" : "rgba(56,189,248,0.85)", border: "none", borderRadius: 8, color: "#0F172A", cursor: running ? "not-allowed" : "pointer", fontWeight: 700, fontSize: "0.85rem", boxShadow: "0 0 12px rgba(56,189,248,0.2)" }}>
            {running ? <RefreshCw size={15} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={15} />}
            {running ? "Running..." : "Run"}
          </button>
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {DEMO_PROMPTS.map(p => (
            <button key={p} data-testid={`demo-prompt-${p.slice(0,8)}`} onClick={() => { setActivePrompt(p); runPipeline(p); }} disabled={running} style={{ fontSize: "0.72rem", padding: "3px 10px", borderRadius: 20, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#94A3B8", cursor: "pointer" }}>
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Agent Cards + Live Feed */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Agent Grid */}
        <div>
          <div style={{ fontSize: "0.75rem", color: "#64748B", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
            <Activity size={13} color="#38BDF8" /> AGENT STATUS GRID
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {agents.map(agent => {
              const st = STATUS_STYLES[agent.status] || STATUS_STYLES.idle;
              const isActive = agent.status === "processing";
              return (
                <div
                  key={agent.agent_id}
                  data-testid={`agent-card-${agent.agent_id}`}
                  className="glass-card"
                  style={{
                    padding: "1rem",
                    borderColor: isActive ? agent.color + "40" : undefined,
                    boxShadow: isActive ? `0 0 16px ${agent.color}20` : undefined,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                    <div style={{ width: 32, height: 32, borderRadius: 8, background: `${agent.color}15`, border: `1px solid ${agent.color}25`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1rem" }}>
                      {agent.icon}
                    </div>
                    <span style={{ fontSize: "0.6rem", fontFamily: "JetBrains Mono, monospace", padding: "2px 6px", borderRadius: 4, background: st.bg, color: st.color, border: `1px solid ${st.border}`, letterSpacing: "0.05em" }}>
                      {isActive && <span style={{ display: "inline-block", marginRight: 3, animation: "pulse-dot 1s ease-in-out infinite" }}>●</span>}
                      {st.label}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#E2E8F0" }}>{agent.name}</div>
                  <div style={{ fontSize: "0.65rem", color: "#64748B", marginTop: 2 }}>{agent.role}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Feed */}
        <div>
          <div style={{ fontSize: "0.75rem", color: "#64748B", marginBottom: 10, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Terminal size={13} color="#38BDF8" /> LIVE AGENT FEED
              {wsConnected && <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22C55E", display: "inline-block" }} className="status-dot-live" />}
            </span>
            <button data-testid="clear-feed" onClick={clearFeed} style={{ background: "none", border: "none", cursor: "pointer", color: "#64748B", fontSize: "0.7rem", display: "flex", alignItems: "center", gap: 4 }}>
              <RotateCcw size={11} /> Clear
            </button>
          </div>
          <div
            ref={feedRef}
            data-testid="agent-feed"
            className="terminal-feed"
            style={{ height: 420, overflowY: "auto" }}
          >
            {feed.length === 0 ? (
              <div style={{ color: "#334155", textAlign: "center", paddingTop: "3rem", fontSize: "0.75rem" }}>
                <Terminal size={24} style={{ margin: "0 auto 0.5rem", display: "block", color: "#334155" }} />
                Waiting for agent activity...<br />
                <span style={{ color: "#1E3A5F" }}>Run a pipeline above to see the A2A flow</span>
              </div>
            ) : (
              feed.map((ev, i) => {
                const meta = AGENT_META[ev.agent_id];
                const color = ev.color || meta?.color || "#94A3B8";
                return (
                  <div key={ev.id || i} style={{ marginBottom: "0.6rem", animation: "fadeInUp 0.3s ease forwards", borderLeft: `2px solid ${color}40`, paddingLeft: "0.75rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <span style={{ color, fontWeight: 600 }}>[{(ev.agent_name || ev.agent_id || "Agent").toUpperCase().replace(/_/g, " ")}]</span>
                      <span style={{ color: "#334155", fontSize: "0.65rem" }}>{ev.ts}</span>
                      {ev.action && (
                        <span style={{ fontSize: "0.6rem", padding: "1px 5px", borderRadius: 3, background: `${color}15`, color, border: `1px solid ${color}30` }}>{ev.action}</span>
                      )}
                    </div>
                    <div style={{ color: "#94A3B8", paddingLeft: "0.25rem", fontSize: "0.75rem" }}>{ev.content}</div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Booking Outcome */}
      {lastOutcome && (
        <div
          data-testid="booking-outcome"
          className="glass-card"
          style={{ padding: "1.25rem", borderColor: "rgba(34,197,94,0.3)", boxShadow: "0 0 20px rgba(34,197,94,0.1)" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <div style={{ width: 28, height: 28, borderRadius: 6, background: "rgba(34,197,94,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: "0.875rem" }}>✓</span>
            </div>
            <span style={{ fontFamily: "Chivo", fontWeight: 700, color: "#22C55E", fontSize: "0.9rem" }}>Pipeline Complete — Booking Confirmed</span>
          </div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {[
              { label: "Confirmation", value: lastOutcome.confirmation },
              { label: "Room Type",    value: lastOutcome.room_type || "—" },
              { label: "Check In",     value: lastOutcome.check_in || "—" },
              { label: "Check Out",    value: lastOutcome.check_out || "—" },
              { label: "Total",        value: lastOutcome.total ? `$${lastOutcome.total}` : "—" },
            ].map(item => (
              <div key={item.label}>
                <div style={{ fontSize: "0.65rem", color: "#64748B" }}>{item.label}</div>
                <div style={{ fontSize: "0.875rem", fontFamily: "JetBrains Mono, monospace", color: "#22C55E", fontWeight: 600 }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
