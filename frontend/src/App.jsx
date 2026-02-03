import { useState, useEffect } from "react";
import "./App.css";
import ChatBox from "./components/ChatBox.jsx";
import AdminPage from "./components/AdminPage.jsx";
import LandingPage from "./components/LandingPage.jsx";
import ChatWidget from "./components/ChatWidget.jsx";
import Login from "./components/Login.jsx";
import { BookingPage, GuidePage, WiFiPage, ReceptionPage } from "./components/ToolPages.jsx";

// Configure Global Fetch Interceptor to add Token
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  const [resource, config] = args;
  const token = localStorage.getItem('token');

  if (token && !resource.includes('/auth/')) {
    const headers = config?.headers || {};
    const newConfig = {
      ...config,
      headers: {
        ...headers,
        'Authorization': `Bearer ${token}`
      }
    };
    return originalFetch(resource, newConfig);
  }
  return originalFetch(resource, config);
};


function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [view, setView] = useState("home"); // "home" | "staff" | "admin" | ...

  useEffect(() => {
    // If we have a token but receive 401, we should probably logout.
    // For now, rely on manual logout.
  }, [token]);

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setView("home");
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setView("home");
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  // If admin view, render it separately without header/footer
  if (view === "admin") {
    return <AdminPage />;
  }

  return (
    <div className="app">
      {/* Top bar / branding */}
      <header className="app-header">
        <div className="brand">
          <span className="brand-title">Southern Horizons Hotel</span>
          <span className="brand-subtitle">
            AI Concierge & Staff Assistant
          </span>
        </div>

        <nav className="nav">
          <button
            className={view === "home" ? "nav-btn active" : "nav-btn"}
            onClick={() => setView("home")}
          >
            Hotel Website
          </button>

          <button
            className={view === "staff" ? "nav-btn active" : "nav-btn"}
            onClick={() => setView("staff")}
          >
            Staff Portal
          </button>

          <button
            className="nav-btn"
            onClick={handleLogout}
            style={{ marginLeft: "10px", border: "1px solid #ccc", background: "transparent" }}
          >
            Logout
          </button>

          <button
            className={view === "admin" ? "nav-btn active bg-admin" : "nav-btn bg-admin"}
            onClick={() => setView("admin")}
            style={{ marginLeft: "20px", border: "1px solid var(--accent-gold)" }}
          >
            ⚙️ Admin
          </button>
        </nav>
      </header>

      {/* Main content area */}
      <main className="app-main" style={{ maxWidth: view === "home" ? "100%" : "1000px", padding: view === "home" ? "0" : "3rem 2rem" }}>
        {view === "home" && (
          <LandingPage onNavigate={setView} />
        )}

        {view === "staff" && <StaffAssistantPage />}

        {/* Tool Pages */}
        {view === "book" && <BookingPage />}
        {view === "guide" && <GuidePage />}
        {view === "wifi" && <WiFiPage />}
        {view === "reception" && <ReceptionPage />}
      </main>

      {/* The Widget lives everywhere (except Admin ideally, but ok everywhere) 
          and handles navigation via onNavigate 
      */}
      <ChatWidget onNavigate={setView} />

      {view !== "home" && (
        <footer className="app-footer">
          <small>Demo project · SHHG AI Concierge & Staff Assistant</small>
        </footer>
      )}
    </div>
  );
}

// --------- Pages ---------

function HomePage() {
  return (
    <section className="page">
      <h1>Welcome to Southern Horizons Hotel</h1>
      <p>
        This is a demo hotel website that showcases an AI-powered Concierge &
        Staff Assistant.
      </p>
      <ul>
        <li>
          <strong>Guest Concierge</strong> helps guests with questions about
          their stay, facilities, and local attractions.
        </li>
        <li>
          <strong>Staff Assistant</strong> helps team members quickly find
          training, procedures, and service standards.
        </li>
      </ul>
      <p>Use the buttons at the top to switch between the Guest and Staff views.</p>
    </section>
  );
}

function GuestConciergePage() {
  return (
    <section className="page">
      <h1>Guest Concierge</h1>
      <p>
        Ask questions about check-in, check-out, facilities, or things to do
        nearby. This chat box sends your question to the Guest AI endpoint.
      </p>

      <ChatBox endpoint="/api/ask/guest" />
    </section>
  );
}

function StaffAssistantPage() {
  return (
    <section className="page">
      <h1>Staff Knowledge Assistant</h1>
      <p>
        Internal tool for staff. Ask about procedures, service standards, and
        training information. This chat box sends your question to the Staff AI
        endpoint.
      </p>

      <ChatBox endpoint="/api/ask/staff" />
    </section>
  );
}

export default App;