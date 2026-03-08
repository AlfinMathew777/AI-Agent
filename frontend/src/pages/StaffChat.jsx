import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, FileText, BookOpen, HelpCircle, Headphones, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || "";

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

// Fallback example questions if API fails
const FALLBACK_EXAMPLES = {
  front_desk: [
    "What is the late check-out policy?",
    "How do I handle a guest complaint?",
    "What amenities come with the deluxe rooms?",
    "What's the procedure for lost and found items?"
  ],
  housekeeping: [
    "What is the standard room cleaning checklist?",
    "How do I handle a biohazard situation?",
    "What's the procedure for deep cleaning?",
    "How often should linens be changed?"
  ],
  restaurant: [
    "What are the allergen-free options on the menu?",
    "How do I handle a food allergy emergency?",
    "What's the wine pairing for the steak?",
    "What are the restaurant opening hours?"
  ],
  manager: [
    "What is the escalation procedure for guest complaints?",
    "How do I approve overtime for staff?",
    "What are the fire safety procedures?",
    "How do I handle a staffing shortage?"
  ],
  admin: [
    "What are the emergency evacuation procedures?",
    "How do I update the pricing structure?",
    "What's the vendor management process?",
    "How do I onboard a new employee?"
  ]
};

const ROLE_TITLES = {
  front_desk: "Front Desk Assistant",
  housekeeping: "Housekeeping Assistant",
  restaurant: "Restaurant Assistant",
  manager: "Management Assistant",
  admin: "Admin Assistant"
};

