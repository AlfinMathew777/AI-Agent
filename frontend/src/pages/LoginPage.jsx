import { useState } from "react";
import { ArrowLeft, Bot, Eye, EyeOff, AlertCircle } from "lucide-react";

export default function LoginPage({ onLogin, onBack }) {
  const [email, setEmail] = useState("admin@hotel.com");
  const [password, setPassword] = useState("admin123");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("username", email);
      fd.append("password", password);
      const res = await fetch("/api/auth/login", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.error || "Login failed");
      localStorage.setItem("token", data.access_token);
      onLogin({ email, role: data.role || "admin", token: data.access_token });
    } catch (err) {
      setError(err.message || "Unable to connect. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0F172A", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
      {/* Back */}
      <button
        data-testid="login-back"
        onClick={onBack}
        style={{ position: "absolute", top: 24, left: 24, background: "none", border: "none", cursor: "pointer", color: "#64748B", display: "flex", alignItems: "center", gap: 6, fontSize: "0.875rem" }}
      >
        <ArrowLeft size={16} /> Back
      </button>

      {/* Card */}
      <div className="glass-card" style={{ width: "100%", maxWidth: 400, padding: "2.5rem" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1rem" }}>
            <Bot size={28} color="#0F172A" />
          </div>
          <h1 style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1.5rem", color: "#F1F5F9" }}>A2A Nexus</h1>
          <p style={{ fontSize: "0.8rem", color: "#64748B", marginTop: 4 }}>Staff & Admin Login</p>
        </div>

        <form onSubmit={handleLogin} data-testid="login-form">
          {error && (
            <div data-testid="login-error" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "0.75rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 8, fontSize: "0.8rem", color: "#FCA5A5" }}>
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.75rem", color: "#94A3B8", marginBottom: 6, fontWeight: 500 }}>Email</label>
            <input
              data-testid="login-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={{ width: "100%", padding: "0.625rem 0.875rem", background: "rgba(0,0,0,0.3)", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.875rem", outline: "none", transition: "border-color 0.15s ease" }}
              onFocus={e => e.target.style.borderColor = "#38BDF8"}
              onBlur={e => e.target.style.borderColor = "#334155"}
            />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", fontSize: "0.75rem", color: "#94A3B8", marginBottom: 6, fontWeight: 500 }}>Password</label>
            <div style={{ position: "relative" }}>
              <input
                data-testid="login-password"
                type={showPw ? "text" : "password"}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                style={{ width: "100%", padding: "0.625rem 2.5rem 0.625rem 0.875rem", background: "rgba(0,0,0,0.3)", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.875rem", outline: "none", transition: "border-color 0.15s ease" }}
                onFocus={e => e.target.style.borderColor = "#38BDF8"}
                onBlur={e => e.target.style.borderColor = "#334155"}
              />
              <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#64748B" }}>
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            data-testid="login-submit"
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.75rem",
              background: loading ? "rgba(56,189,248,0.5)" : "rgba(56,189,248,0.9)",
              border: "none",
              borderRadius: 8,
              color: "#0F172A",
              fontWeight: 700,
              fontSize: "0.9rem",
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 0 16px rgba(56,189,248,0.3)",
              transition: "background-color 0.15s ease",
            }}
          >
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.75rem", color: "#64748B" }}>
          Default: admin@hotel.com / admin123
        </p>
      </div>
    </div>
  );
}
