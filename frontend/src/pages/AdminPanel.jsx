import { useState, useEffect, useCallback, useRef } from "react";
import { BedDouble, CalendarCheck, CreditCard, RefreshCw, Search, FileText, Upload, Trash2, Database, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

const TABS = [
  { id: "rooms",        label: "Rooms",        icon: BedDouble },
  { id: "reservations", label: "Reservations", icon: CalendarCheck },
  { id: "payments",     label: "Payments",     icon: CreditCard },
  { id: "knowledge",    label: "Knowledge Base", icon: Database },
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
    if (tab === "knowledge") return; // Knowledge tab has its own data fetching
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

      {/* Content based on tab */}
      {tab === "knowledge" ? (
        <KnowledgeBasePanel />
      ) : (
        <>
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
        </>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`}</style>
    </div>
  );
}


// ============================================================
// Knowledge Base Panel
// ============================================================

function KnowledgeBasePanel() {
  const [files, setFiles] = useState({ guest: [], staff: [] });
  const [indexStatus, setIndexStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [uploadAudience, setUploadAudience] = useState("staff");
  const [message, setMessage] = useState(null);
  const fileInputRef = useRef(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const [filesData, statusData] = await Promise.all([
        apiCall("/admin/files"),
        apiCall("/admin/index/status")
      ]);
      setFiles(filesData || { guest: [], staff: [] });
      setIndexStatus(statusData);
    } catch (e) {
      console.error("Failed to fetch KB data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = [".pdf", ".txt", ".md"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowedTypes.includes(ext)) {
      setMessage({ type: "error", text: `Invalid file type. Allowed: ${allowedTypes.join(", ")}` });
      return;
    }

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("audience", uploadAudience);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/admin/upload", {
        method: "POST",
        headers: {
          "x-admin-key": ADMIN_KEY,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });
      const data = await res.json();
      
      if (res.ok) {
        setMessage({ type: "success", text: `Uploaded ${data.filename} - ${data.chunks_indexed || 0} chunks indexed` });
        fetchFiles();
      } else {
        setMessage({ type: "error", text: data.detail || "Upload failed" });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Upload failed: " + err.message });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (audience, filename) => {
    if (!confirm(`Delete ${filename}?`)) return;

    try {
      const res = await apiCall(`/admin/files/${audience}/${filename}`, { method: "DELETE" });
      if (res.status === "deleted") {
        setMessage({ type: "success", text: `Deleted ${filename}` });
        fetchFiles();
      } else {
        setMessage({ type: "error", text: res.detail || "Delete failed" });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Delete failed: " + err.message });
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    setMessage(null);
    try {
      const res = await apiCall("/admin/reindex", { method: "POST" });
      if (res.status === "success") {
        setMessage({ type: "success", text: `Reindexed ${res.files_processed || 0} files, ${res.chunks_added || 0} chunks` });
        fetchFiles();
      } else {
        setMessage({ type: "error", text: res.detail || "Reindex failed" });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Reindex failed: " + err.message });
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Status Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        <StatusCard
          title="Staff Documents"
          value={indexStatus?.staff_docs || 0}
          label="vectors indexed"
          color="#A78BFA"
        />
        <StatusCard
          title="Guest Documents"
          value={indexStatus?.guest_docs || 0}
          label="vectors indexed"
          color="#38BDF8"
        />
        <StatusCard
          title="Last Reindex"
          value={indexStatus?.last_reindex_time ? new Date(indexStatus.last_reindex_time).toLocaleString() : "Never"}
          label={indexStatus?.last_reindex_error ? "Error occurred" : ""}
          color={indexStatus?.last_reindex_error ? "#EF4444" : "#22C55E"}
          isText
        />
      </div>

      {/* Upload Section */}
      <div className="glass-card" style={{ padding: "1.5rem" }}>
        <h3 style={{ color: "#F1F5F9", fontSize: "1rem", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <Upload size={18} /> Upload Policy Documents
        </h3>

        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={uploadAudience}
            onChange={(e) => setUploadAudience(e.target.value)}
            style={{
              padding: "0.5rem 1rem",
              background: "#0F172A",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#F1F5F9",
              fontSize: "0.875rem"
            }}
          >
            <option value="staff">Staff Knowledge</option>
            <option value="guest">Guest Knowledge</option>
          </select>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md"
            onChange={handleUpload}
            style={{ display: "none" }}
            id="kb-file-input"
          />
          <label
            htmlFor="kb-file-input"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "0.5rem 1rem",
              background: uploading ? "rgba(56,189,248,0.3)" : "rgba(56,189,248,0.15)",
              border: "1px solid rgba(56,189,248,0.3)",
              borderRadius: 8,
              color: "#38BDF8",
              cursor: uploading ? "not-allowed" : "pointer",
              fontSize: "0.875rem"
            }}
          >
            {uploading ? <Loader2 size={16} className="spin" /> : <Upload size={16} />}
            {uploading ? "Uploading..." : "Choose File"}
          </label>

          <button
            onClick={handleReindex}
            disabled={reindexing}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "0.5rem 1rem",
              background: reindexing ? "rgba(167,139,250,0.3)" : "rgba(167,139,250,0.15)",
              border: "1px solid rgba(167,139,250,0.3)",
              borderRadius: 8,
              color: "#A78BFA",
              cursor: reindexing ? "not-allowed" : "pointer",
              fontSize: "0.875rem"
            }}
          >
            {reindexing ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}
            {reindexing ? "Reindexing..." : "Reindex All"}
          </button>
        </div>

        <p style={{ color: "#64748B", fontSize: "0.75rem", marginTop: 12 }}>
          Supported: PDF, TXT, MD files (max 10MB). Staff documents are used by the Staff AI Assistant.
        </p>

        {/* Message */}
        {message && (
          <div style={{
            marginTop: 12,
            padding: "0.75rem 1rem",
            background: message.type === "success" ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
            border: `1px solid ${message.type === "success" ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
            borderRadius: 8,
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: message.type === "success" ? "#22C55E" : "#EF4444",
            fontSize: "0.8rem"
          }}>
            {message.type === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            {message.text}
          </div>
        )}
      </div>

      {/* File Lists */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <FileList
          title="Staff Documents"
          files={files.staff || []}
          audience="staff"
          onDelete={handleDelete}
          loading={loading}
          color="#A78BFA"
        />
        <FileList
          title="Guest Documents"
          files={files.guest || []}
          audience="guest"
          onDelete={handleDelete}
          loading={loading}
          color="#38BDF8"
        />
      </div>
    </div>
  );
}

function StatusCard({ title, value, label, color, isText }) {
  return (
    <div className="glass-card" style={{ padding: "1.25rem" }}>
      <div style={{ color: "#64748B", fontSize: "0.75rem", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {title}
      </div>
      <div style={{ 
        color: color, 
        fontSize: isText ? "0.9rem" : "2rem", 
        fontWeight: 700, 
        fontFamily: isText ? "inherit" : "Chivo" 
      }}>
        {value}
      </div>
      {label && (
        <div style={{ color: "#64748B", fontSize: "0.7rem", marginTop: 4 }}>
          {label}
        </div>
      )}
    </div>
  );
}

function FileList({ title, files, audience, onDelete, loading, color }) {
  return (
    <div className="glass-card" style={{ padding: "1.25rem" }}>
      <h4 style={{ 
        color, 
        fontSize: "0.875rem", 
        marginBottom: 12, 
        display: "flex", 
        alignItems: "center", 
        gap: 8 
      }}>
        <FileText size={16} /> {title}
        <span style={{ 
          background: `${color}20`, 
          padding: "2px 8px", 
          borderRadius: 10, 
          fontSize: "0.7rem" 
        }}>
          {files.length}
        </span>
      </h4>

      {loading ? (
        <div style={{ textAlign: "center", padding: "2rem", color: "#64748B" }}>
          <Loader2 size={20} className="spin" />
        </div>
      ) : files.length === 0 ? (
        <div style={{ textAlign: "center", padding: "2rem", color: "#64748B", fontSize: "0.8rem" }}>
          No documents uploaded
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 300, overflowY: "auto" }}>
          {files.map((file, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.5rem 0.75rem",
                background: "rgba(0,0,0,0.2)",
                borderRadius: 8
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, overflow: "hidden" }}>
                <FileText size={14} color={color} />
                <span style={{ 
                  color: "#CBD5E1", 
                  fontSize: "0.8rem", 
                  overflow: "hidden", 
                  textOverflow: "ellipsis", 
                  whiteSpace: "nowrap" 
                }}>
                  {file}
                </span>
              </div>
              <button
                onClick={() => onDelete(audience, file)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "#64748B",
                  padding: 4,
                  borderRadius: 4
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = "#EF4444"}
                onMouseLeave={(e) => e.currentTarget.style.color = "#64748B"}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ============================================================
// Table Components
// ============================================================

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
