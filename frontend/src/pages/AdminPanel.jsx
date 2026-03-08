import { useState, useEffect, useCallback } from "react";
import { BedDouble, CalendarCheck, CreditCard, RefreshCw, Plus, Search } from "lucide-react";

const TABS = [
  { id: "rooms",        label: "Rooms",        icon: BedDouble },
  { id: "reservations", label: "Reservations", icon: CalendarCheck },
  { id: "payments",     label: "Payments",     icon: CreditCard },
];

const ADMIN_KEY = "shhg_admin_secure_key_2024";

function apiCall(path, options = {}) {
  const token = localStorage.getItem("token");
  return fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-admin-key": ADMIN_KEY,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  }).then(r => r.json());
}

export default function AdminPanel() {
  const [tab, setTab] = useState("rooms");
  const [rooms, setRooms] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === "rooms") {
        const d = await apiCall("/admin/rooms");
        setRooms(Array.isArray(d) ? d : d?.rooms || []);
      } else if (tab === "reservations") {
        const d = await apiCall("/admin/reservations");
        setReservations(Array.isArray(d) ? d : d?.reservations || []);
      } else if (tab === "payments") {
        const d = await apiCall("/admin/payments");
        setPayments(Array.isArray(d) ? d : d?.payments || d?.receipts || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, background: "rgba(0,0,0,0.2)", borderRadius: 10, padding: 4, width: "fit-content" }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            data-testid={`admin-tab-${id}`}
            onClick={() => setTab(id)}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "0.5rem 1rem", borderRadius: 7, border: "none", cursor: "pointer",
              background: tab === id ? "rgba(56,189,248,0.12)" : "transparent",
              color: tab === id ? "#38BDF8" : "#94A3B8",
              fontWeight: tab === id ? 600 : 400,
              fontSize: "0.875rem",
              borderBottom: tab === id ? "2px solid #38BDF8" : "2px solid transparent",
            }}
          >
            <Icon size={15} strokeWidth={1.5} /> {label}
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, maxWidth: 340 }}>
          <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#64748B" }} />
          <input
            data-testid="admin-search"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={`Search ${tab}...`}
            style={{ width: "100%", paddingLeft: 32, paddingRight: 12, paddingTop: "0.5rem", paddingBottom: "0.5rem", background: "rgba(0,0,0,0.2)", border: "1px solid #334155", borderRadius: 8, color: "#F1F5F9", fontSize: "0.8rem", outline: "none" }}
          />
        </div>
        <button data-testid="admin-refresh" onClick={fetchData} style={{ display: "flex", alignItems: "center", gap: 6, padding: "0.5rem 0.875rem", background: "rgba(255,255,255,0.05)", border: "1px solid #334155", borderRadius: 8, color: "#94A3B8", cursor: "pointer", fontSize: "0.8rem" }}>
          <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ overflow: "hidden" }}>
        {tab === "rooms" && <RoomsTable data={rooms} search={search} loading={loading} />}
        {tab === "reservations" && <ReservationsTable data={reservations} search={search} loading={loading} />}
        {tab === "payments" && <PaymentsTable data={payments} search={search} loading={loading} />}
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`}</style>
    </div>
  );
}

function TableWrap({ headers, children, loading }) {
  return (
    <div style={{ overflowX: "auto" }}>
      {loading && <div style={{ height: 3, background: "linear-gradient(90deg, transparent, #38BDF8, transparent)", animation: "slide 1.5s ease-in-out infinite" }} />}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #1E293B" }}>
            {headers.map(h => <th key={h} style={{ padding: "0.875rem 1rem", color: "#64748B", fontWeight: 500, textAlign: "left", whiteSpace: "nowrap", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>)}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
      <style>{`@keyframes slide { from { transform: translateX(-100%); } to { transform: translateX(400%); } }`}</style>
    </div>
  );
}

function Row({ cells, testId }) {
  return (
    <tr data-testid={testId} style={{ borderBottom: "1px solid rgba(30,41,59,0.8)" }} onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.02)"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
      {cells.map((c, i) => <td key={i} style={{ padding: "0.75rem 1rem", color: "#CBD5E1", verticalAlign: "middle" }}>{c}</td>)}
    </tr>
  );
}

function Badge({ value, colorMap }) {
  const color = colorMap?.[value?.toLowerCase()] || "#94A3B8";
  return <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: "0.68rem", fontWeight: 600, background: `${color}18`, color, border: `1px solid ${color}30`, textTransform: "uppercase", letterSpacing: "0.04em" }}>{value || "—"}</span>;
}

function RoomsTable({ data, search, loading }) {
  const filtered = data.filter(r => !search || JSON.stringify(r).toLowerCase().includes(search.toLowerCase()));
  return (
    <TableWrap headers={["#", "Room", "Type", "Floor", "Capacity", "Price/Night", "Status"]} loading={loading}>
      {filtered.length === 0 ? (
        <tr><td colSpan={7} style={{ textAlign: "center", padding: "3rem", color: "#334155" }}>No rooms found</td></tr>
      ) : filtered.map((r, i) => (
        <Row key={r.id || i} testId={`room-row-${i}`} cells={[
          i + 1,
          <b style={{ color: "#F1F5F9" }}>{r.room_number || r.number || "—"}</b>,
          r.room_type || r.type || "—",
          r.floor || "—",
          r.capacity || "—",
          r.price_per_night ? `$${r.price_per_night}` : "—",
          <Badge value={r.is_available ? "Available" : "Occupied"} colorMap={{ available: "#22C55E", occupied: "#F59E0B" }} />,
        ]} />
      ))}
    </TableWrap>
  );
}

function ReservationsTable({ data, search, loading }) {
  const filtered = data.filter(r => !search || JSON.stringify(r).toLowerCase().includes(search.toLowerCase()));
  return (
    <TableWrap headers={["#", "Guest", "Email", "Room", "Check In", "Check Out", "Total", "Status"]} loading={loading}>
      {filtered.length === 0 ? (
        <tr><td colSpan={8} style={{ textAlign: "center", padding: "3rem", color: "#334155" }}>No reservations found</td></tr>
      ) : filtered.map((r, i) => (
        <Row key={r.id || i} testId={`res-row-${i}`} cells={[
          i + 1,
          <b style={{ color: "#F1F5F9" }}>{r.guest_name || "—"}</b>,
          <span style={{ color: "#64748B", fontSize: "0.75rem" }}>{r.guest_email || "—"}</span>,
          r.room_id || r.room_number || "—",
          r.check_in_date || r.check_in || "—",
          r.check_out_date || r.check_out || "—",
          r.total_amount ? `$${parseFloat(r.total_amount).toFixed(2)}` : "—",
          <Badge value={r.status || "confirmed"} colorMap={{ confirmed: "#22C55E", cancelled: "#EF4444", pending: "#F59E0B" }} />,
        ]} />
      ))}
    </TableWrap>
  );
}

function PaymentsTable({ data, search, loading }) {
  const filtered = data.filter(r => !search || JSON.stringify(r).toLowerCase().includes(search.toLowerCase()));
  return (
    <TableWrap headers={["#", "Ref", "Amount", "Method", "Status", "Date"]} loading={loading}>
      {filtered.length === 0 ? (
        <tr><td colSpan={6} style={{ textAlign: "center", padding: "3rem", color: "#334155" }}>No payments found</td></tr>
      ) : filtered.map((r, i) => (
        <Row key={r.id || i} testId={`pay-row-${i}`} cells={[
          i + 1,
          <b style={{ color: "#F1F5F9", fontFamily: "JetBrains Mono, monospace", fontSize: "0.75rem" }}>{r.confirmation_code || r.id?.slice(0,8) || "—"}</b>,
          r.amount ? `$${(parseFloat(r.amount) / 100).toFixed(2)}` : r.total_amount ? `$${parseFloat(r.total_amount).toFixed(2)}` : "—",
          r.payment_method || r.method || "card",
          <Badge value={r.status || "paid"} colorMap={{ paid: "#22C55E", pending: "#F59E0B", failed: "#EF4444" }} />,
          r.created_at ? new Date(r.created_at).toLocaleDateString() : "—",
        ]} />
      ))}
    </TableWrap>
  );
}
