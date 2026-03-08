import { useState, useEffect } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import LandingPage from "./pages/LandingPage";
import GuestChat from "./pages/GuestChat";
import A2ADashboard from "./pages/A2ADashboard";
import AdminPanel from "./pages/AdminPanel";
import OperationsDashboard from "./pages/OperationsDashboard";
import Analytics from "./pages/Analytics";
import LoginPage from "./pages/LoginPage";

// Global fetch interceptor for auth token
const _originalFetch = window.fetch;
window.fetch = async (...args) => {
  const [resource, config] = args;
  const token = localStorage.getItem("token");
  if (token && typeof resource === "string" && !resource.includes("/auth/")) {
    return _originalFetch(resource, {
      ...config,
      headers: { ...(config?.headers || {}), Authorization: `Bearer ${token}` },
    });
  }
  return _originalFetch(resource, config);
};

export const VIEWS = {
  LANDING: "landing",
  CHAT: "chat",
  A2A: "a2a",
  ADMIN: "admin",
  OPERATIONS: "operations",
  ANALYTICS: "analytics",
  LOGIN: "login",
};

export default function App() {
  const [view, setView] = useState(VIEWS.LANDING);
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("user");
    if (saved) {
      try { setUser(JSON.parse(saved)); } catch (_) {}
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
    setView(VIEWS.A2A);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setView(VIEWS.LANDING);
  };

  // Landing page has its own layout (no sidebar)
  if (view === VIEWS.LANDING) {
    return (
      <div className="App">
        <LandingPage
          onNavigate={setView}
          onLogin={() => setView(VIEWS.LOGIN)}
          VIEWS={VIEWS}
        />
      </div>
    );
  }

  if (view === VIEWS.LOGIN) {
    return (
      <div className="App">
        <LoginPage onLogin={handleLogin} onBack={() => setView(VIEWS.LANDING)} />
      </div>
    );
  }

  // Guest chat is full-screen (no sidebar needed for guests)
  if (view === VIEWS.CHAT && !user) {
    return (
      <div className="App">
        <GuestChat onBack={() => setView(VIEWS.LANDING)} />
      </div>
    );
  }

  // Dashboard layout with sidebar
  return (
    <div className="App app-layout">
      <Sidebar
        view={view}
        setView={setView}
        user={user}
        open={sidebarOpen}
        setOpen={setSidebarOpen}
        VIEWS={VIEWS}
        onLogout={handleLogout}
      />
      <div className="app-main">
        <TopBar
          user={user}
          view={view}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          onLogout={handleLogout}
        />
        <div className="app-content" data-testid="app-content">
          {view === VIEWS.A2A         && <A2ADashboard />}
          {view === VIEWS.CHAT        && <GuestChat embedded />}
          {view === VIEWS.ADMIN       && <AdminPanel />}
          {view === VIEWS.OPERATIONS  && <OperationsDashboard />}
          {view === VIEWS.ANALYTICS   && <Analytics />}
        </div>
      </div>
    </div>
  );
}
