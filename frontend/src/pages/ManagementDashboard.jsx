import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User, Loader2, BrainCircuit, TrendingUp, Users, 
  BedDouble, DollarSign, BarChart3, AlertCircle, HelpCircle 
} from "lucide-react";

const EXAMPLE_QUERIES = [
  { icon: TrendingUp, text: "What is today's occupancy rate?", category: "occupancy" },
  { icon: DollarSign, text: "What was yesterday's total revenue?", category: "revenue" },
  { icon: Users, text: "How many guests checked in today?", category: "guests" },
  { icon: BedDouble, text: "Which rooms need housekeeping?", category: "operations" },
  { icon: AlertCircle, text: "Any pending guest complaints?", category: "complaints" },
  { icon: BarChart3, text: "Show me this week's performance summary", category: "summary" }
];

export default function ManagementDashboard({ user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL;

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
      // For now, use a mock response - this will be connected to ManagementAgent later
      // In Phase 3 (Management AI), this will query the live database
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const assistantMessage = {
        role: "assistant",
        content: `**Management Intelligence Response** (Demo Mode)\n\nYour query: "${input}"\n\n*This is a placeholder response. The full Management Intelligence AI will be implemented in Phase 3, connecting to the live database to provide real-time business metrics and insights.*\n\n**Sample Response Format:**\n- Today's Occupancy: 78%\n- Revenue MTD: $45,230\n- Pending Issues: 3\n- Check-ins Today: 12`
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Management chat error:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I apologize, but I encountered an error processing your request. Please try again."
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
      padding: "1.5rem"
    }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
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
              Ask real-time questions about occupancy, revenue, operations, and business performance.
            </p>
          </div>
        </div>
        
        {/* Role indicator */}
        <div style={{ 
          display: "inline-flex", 
          alignItems: "center", 
          gap: 6,
          padding: "4px 12px",
          background: "rgba(167,139,250,0.1)",
          border: "1px solid rgba(167,139,250,0.2)",
          borderRadius: 20,
          fontSize: "0.75rem",
          color: "#A78BFA"
        }}>
          <Users size={12} />
          {user?.role === "admin" ? "Administrator Access" : "Manager Access"}
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ 
        flex: 1, 
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
          padding: "1.5rem",
          display: "flex",
          flexDirection: "column",
          gap: 16
        }}>
          {messages.length === 0 ? (
            <div style={{ 
              flex: 1, 
              display: "flex", 
              flexDirection: "column", 
              alignItems: "center", 
              justifyContent: "center",
              gap: 32
            }}>
              <div style={{ textAlign: "center" }}>
                <BrainCircuit size={56} color="#A78BFA" style={{ marginBottom: 16, opacity: 0.6 }} />
                <h3 style={{ color: "#F1F5F9", fontSize: "1.25rem", marginBottom: 8 }}>
                  Business Intelligence at Your Fingertips
                </h3>
                <p style={{ color: "#64748B", fontSize: "0.875rem", maxWidth: 500 }}>
                  Ask me about occupancy rates, revenue metrics, guest statistics, operational status, 
                  or any business intelligence question. I have access to real-time hotel data.
                </p>
              </div>
              
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(3, 1fr)", 
                gap: 12,
                maxWidth: 700,
                width: "100%"
              }}>
                {EXAMPLE_QUERIES.map((example, idx) => {
                  const Icon = example.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleExampleClick(example)}
                      data-testid={`example-query-${idx}`}
                      style={{
                        padding: "1rem",
                        background: "rgba(167,139,250,0.08)",
                        border: "1px solid rgba(167,139,250,0.2)",
                        borderRadius: 12,
                        color: "#94A3B8",
                        fontSize: "0.8rem",
                        textAlign: "left",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                        display: "flex",
                        flexDirection: "column",
                        gap: 8
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = "rgba(167,139,250,0.15)";
                        e.currentTarget.style.color = "#F1F5F9";
                        e.currentTarget.style.borderColor = "rgba(167,139,250,0.4)";
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = "rgba(167,139,250,0.08)";
                        e.currentTarget.style.color = "#94A3B8";
                        e.currentTarget.style.borderColor = "rgba(167,139,250,0.2)";
                      }}
                    >
                      <Icon size={18} color="#A78BFA" />
                      <span>{example.text}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  gap: 12,
                  flexDirection: msg.role === "user" ? "row-reverse" : "row"
                }}
              >
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  background: msg.role === "user" 
                    ? "linear-gradient(135deg, #38BDF8, #0EA5E9)" 
                    : "linear-gradient(135deg, #A78BFA, #8B5CF6)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0
                }}>
                  {msg.role === "user" 
                    ? <User size={18} color="#0F172A" />
                    : <BrainCircuit size={18} color="#0F172A" />
                  }
                </div>
                <div style={{
                  maxWidth: "75%",
                  padding: "1rem 1.25rem",
                  borderRadius: 12,
                  background: msg.role === "user" 
                    ? "rgba(56,189,248,0.12)" 
                    : "rgba(167,139,250,0.08)",
                  border: msg.role === "user"
                    ? "1px solid rgba(56,189,248,0.25)"
                    : "1px solid rgba(167,139,250,0.15)",
                  color: "#F1F5F9",
                  fontSize: "0.9rem",
                  lineHeight: 1.7,
                  whiteSpace: "pre-wrap"
                }}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div style={{ display: "flex", gap: 12 }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #A78BFA, #8B5CF6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <BrainCircuit size={18} color="#0F172A" />
              </div>
              <div style={{
                padding: "1rem 1.25rem",
                borderRadius: 12,
                background: "rgba(167,139,250,0.08)",
                border: "1px solid rgba(167,139,250,0.15)",
                display: "flex",
                alignItems: "center",
                gap: 10
              }}>
                <Loader2 size={18} className="spin" color="#A78BFA" />
                <span style={{ color: "#94A3B8", fontSize: "0.875rem" }}>
                  Analyzing data...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ 
          padding: "1rem 1.5rem", 
          borderTop: "1px solid #334155",
          background: "rgba(15,23,42,0.5)"
        }}>
          <div style={{ 
            display: "flex", 
            gap: 12,
            alignItems: "center"
          }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about occupancy, revenue, operations..."
              data-testid="management-chat-input"
              style={{
                flex: 1,
                padding: "0.875rem 1rem",
                borderRadius: 10,
                border: "1px solid #334155",
                background: "#0F172A",
                color: "#F1F5F9",
                fontSize: "0.9rem",
                outline: "none"
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              data-testid="management-chat-send"
              style={{
                width: 48,
                height: 48,
                borderRadius: 10,
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
              <Send size={20} color={input.trim() ? "#0F172A" : "#64748B"} />
            </button>
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
