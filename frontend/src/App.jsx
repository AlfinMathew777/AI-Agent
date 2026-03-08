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
import StaffChat from "./pages/StaffChat";
import ManagementDashboard from "./pages/ManagementDashboard";

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
  STAFF_CHAT: "staff_chat",
  MANAGEMENT: "management",
};

// Role-based default landing page
const getDefaultViewForRole = (role) => {
  switch (role) {
    case "admin":
      return VIEWS.A2A;
    case "manager":
      return VIEWS.MANAGEMENT;
    case "front_desk":
      return VIEWS.OPERATIONS;
    case "housekeeping":
      return VIEWS.OPERATIONS;
    case "restaurant":
      return VIEWS.OPERATIONS;
    case "guest":
      return VIEWS.CHAT;
    default:
      return VIEWS.A2A;
  }
};

// Check if user can access a specific view
const canAccessView = (role, view) => {
  const permissions = {
    admin: [VIEWS.A2A, VIEWS.CHAT, VIEWS.ADMIN, VIEWS.OPERATIONS, VIEWS.ANALYTICS, VIEWS.STAFF_CHAT, VIEWS.MANAGEMENT],
    manager: [VIEWS.A2A, VIEWS.CHAT, VIEWS.OPERATIONS, VIEWS.ANALYTICS, VIEWS.STAFF_CHAT, VIEWS.MANAGEMENT],
    front_desk: [VIEWS.A2A, VIEWS.CHAT, VIEWS.OPERATIONS, VIEWS.STAFF_CHAT],
    housekeeping: [VIEWS.OPERATIONS, VIEWS.STAFF_CHAT],
    restaurant: [VIEWS.OPERATIONS, VIEWS.STAFF_CHAT],
    guest: [VIEWS.CHAT],
  };
  return permissions[role]?.includes(view) ?? false;
};

export default function App() {
  const [view, setView] = useState(VIEWS.LANDING);
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("user");
    if (saved) {
      try { 
        const userData = JSON.parse(saved);
        setUser(userData);
        // Set default view based on role
        setView(getDefaultViewForRole(userData.role));
      } catch (_) {}
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("token", userData.access_token);
    // Navigate to role-appropriate default page
    setView(getDefaultViewForRole(userData.role));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setView(VIEWS.LANDING);
  };

  // Handle view changes with permission check
  const handleSetView = (newView) => {
    if (!user) {
      setView(newView);
      return;
    }
    // Check if user can access the requested view
    if (canAccessView(user.role, newView)) {
      setView(newView);
    } else {
      // Redirect to their default view if they try to access unauthorized page
      setView(getDefaultViewForRole(user.role));
    }
  };

  // Landing page has its own layout (no sidebar)
  if (view === VIEWS.LANDING) {
    return (
      <div className="App">
        <LandingPage
          onNavigate={handleSetView}
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
        setView={handleSetView}
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
          {view === VIEWS.OPERATIONS  && <OperationsDashboard user={user} />}
          {view === VIEWS.ANALYTICS   && <Analytics />}
          {view === VIEWS.STAFF_CHAT  && <StaffChat user={user} />}
          {view === VIEWS.MANAGEMENT  && <ManagementDashboard user={user} />}
        </div>
      </div>
    </div>
  );
}
