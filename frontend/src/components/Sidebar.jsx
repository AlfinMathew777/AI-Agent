import { 
  Bot, 
  LayoutDashboard, 
  MessageSquare, 
  Settings, 
  BarChart3, 
  ClipboardList, 
  ChevronLeft, 
  ChevronRight, 
  LogOut, 
  User,
  Users,
  BrainCircuit,
  Headphones
} from "lucide-react";

// Navigation items with role-based visibility
const NAV_ITEMS = [
  { 
    id: "a2a", 
    label: "A2A Dashboard", 
    icon: LayoutDashboard, 
    badge: "LIVE",
    allowedRoles: ["admin", "manager", "front_desk"]
  },
  { 
    id: "chat", 
    label: "Guest Chat", 
    icon: MessageSquare,
    allowedRoles: ["admin", "manager", "front_desk", "guest"]
  },
  { 
    id: "staff_chat", 
    label: "Staff Assistant", 
    icon: Headphones,
    allowedRoles: ["admin", "manager", "front_desk", "housekeeping", "restaurant"]
  },
  { 
    id: "management", 
    label: "Intelligence", 
    icon: BrainCircuit,
    badge: "AI",
    allowedRoles: ["admin", "manager"]
  },
  { 
    id: "admin", 
    label: "Admin Panel", 
    icon: Settings,
    allowedRoles: ["admin"]
  },
  { 
    id: "operations", 
    label: "Operations", 
    icon: ClipboardList,
    allowedRoles: ["admin", "manager", "front_desk", "housekeeping", "restaurant"]
  },
  { 
    id: "analytics", 
    label: "Analytics", 
    icon: BarChart3,
    allowedRoles: ["admin", "manager"]
  },
];

// Role display names and colors
const ROLE_CONFIG = {
  admin: { label: "Administrator", color: "#EF4444", bgColor: "rgba(239,68,68,0.15)" },
  manager: { label: "Manager", color: "#F59E0B", bgColor: "rgba(245,158,11,0.15)" },
  front_desk: { label: "Front Desk", color: "#38BDF8", bgColor: "rgba(56,189,248,0.15)" },
  housekeeping: { label: "Housekeeping", color: "#22C55E", bgColor: "rgba(34,197,94,0.15)" },
  restaurant: { label: "Restaurant", color: "#A78BFA", bgColor: "rgba(167,139,250,0.15)" },
  guest: { label: "Guest", color: "#94A3B8", bgColor: "rgba(148,163,184,0.15)" },
};

export default function Sidebar({ view, setView, user, open, setOpen, VIEWS, onLogout }) {
  const userRole = user?.role || "guest";
  const roleConfig = ROLE_CONFIG[userRole] || ROLE_CONFIG.guest;
  
  // Filter nav items based on user role
  const visibleNavItems = NAV_ITEMS.filter(item => 
    item.allowedRoles.includes(userRole)
  );

  return (
    <aside
      data-testid="sidebar"
      style={{
        width: open ? 240 : 68,
        background: "rgba(15,23,42,0.95)",
        borderRight: "1px solid #1E293B",
        display: "flex",
        flexDirection: "column",
        transition: "width 0.25s ease",
        overflow: "hidden",
        position: "relative",
        zIndex: 40,
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: "1.25rem 1rem", borderBottom: "1px solid #1E293B", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: "linear-gradient(135deg,#0EA5E9,#38BDF8)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Bot size={20} color="#0F172A" strokeWidth={2} />
        </div>
        {open && (
          <div>
            <div style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "0.9rem", color: "#F1F5F9", letterSpacing: "-0.02em" }}>A2A Nexus</div>
            <div style={{ fontSize: "0.65rem", color: "#38BDF8", letterSpacing: "0.08em", textTransform: "uppercase" }}>Hotel AI</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "0.75rem 0.5rem", display: "flex", flexDirection: "column", gap: 2 }}>
        {visibleNavItems.map(({ id, label, icon: Icon, badge }) => {
          const active = view === id;
          return (
            <button
              key={id}
              data-testid={`nav-${id}`}
              onClick={() => setView(id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "0.6rem 0.75rem",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                background: active ? "rgba(56,189,248,0.12)" : "transparent",
                color: active ? "#38BDF8" : "#94A3B8",
                borderLeft: active ? "2px solid #38BDF8" : "2px solid transparent",
                fontSize: "0.875rem",
                fontWeight: active ? 600 : 400,
                width: "100%",
                textAlign: "left",
                transition: "background-color 0.15s ease, color 0.15s ease",
                whiteSpace: "nowrap",
                overflow: "hidden",
              }}
              onMouseEnter={e => { if (!active) { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.color = "#F1F5F9"; } }}
              onMouseLeave={e => { if (!active) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#94A3B8"; } }}
            >
              <Icon size={18} strokeWidth={1.5} style={{ flexShrink: 0 }} />
              {open && (
                <span style={{ flex: 1 }}>{label}</span>
              )}
              {open && badge && (
                <span style={{ 
                  fontSize: "0.6rem", 
                  padding: "1px 5px", 
                  borderRadius: 4, 
                  background: badge === "AI" ? "rgba(167,139,250,0.15)" : "rgba(34,197,94,0.15)", 
                  color: badge === "AI" ? "#A78BFA" : "#22C55E", 
                  border: badge === "AI" ? "1px solid rgba(167,139,250,0.3)" : "1px solid rgba(34,197,94,0.3)", 
                  letterSpacing: "0.05em" 
                }}>
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* User section */}
      {user && (
        <div style={{ padding: "0.75rem 0.5rem", borderTop: "1px solid #1E293B" }}>
          {open ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0.5rem 0.75rem", borderRadius: 8, background: "rgba(255,255,255,0.03)" }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", background: roleConfig.bgColor, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <User size={14} color={roleConfig.color} />
              </div>
              <div style={{ flex: 1, overflow: "hidden" }}>
                <div style={{ fontSize: "0.75rem", color: "#F1F5F9", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.full_name || user.email}
                </div>
                <div style={{ 
                  fontSize: "0.6rem", 
                  color: roleConfig.color, 
                  fontWeight: 500,
                  letterSpacing: "0.03em"
                }}>
                  {roleConfig.label}
                </div>
              </div>
              <button 
                data-testid="sidebar-logout" 
                onClick={onLogout} 
                style={{ background: "none", border: "none", cursor: "pointer", color: "#64748B", padding: 4, borderRadius: 4, transition: "color 0.15s ease" }} 
                onMouseEnter={e => e.currentTarget.style.color = "#EF4444"} 
                onMouseLeave={e => e.currentTarget.style.color = "#64748B"}
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button 
              data-testid="sidebar-logout-compact" 
              onClick={onLogout} 
              style={{ width: "100%", padding: "0.5rem", background: "none", border: "none", cursor: "pointer", color: "#64748B", borderRadius: 8 }}
            >
              <LogOut size={18} strokeWidth={1.5} />
            </button>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <button
        data-testid="sidebar-toggle"
        onClick={() => setOpen(!open)}
        style={{
          position: "absolute",
          bottom: user ? 72 : 12,
          right: -12,
          width: 24,
          height: 24,
          borderRadius: "50%",
          background: "#1E293B",
          border: "1px solid #334155",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          color: "#94A3B8",
          zIndex: 50,
        }}
      >
        {open ? <ChevronLeft size={13} /> : <ChevronRight size={13} />}
      </button>
    </aside>
  );
}
