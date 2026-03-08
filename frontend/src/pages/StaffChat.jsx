import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, FileText, BookOpen, HelpCircle, Headphones } from "lucide-react";

const ROLE_CONTEXT = {
  front_desk: {
    title: "Front Desk Assistant",
    description: "Ask about check-in/out procedures, reservation policies, guest services, and front desk operations.",
    examples: [
      "What is the late check-out policy?",
      "How do I handle a guest complaint?",
      "What amenities come with the deluxe rooms?",
      "What's the procedure for lost and found items?"
    ]
  },
  housekeeping: {
    title: "Housekeeping Assistant",
    description: "Ask about cleaning procedures, room standards, supplies, and housekeeping protocols.",
    examples: [
      "What is the standard room cleaning checklist?",
      "How do I handle a biohazard situation?",
      "What's the procedure for deep cleaning?",
      "How often should linens be changed?"
    ]
  },
  restaurant: {
    title: "Restaurant Assistant",
    description: "Ask about menu items, dietary restrictions, food safety, and restaurant operations.",
    examples: [
      "What are the allergen-free options on the menu?",
      "How do I handle a food allergy emergency?",
      "What's the wine pairing for the steak?",
      "What are the restaurant opening hours?"
    ]
  },
  manager: {
    title: "Management Assistant",
    description: "Ask about hotel policies, staff procedures, operational guidelines, and management protocols.",
    examples: [
      "What is the escalation procedure for guest complaints?",
      "How do I approve overtime for staff?",
      "What are the fire safety procedures?",
      "How do I handle a staffing shortage?"
    ]
  },
  admin: {
    title: "Admin Assistant",
    description: "Full access to all hotel policies, procedures, and operational knowledge base.",
    examples: [
      "What are the emergency evacuation procedures?",
      "How do I update the pricing structure?",
      "What's the vendor management process?",
      "How do I onboard a new employee?"
    ]
  }
};

export default function StaffChat({ user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL;
  
  const userRole = user?.role || "front_desk";
  const roleConfig = ROLE_CONTEXT[userRole] || ROLE_CONTEXT.front_desk;

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
      // For now, use a mock response - this will be connected to the PolicyAgent later
      // In Phase 2 (Staff AI), this will be: POST /api/staff/chat with RAG integration
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const assistantMessage = {
        role: "assistant",
        content: `**Staff AI Response** (Demo Mode)\n\nThis is a placeholder response for your question about: "${input}"\n\n*Note: The full Staff AI with RAG knowledge base integration will be implemented in the next phase. This assistant will answer questions based on hotel policies and procedures stored in the knowledge base.*`
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Staff chat error:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I apologize, but I encountered an error. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setInput(example);
  };

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
              {roleConfig.title}
            </h1>
            <p style={{ 
              color: "#94A3B8", 
              fontSize: "0.875rem",
              margin: 0
            }}>
              {roleConfig.description}
            </p>
          </div>
        </div>
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
                </p>
              </div>
              
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(2, 1fr)", 
                gap: 12,
                maxWidth: 600,
                width: "100%"
              }}>
                {roleConfig.examples.map((example, idx) => (
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
              <div
                key={idx}
                style={{
                  display: "flex",
                  gap: 12,
                  flexDirection: msg.role === "user" ? "row-reverse" : "row"
                }}
              >
                <div style={{
                  width: 32,
                  height: 32,
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
                    ? <User size={16} color="#0F172A" />
                    : <Bot size={16} color="#0F172A" />
                  }
                </div>
                <div style={{
                  maxWidth: "70%",
                  padding: "0.75rem 1rem",
                  borderRadius: 12,
                  background: msg.role === "user" 
                    ? "rgba(56,189,248,0.15)" 
                    : "rgba(167,139,250,0.1)",
                  border: msg.role === "user"
                    ? "1px solid rgba(56,189,248,0.3)"
                    : "1px solid rgba(167,139,250,0.2)",
                  color: "#F1F5F9",
                  fontSize: "0.875rem",
                  lineHeight: 1.6,
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
                <span style={{ color: "#94A3B8", fontSize: "0.875rem" }}>Thinking...</span>
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