export default function StaffChat({ user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [roleContext, setRoleContext] = useState(null);
  const [exampleQuestions, setExampleQuestions] = useState([]);
  const messagesEndRef = useRef(null);
  
  const userRole = user?.role || "front_desk";

  // Fetch role context on mount
  useEffect(() => {
    fetchRoleContext();
  }, [userRole]);

  const fetchRoleContext = async () => {
    try {
      const res = await fetch(`${API_URL}/api/staff/context`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setRoleContext(data);
        setExampleQuestions(data.example_questions || FALLBACK_EXAMPLES[userRole] || []);
      } else {
        // Fallback
        setExampleQuestions(FALLBACK_EXAMPLES[userRole] || []);
      }
    } catch (err) {
      console.error("Failed to fetch role context:", err);
      setExampleQuestions(FALLBACK_EXAMPLES[userRole] || []);
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
      const res = await fetch(`${API_URL}/api/staff/chat`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      
      // Update session ID if new
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        chunks_used: data.chunks_used || 0
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Staff chat error:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I apologize, but I encountered an error connecting to the assistant. Please try again or contact support if the issue persists.",
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setInput(example);
  };

  const roleTitle = roleContext?.title || ROLE_TITLES[userRole] || "Staff Assistant";
  const focusAreas = roleContext?.focus_areas || [];

  return (
    <div data-testid="staff-chat-page" style={{ 
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
            background: "linear-gradient(135deg, #38BDF8, #0EA5E9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <Headphones size={24} color="#0F172A" />
          </div>
          <div>
            <h1 style={{ 
              fontFamily: "Chivo", 
              fontSize: "1.5rem", 
              fontWeight: 700, 
              color: "#F1F5F9",
              margin: 0
            }}>
              {roleTitle}
            </h1>
            <p style={{ 
              color: "#94A3B8", 
              fontSize: "0.875rem",
              margin: 0
            }}>
              Ask about hotel policies, procedures, and operational guidance
            </p>
          </div>
        </div>
        
        {/* Focus Areas Tags */}
        {focusAreas.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
            {focusAreas.slice(0, 5).map((area, idx) => (
              <span
                key={idx}
                style={{
                  padding: "4px 10px",
                  background: "rgba(56,189,248,0.1)",
                  border: "1px solid rgba(56,189,248,0.2)",
                  borderRadius: 16,
                  color: "#38BDF8",
                  fontSize: "0.7rem",
                  textTransform: "capitalize"
                }}
              >
                {area}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Chat Area */}
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
              gap: 24
            }}>
              <div style={{ textAlign: "center" }}>
                <BookOpen size={48} color="#38BDF8" style={{ marginBottom: 16, opacity: 0.5 }} />
                <h3 style={{ color: "#F1F5F9", fontSize: "1.1rem", marginBottom: 8 }}>
                  How can I help you today?
                </h3>
                <p style={{ color: "#64748B", fontSize: "0.875rem", maxWidth: 400 }}>
                  Ask me anything about hotel policies, procedures, or operational guidelines.
                  I'll provide role-specific guidance based on your position.
                </p>
              </div>
              
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(2, 1fr)", 
                gap: 12,
                maxWidth: 600,
                width: "100%"
              }}>
                {exampleQuestions.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(example)}
                    data-testid={`example-question-${idx}`}
                    style={{
                      padding: "0.75rem 1rem",
                      background: "rgba(56,189,248,0.08)",
                      border: "1px solid rgba(56,189,248,0.2)",
                      borderRadius: 8,
                      color: "#94A3B8",
                      fontSize: "0.8rem",
                      textAlign: "left",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      display: "flex",
                      alignItems: "center",
                      gap: 8
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = "rgba(56,189,248,0.15)";
                      e.currentTarget.style.color = "#F1F5F9";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "rgba(56,189,248,0.08)";
                      e.currentTarget.style.color = "#94A3B8";
                    }}
                  >
                    <HelpCircle size={14} style={{ flexShrink: 0 }} />
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <MessageBubble key={idx} message={msg} />
            ))
          )}
          {loading && (
            <div style={{ display: "flex", gap: 12 }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #A78BFA, #8B5CF6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <Bot size={16} color="#0F172A" />
              </div>
              <div style={{
                padding: "0.75rem 1rem",
                borderRadius: 12,
                background: "rgba(167,139,250,0.1)",
                border: "1px solid rgba(167,139,250,0.2)",
                display: "flex",
                alignItems: "center",
                gap: 8
              }}>
                <Loader2 size={16} className="spin" color="#A78BFA" />
                <span style={{ color: "#94A3B8", fontSize: "0.875rem" }}>Searching knowledge base...</span>
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
              placeholder="Ask about hotel policies and procedures..."
              data-testid="staff-chat-input"
              style={{
                flex: 1,
                padding: "0.75rem 1rem",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0F172A",
                color: "#F1F5F9",
                fontSize: "0.875rem",
                outline: "none"
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              data-testid="staff-chat-send"
              style={{
                width: 44,
                height: 44,
                borderRadius: 8,
                background: input.trim() 
                  ? "linear-gradient(135deg, #38BDF8, #0EA5E9)" 
                  : "#334155",
                border: "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: input.trim() ? "pointer" : "not-allowed",
                transition: "all 0.15s ease"
              }}
            >
              <Send size={18} color={input.trim() ? "#0F172A" : "#64748B"} />
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


// Message Bubble Component
function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === "user";
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        flexDirection: isUser ? "row-reverse" : "row"
      }}
    >
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
          ? <User size={16} color="#0F172A" />
          : <Bot size={16} color="#0F172A" />
        }
      </div>
      <div style={{ maxWidth: "75%" }}>
        <div style={{
          padding: "0.75rem 1rem",
          borderRadius: 12,
          background: isUser 
            ? "rgba(56,189,248,0.15)" 
            : message.isError 
              ? "rgba(239,68,68,0.1)"
              : "rgba(167,139,250,0.1)",
          border: isUser
            ? "1px solid rgba(56,189,248,0.3)"
            : message.isError
              ? "1px solid rgba(239,68,68,0.2)"
              : "1px solid rgba(167,139,250,0.2)",
          color: "#F1F5F9",
          fontSize: "0.875rem",
          lineHeight: 1.7,
          whiteSpace: "pre-wrap"
        }}>
          {message.content}
        </div>
        
        {/* Sources Section */}
        {hasSources && (
          <div style={{ marginTop: 8 }}>
            <button
              onClick={() => setShowSources(!showSources)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 8px",
                background: "rgba(167,139,250,0.08)",
                border: "1px solid rgba(167,139,250,0.15)",
                borderRadius: 6,
                color: "#A78BFA",
                fontSize: "0.7rem",
                cursor: "pointer"
              }}
            >
              <FileText size={12} />
              {message.sources.length} source{message.sources.length > 1 ? "s" : ""} referenced
              {showSources ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            
            {showSources && (
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                background: "rgba(0,0,0,0.2)", 
                borderRadius: 8,
                fontSize: "0.75rem",
                color: "#94A3B8"
              }}>
                {message.sources.map((source, idx) => (
                  <div key={idx} style={{ 
                    marginBottom: idx < message.sources.length - 1 ? 8 : 0,
                    paddingBottom: idx < message.sources.length - 1 ? 8 : 0,
                    borderBottom: idx < message.sources.length - 1 ? "1px solid #334155" : "none"
                  }}>
                    <div style={{ color: "#A78BFA", marginBottom: 4 }}>
                      Source {source.index}
                    </div>
                    <div style={{ fontStyle: "italic" }}>
                      "{source.preview}"
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
