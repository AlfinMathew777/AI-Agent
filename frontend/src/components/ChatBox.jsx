
import { useState, useRef, useEffect } from "react";
import "./ChatBox.css"; // We will create this specific CSS file

export default function ChatBox({ endpoint, audience = "guest" }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Hello! How can I assist you today?" }
  ]);
  const [pendingAction, setPendingAction] = useState(null); // { action_id, message, proposed_action }

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pendingAction]);

  // Helper to make requests (handles proxy fallback)
  async function makeRequest(url, body, signal) {
    try {
      return await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: signal,
      });
    } catch (proxyError) {
      console.warn("Proxy connection failed, trying direct connection...", proxyError);
      // Fallback: Try hitting port 8002 directly
      // Only if url starts with /api
      if (url.startsWith('/api')) {
        const directUrl = "http://localhost:8002" + url.replace(/^\/api/, '');
        return await fetch(directUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: signal,
        });
      }
      throw proxyError;
    }
  }

  async function sendQuestion(e) {
    if (e) e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    const userQ = question;
    setQuestion("");

    // Add user message
    setMessages((prev) => [...prev, { sender: "you", text: userQ }]);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const payload = {
        audience: audience,
        question: userQ
      };

      const response = await makeRequest(endpoint, payload, controller.signal);
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status} ${response.statusText}`);
      }

      const result = await response.json();

      // Handle Confirmation
      if (result.status === "needs_confirmation") {
        setPendingAction(result);
        setMessages((prev) => [
          ...prev,
          { sender: "ai", text: result.message } // "I can book... confirm?"
        ]);
      } else {
        // Standard Answer
        setMessages((prev) => [
          ...prev,
          { sender: "ai", text: result.answer || result.message || JSON.stringify(result) }
        ]);
      }

    } catch (err) {
      console.error("Chat Error:", err);
      let errorMessage = "Sorry, I'm having trouble connecting. Please try again.";
      if (err.name === "AbortError") {
        errorMessage = "Request timed out.";
      }
      setMessages((prev) => [...prev, { sender: "ai", text: `⚠️ ${errorMessage}` }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm(isConfirmed) {
    if (!pendingAction) return;

    setLoading(true);
    // Remove the pending action UI state immediately (we will show result msg)
    const currentActionId = pendingAction.action_id;
    setPendingAction(null);

    try {
      const controller = new AbortController();
      const targetEndpoint = "/api/ask/agent/confirm";

      const payload = {
        action_id: currentActionId,
        confirm: isConfirmed
      };

      const response = await makeRequest(targetEndpoint, payload, controller.signal);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const result = await response.json();

      // Add result message
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: result.answer || "Action processed." }
      ]);

    } catch (err) {
      console.error("Confirm Error:", err);
      setMessages((prev) => [...prev, { sender: "ai", text: `⚠️ Error confirming action: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message-row ${msg.sender}`}>
            <div className={`message-bubble ${msg.sender}`}>
              {msg.sender === "ai" && <div className="avatar">AI</div>}
              <div className="message-content">
                {msg.text.split('\n').map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
            </div>
          </div>
        ))}

        {/* Pending Action Verification UI */}
        {pendingAction && (
          <div className="message-row ai">
            <div className="message-bubble ai action-request">
              <div className="action-details">
                <strong>Confirmation Required</strong>
                <p>Action: {pendingAction.proposed_action?.tool}</p>
                <div className="action-buttons">
                  <button className="confirm-btn" onClick={() => handleConfirm(true)}>
                    ✅ Yes, Proceed
                  </button>
                  <button className="cancel-btn" onClick={() => handleConfirm(false)}>
                    ❌ Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="message-row ai">
            <div className="message-bubble ai thinking">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-area" onSubmit={sendQuestion}>
        <input
          placeholder="Type your request here..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading || !!pendingAction} // Disable input while waiting for confirm
        />
        <button type="submit" disabled={loading || !question.trim() || !!pendingAction}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
      {/* 4. Confirmation Hint */}
      {!!pendingAction && (
        <div className="pending-hint">
          <small>⚠️ Please confirm or cancel the action above to continue.</small>
        </div>
      )}
    </div>
  );
}
