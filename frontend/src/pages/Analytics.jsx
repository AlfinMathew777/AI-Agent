import { useState, useEffect } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, BarChart2, Target, Zap } from "lucide-react";

const COLORS = ["#38BDF8", "#22C55E", "#F59E0B", "#A78BFA", "#FB923C", "#60A5FA", "#34D399"];

export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [revenue, setRevenue] = useState([]);
  const [agents, setAgents] = useState([]);
  const [occupancy, setOccupancy] = useState([]);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    Promise.all([
      fetch("/api/analytics/summary").then(r => r.json()).catch(() => ({})),
      fetch(`/api/analytics/revenue?days=${period}`).then(r => r.json()).catch(() => ({ data: [] })),
      fetch("/api/analytics/agents").then(r => r.json()).catch(() => ({ agents: [] })),
      fetch("/api/analytics/occupancy").then(r => r.json()).catch(() => ({ data: [] })),
    ]).then(([s, rv, ag, oc]) => {
      setSummary(s);
      setRevenue(rv.data || []);
      setAgents(ag.agents || []);
      setOccupancy(oc.data || []);
    });
  }, [period]);

  const tooltipStyle = { background: "#1E293B", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.75rem" };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
        {summary && [
          { label: "Total Revenue",      value: `$${(summary.total_revenue || 0).toLocaleString()}`,  icon: TrendingUp, color: "#22C55E" },
          { label: "Total Bookings",     value: summary.total_bookings || 0,                          icon: BarChart2,  color: "#38BDF8" },
          { label: "Occupancy Rate",     value: `${summary.occupancy_rate || 0}%`,                   icon: Target,     color: "#F59E0B" },
          { label: "Agent Success Rate", value: `${summary.agent_success_rate || 94.2}%`,            icon: Zap,        color: "#A78BFA" },
        ].map(k => (
          <div key={k.label} className="glass-card" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <k.icon size={18} color={k.color} strokeWidth={1.5} />
            </div>
            <div style={{ fontFamily: "Chivo", fontWeight: 700, fontSize: "1.75rem", color: k.color }}>{k.value}</div>
            <div style={{ fontSize: "0.7rem", color: "#64748B", marginTop: 2 }}>{k.label}</div>
          </div>
        ))}
      </div>

      {/* Revenue Chart */}
      <div className="glass-card" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <h3 style={{ fontFamily: "Chivo", fontWeight: 600, fontSize: "0.9rem", color: "#E2E8F0" }}>Revenue Trend</h3>
          <div style={{ display: "flex", gap: 6 }}>
            {[7, 14, 30].map(d => (
              <button key={d} data-testid={`period-${d}`} onClick={() => setPeriod(d)} style={{ padding: "3px 10px", borderRadius: 6, border: "none", cursor: "pointer", background: period === d ? "rgba(56,189,248,0.15)" : "rgba(255,255,255,0.04)", color: period === d ? "#38BDF8" : "#64748B", fontSize: "0.75rem", fontWeight: period === d ? 600 : 400 }}>
                {d}d
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={revenue} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
            <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 10, fill: "#64748B" }} axisLine={{ stroke: "#334155" }} />
            <YAxis tick={{ fontSize: 10, fill: "#64748B" }} axisLine={{ stroke: "#334155" }} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
            <Tooltip contentStyle={tooltipStyle} formatter={v => [`$${v.toLocaleString()}`, "Revenue"]} />
            <Line type="monotone" dataKey="revenue" stroke="#38BDF8" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#38BDF8" }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom: Bookings Bar + Occupancy Pie + Agent Performance */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        {/* Bookings */}
        <div className="glass-card" style={{ padding: "1.25rem", gridColumn: "span 1" }}>
          <h3 style={{ fontFamily: "Chivo", fontWeight: 600, fontSize: "0.85rem", color: "#E2E8F0", marginBottom: "1rem" }}>Bookings / Day</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={revenue.slice(-14)} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="2 2" stroke="#1E293B" />
              <XAxis dataKey="date" tickFormatter={d => d.slice(8)} tick={{ fontSize: 9, fill: "#64748B" }} axisLine={{ stroke: "#334155" }} />
              <YAxis tick={{ fontSize: 9, fill: "#64748B" }} axisLine={{ stroke: "#334155" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="bookings" fill="#38BDF8" fillOpacity={0.8} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Occupancy Pie */}
        <div className="glass-card" style={{ padding: "1.25rem" }}>
          <h3 style={{ fontFamily: "Chivo", fontWeight: 600, fontSize: "0.85rem", color: "#E2E8F0", marginBottom: "1rem" }}>Occupancy by Type</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={occupancy} dataKey="occupied" nameKey="type" cx="50%" cy="50%" outerRadius={65} label={({ type, percent }) => `${type} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {occupancy.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Performance */}
        <div className="glass-card" style={{ padding: "1.25rem" }}>
          <h3 style={{ fontFamily: "Chivo", fontWeight: 600, fontSize: "0.85rem", color: "#E2E8F0", marginBottom: "1rem" }}>Agent Performance</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {agents.slice(0, 5).map((ag, i) => (
              <div key={ag.name} data-testid={`agent-perf-${i}`}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3, fontSize: "0.7rem" }}>
                  <span style={{ color: "#94A3B8" }}>{ag.name.replace(" Agent", "")}</span>
                  <span style={{ color: COLORS[i], fontFamily: "JetBrains Mono, monospace" }}>{ag.success_rate}%</span>
                </div>
                <div style={{ height: 5, background: "rgba(255,255,255,0.05)", borderRadius: 3, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${ag.success_rate}%`, background: COLORS[i], borderRadius: 3, transition: "width 0.8s ease" }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
