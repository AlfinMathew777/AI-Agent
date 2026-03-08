import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User, Loader2, BrainCircuit, TrendingUp, Users, 
  BedDouble, DollarSign, BarChart3, AlertCircle, Calendar, 
  ArrowUpRight, ArrowDownRight, RefreshCw, Clock, CheckCircle,
  AlertTriangle, Info
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || "";

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

const EXAMPLE_QUERIES = [
  { icon: TrendingUp, text: "What is today's occupancy rate?", category: "occupancy" },
  { icon: DollarSign, text: "Show me today's revenue summary", category: "revenue" },
  { icon: Users, text: "How many guests are checking in today?", category: "guests" },
  { icon: BedDouble, text: "Which room types have availability?", category: "rooms" },
  { icon: Calendar, text: "What reservations are pending?", category: "reservations" },
  { icon: BarChart3, text: "Give me a weekly performance summary", category: "summary" }
];

export default function ManagementDashboard({ user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [insights, setInsights] = useState([]);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const messagesEndRef = useRef(null);

  // Fetch metrics on mount
  useEffect(() => {
    fetchMetrics();
    fetchInsights();
  }, []);

  const fetchMetrics = async () => {
    setMetricsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/management/metrics`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    } finally {
      setMetricsLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const res = await fetch(`${API_URL}/api/management/insights`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setInsights(data.insights || []);
      }
    } catch (err) {
      console.error("Failed to fetch insights:", err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/management/chat`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: input,
          include_metrics: false
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      
      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        timestamp: data.timestamp
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Management chat error:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I apologize, but I encountered an error connecting to the analytics system. Please try again.",
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setInput(example.text);
  };

  return (
    <div data-testid="management-dashboard" style={{ 
      height: "100%", 
      display: "flex", 
      flexDirection: "column",
      background: "#0F172A",
      padding: "1.5rem",
      overflow: "auto"
    }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ 
              width: 48, 
              height: 48, 
              borderRadius: 12, 
              background: "linear-gradient(135deg, #A78BFA, #8B5CF6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <BrainCircuit size={24} color="#0F172A" />
            </div>
            <div>
              <h1 style={{ 
                fontFamily: "Chivo", 
                fontSize: "1.5rem", 
                fontWeight: 700, 
                color: "#F1F5F9",
                margin: 0
              }}>
                Management Intelligence
              </h1>
              <p style={{ 
                color: "#94A3B8", 
                fontSize: "0.875rem",
                margin: 0
              }}>
                Real-time business insights powered by AI
              </p>
            </div>
          </div>
          
          <button
            onClick={() => { fetchMetrics(); fetchInsights(); }}
            disabled={metricsLoading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "0.5rem 1rem",
              background: "rgba(167,139,250,0.1)",
              border: "1px solid rgba(167,139,250,0.2)",
              borderRadius: 8,
              color: "#A78BFA",
              cursor: metricsLoading ? "not-allowed" : "pointer",
              fontSize: "0.8rem"
            }}
          >
            <RefreshCw size={14} className={metricsLoading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "repeat(4, 1fr)", 
        gap: 16, 
        marginBottom: "1.5rem",
        flexShrink: 0
      }}>
        <KPICard
          title="Occupancy Rate"
          value={metrics?.occupancy_rate ?? "--"}
          suffix="%"
          icon={TrendingUp}
          color="#22C55E"
          subtitle={`${metrics?.occupied_rooms ?? 0} / ${metrics?.total_rooms ?? 0} rooms`}
          loading={metricsLoading}
        />
        <KPICard
          title="Revenue Today"
          value={metrics?.revenue_today ?? 0}
          prefix="$"
          icon={DollarSign}
          color="#38BDF8"
          subtitle={`Week: $${(metrics?.revenue_week ?? 0).toLocaleString()}`}
          loading={metricsLoading}
          format="currency"
        />
        <KPICard
          title="Active Reservations"
          value={metrics?.active_reservations ?? "--"}
          icon={Calendar}
          color="#F59E0B"
          subtitle={`${metrics?.pending_reservations ?? 0} pending`}
          loading={metricsLoading}
        />
        <KPICard
          title="Available Rooms"
          value={metrics?.available_rooms ?? "--"}
          icon={BedDouble}
          color="#A78BFA"
          subtitle={`${metrics?.checkins_today ?? 0} arriving today`}
          loading={metricsLoading}
        />
      </div>

      {/* Insights Bar */}
      {insights.length > 0 && (
        <div style={{ 
          display: "flex", 
          gap: 12, 
          marginBottom: "1.5rem", 
          overflowX: "auto",
          flexShrink: 0,
          paddingBottom: 4
        }}>
          {insights.map((insight, idx) => (
            <InsightCard key={idx} insight={insight} />
          ))}
        </div>
      )}

      {/* Main Content: Chat + Upcoming */}
      <div style={{ 
        flex: 1, 
        display: "grid", 
        gridTemplateColumns: "2fr 1fr", 
        gap: 16,
        minHeight: 0
      }}>
        {/* Chat Area */}
        <div style={{ 
          display: "flex", 
          flexDirection: "column",
          background: "#1E293B",
          borderRadius: 16,
          border: "1px solid #334155",
          overflow: "hidden"
        }}>
          {/* Messages */}
          <div style={{ 
            flex: 1, 
            overflowY: "auto", 
            padding: "1.25rem",
            display: "flex",
            flexDirection: "column",
            gap: 14
          }}>
            {messages.length === 0 ? (
              <div style={{ 
                flex: 1, 
                display: "flex", 
                flexDirection: "column", 
                alignItems: "center", 
                justifyContent: "center",
                gap: 20
              }}>
                <div style={{ textAlign: "center" }}>
                  <BrainCircuit size={40} color="#A78BFA" style={{ marginBottom: 12, opacity: 0.6 }} />
                  <h3 style={{ color: "#F1F5F9", fontSize: "1rem", marginBottom: 6 }}>
                    Ask me anything about your hotel
                  </h3>
                  <p style={{ color: "#64748B", fontSize: "0.8rem", maxWidth: 400 }}>
                    I have access to real-time occupancy, revenue, reservations, and operational data.
                  </p>
                </div>
                
                <div style={{ 
                  display: "grid", 
                  gridTemplateColumns: "repeat(2, 1fr)", 
                  gap: 10,
                  maxWidth: 500,
                  width: "100%"
                }}>
                  {EXAMPLE_QUERIES.slice(0, 4).map((example, idx) => {
                    const Icon = example.icon;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleExampleClick(example)}
                        data-testid={`example-query-${idx}`}
                        style={{
                          padding: "0.75rem",
                          background: "rgba(167,139,250,0.08)",
                          border: "1px solid rgba(167,139,250,0.2)",
                          borderRadius: 10,
                          color: "#94A3B8",
                          fontSize: "0.75rem",
                          textAlign: "left",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          display: "flex",
                          alignItems: "center",
                          gap: 8
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.background = "rgba(167,139,250,0.15)";
                          e.currentTarget.style.color = "#F1F5F9";
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.background = "rgba(167,139,250,0.08)";
                          e.currentTarget.style.color = "#94A3B8";
                        }}
                      >
                        <Icon size={14} color="#A78BFA" style={{ flexShrink: 0 }} />
                        <span>{example.text}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))
            )}
            {loading && (
              <div style={{ display: "flex", gap: 10 }}>
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #A78BFA, #8B5CF6)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <BrainCircuit size={16} color="#0F172A" />
                </div>
                <div style={{
                  padding: "0.75rem 1rem",
                  borderRadius: 10,
                  background: "rgba(167,139,250,0.08)",
                  border: "1px solid rgba(167,139,250,0.15)",
                  display: "flex",
                  alignItems: "center",
                  gap: 8
                }}>
                  <Loader2 size={14} className="spin" color="#A78BFA" />
                  <span style={{ color: "#94A3B8", fontSize: "0.8rem" }}>
                    Analyzing data...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ 
            padding: "1rem", 
            borderTop: "1px solid #334155",
            background: "rgba(15,23,42,0.5)"
          }}>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask about occupancy, revenue, reservations..."
                data-testid="management-chat-input"
                style={{
                  flex: 1,
                  padding: "0.7rem 1rem",
                  borderRadius: 8,
                  border: "1px solid #334155",
                  background: "#0F172A",
                  color: "#F1F5F9",
                  fontSize: "0.85rem",
                  outline: "none"
                }}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                data-testid="management-chat-send"
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 8,
                  background: input.trim() 
                    ? "linear-gradient(135deg, #A78BFA, #8B5CF6)" 
                    : "#334155",
                  border: "none",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: input.trim() ? "pointer" : "not-allowed",
                  transition: "all 0.15s ease"
                }}
              >
                <Send size={16} color={input.trim() ? "#0F172A" : "#64748B"} />
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel: Upcoming & Recent */}
        <div style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: 16,
          overflow: "hidden"
        }}>
          {/* Upcoming Arrivals */}
          <div className="glass-card" style={{ 
            padding: "1rem",
            flex: 1,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column"
          }}>
            <h4 style={{ 
              color: "#F1F5F9", 
              fontSize: "0.85rem", 
              marginBottom: 12, 
              display: "flex", 
              alignItems: "center", 
              gap: 8 
            }}>
              <Users size={14} color="#22C55E" />
              Upcoming Arrivals
            </h4>
            <div style={{ flex: 1, overflowY: "auto" }}>
              {metricsLoading ? (
                <div style={{ textAlign: "center", padding: "2rem", color: "#64748B" }}>
                  <Loader2 size={18} className="spin" />
                </div>
              ) : (metrics?.upcoming_arrivals?.length || 0) === 0 ? (
                <div style={{ textAlign: "center", padding: "1.5rem", color: "#64748B", fontSize: "0.75rem" }}>
                  No upcoming arrivals
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {metrics.upcoming_arrivals.slice(0, 5).map((arrival, idx) => (
                    <div key={idx} style={{
                      padding: "0.6rem",
                      background: "rgba(34,197,94,0.08)",
                      borderRadius: 8,
                      border: "1px solid rgba(34,197,94,0.15)"
                    }}>
                      <div style={{ color: "#F1F5F9", fontSize: "0.8rem", fontWeight: 500 }}>
                        {arrival.guest_name}
                      </div>
                      <div style={{ color: "#64748B", fontSize: "0.7rem", marginTop: 2 }}>
                        Room {arrival.room_number} • {arrival.check_in_date}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Room Types */}
          <div className="glass-card" style={{ 
            padding: "1rem",
            flex: 1,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column"
          }}>
            <h4 style={{ 
              color: "#F1F5F9", 
              fontSize: "0.85rem", 
              marginBottom: 12, 
              display: "flex", 
              alignItems: "center", 
              gap: 8 
            }}>
              <BedDouble size={14} color="#A78BFA" />
              Room Availability
            </h4>
            <div style={{ flex: 1, overflowY: "auto" }}>
              {metricsLoading ? (
                <div style={{ textAlign: "center", padding: "2rem", color: "#64748B" }}>
                  <Loader2 size={18} className="spin" />
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {(metrics?.room_types || []).map((rt, idx) => (
                    <div key={idx} style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.5rem 0.6rem",
                      background: "rgba(167,139,250,0.05)",
                      borderRadius: 6
                    }}>
                      <span style={{ color: "#CBD5E1", fontSize: "0.75rem" }}>
                        {rt.room_type}
                      </span>
                      <span style={{ 
                        color: rt.available > 0 ? "#22C55E" : "#F59E0B", 
                        fontSize: "0.75rem",
                        fontWeight: 600
                      }}>
                        {rt.available} / {rt.total}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}


// KPI Card Component
function KPICard({ title, value, prefix = "", suffix = "", icon: Icon, color, subtitle, loading, format }) {
  const displayValue = format === "currency" 
    ? Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    : value;

  return (
    <div className="glass-card" style={{ padding: "1.25rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div style={{ 
          color: "#94A3B8", 
          fontSize: "0.75rem", 
          textTransform: "uppercase", 
          letterSpacing: "0.04em" 
        }}>
          {title}
        </div>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: `${color}15`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <Icon size={16} color={color} />
        </div>
      </div>
      <div style={{ 
        color: "#F1F5F9", 
        fontSize: "1.75rem", 
        fontWeight: 700, 
        fontFamily: "Chivo",
        marginBottom: 4
      }}>
        {loading ? (
          <Loader2 size={24} className="spin" color="#64748B" />
        ) : (
          <>{prefix}{displayValue}{suffix}</>
        )}
      </div>
      {subtitle && (
        <div style={{ color: "#64748B", fontSize: "0.7rem" }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}


// Insight Card Component
function InsightCard({ insight }) {
  const config = {
    success: { icon: CheckCircle, color: "#22C55E", bg: "rgba(34,197,94,0.1)", border: "rgba(34,197,94,0.2)" },
    warning: { icon: AlertTriangle, color: "#F59E0B", bg: "rgba(245,158,11,0.1)", border: "rgba(245,158,11,0.2)" },
    info: { icon: Info, color: "#38BDF8", bg: "rgba(56,189,248,0.1)", border: "rgba(56,189,248,0.2)" },
    error: { icon: AlertCircle, color: "#EF4444", bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.2)" }
  };
  
  const { icon: Icon, color, bg, border } = config[insight.type] || config.info;

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "0.75rem 1rem",
      background: bg,
      border: `1px solid ${border}`,
      borderRadius: 10,
      minWidth: 250,
      flexShrink: 0
    }}>
      <Icon size={18} color={color} />
      <div>
        <div style={{ color: "#F1F5F9", fontSize: "0.8rem", fontWeight: 500 }}>
          {insight.title}
        </div>
        <div style={{ color: "#94A3B8", fontSize: "0.7rem" }}>
          {insight.message}
        </div>
      </div>
    </div>
  );
}


// Message Bubble Component
function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div style={{
      display: "flex",
      gap: 10,
      flexDirection: isUser ? "row-reverse" : "row"
    }}>
      <div style={{
        width: 32,
        height: 32,
        borderRadius: "50%",
        background: isUser 
          ? "linear-gradient(135deg, #38BDF8, #0EA5E9)" 
          : "linear-gradient(135deg, #A78BFA, #8B5CF6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0
      }}>
        {isUser 
          ? <User size={14} color="#0F172A" />
          : <BrainCircuit size={14} color="#0F172A" />
        }
      </div>
      <div style={{
        maxWidth: "80%",
        padding: "0.75rem 1rem",
        borderRadius: 10,
        background: isUser 
          ? "rgba(56,189,248,0.12)" 
          : message.isError 
            ? "rgba(239,68,68,0.1)"
            : "rgba(167,139,250,0.08)",
        border: isUser
          ? "1px solid rgba(56,189,248,0.25)"
          : message.isError
            ? "1px solid rgba(239,68,68,0.2)"
            : "1px solid rgba(167,139,250,0.15)",
        color: "#F1F5F9",
        fontSize: "0.85rem",
        lineHeight: 1.6,
        whiteSpace: "pre-wrap"
      }}>
        {message.content}
      </div>
    </div>
  );
}
