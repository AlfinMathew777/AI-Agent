
import { useState, useEffect } from "react";
import "./AdminPage.css";

const API_BASE = "http://127.0.0.1:8002";

export default function AdminPage() {
    // --- State ---
    // Auth
    const [adminKey, setAdminKey] = useState(() => localStorage.getItem("adminKey") || "");

    // Tabs
    const [activeTab, setActiveTab] = useState("analytics"); // analytics | bookings | tools | files

    // Data State
    const [analytics, setAnalytics] = useState(null);
    const [files, setFiles] = useState({ guest: [], staff: [] });
    const [bookingsData, setBookingsData] = useState({ bookings: [], summary: {} });
    const [toolStats, setToolStats] = useState(null);
    const [idxStatus, setIdxStatus] = useState(null);

    // UI State
    const [statusMsg, setStatusMsg] = useState("");
    const [uploading, setUploading] = useState(false);

    // Filters
    const [filters, setFilters] = useState({
        date: "",
        room_type: "",
        status: "",
        days: 7,
        limit: 20
    });

    // Pagination
    const [page, setPage] = useState(0);
    const LIMIT = 20;

    // --- Effects ---
    useEffect(() => {
        // Persist Key
        localStorage.setItem("adminKey", adminKey);
    }, [adminKey]);

    useEffect(() => {
        if (!adminKey) return;

        // Reset page on tab switch
        setPage(0);
        setStatusMsg("");

        if (activeTab === "analytics") fetchAnalytics();
        if (activeTab === "bookings") fetchBookings();
        if (activeTab === "tools") fetchToolStats();
        if (activeTab === "files") {
            fetchFiles();
            fetchIndexStatus();
        }
    }, [activeTab, adminKey, filters, page]);

    // --- API Helper ---
    async function adminFetch(path, options = {}) {
        const headers = {
            "x-admin-key": adminKey,
            ...options.headers
        };

        try {
            const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

            if (res.status === 401) {
                setStatusMsg("❌ Unauthorized. Please check your Admin Key.");
                return null;
            }
            if (res.status === 500) {
                const err = await res.json().catch(() => ({ detail: "Server Error" }));
                setStatusMsg(`❌ Server Error: ${err.detail}`);
                return null;
            }
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Unknown Error" }));
                setStatusMsg(`⚠️ Error: ${err.detail}`);
                return null;
            }

            return await res.json();
        } catch (err) {
            setStatusMsg("❌ Network Error. Is backend running?");
            return null;
        }
    }

    // --- Fetchers ---
    async function fetchAnalytics() {
        const data = await adminFetch("/admin/analytics");
        if (data) setAnalytics(data);
    }

    async function fetchFiles() {
        const data = await adminFetch("/admin/files");
        if (data) setFiles(data);
    }

    async function fetchIndexStatus() {
        const data = await adminFetch("/admin/index/status");
        if (data) setIdxStatus(data);
    }

    async function fetchBookings() {
        // Build query
        const query = new URLSearchParams({
            limit: LIMIT,
            offset: page * LIMIT
        });
        if (filters.date) query.append("date", filters.date);
        if (filters.room_type) query.append("room_type", filters.room_type);
        if (filters.status) query.append("status", filters.status);

        const data = await adminFetch(`/admin/bookings?${query.toString()}`);
        if (data) setBookingsData(data);
    }

    async function fetchToolStats() {
        const query = new URLSearchParams({
            days: filters.days,
            limit: filters.limit
        });
        const data = await adminFetch(`/admin/tools/stats?${query.toString()}`);
        if (data) setToolStats(data);
    }

    // --- Actions ---
    async function handleUpload(e, audience) {
        if (!e.target.files[0]) return;
        setUploading(true);
        setStatusMsg("Uploading...");

        const formData = new FormData();
        formData.append("file", e.target.files[0]);
        formData.append("audience", audience);

        // Custom fetch for upload (multipart)
        try {
            const res = await fetch(`${API_BASE}/admin/upload`, {
                method: "POST",
                headers: { "x-admin-key": adminKey },
                body: formData,
            });
            if (res.ok) {
                setStatusMsg("✅ Upload Success.");
                fetchFiles();
            } else {
                const err = await res.json();
                setStatusMsg(`❌ Upload Failed: ${err.detail}`);
            }
        } catch (e) {
            setStatusMsg("❌ Upload Exception.");
        } finally {
            setUploading(false);
        }
    }

    async function handleReindex(audience) {
        if (!confirm(`Reindex ${audience}? This might take a moment.`)) return;
        setStatusMsg("⏳ Reindexing...");
        const res = await adminFetch(`/admin/reindex?audience=${audience}`, { method: "POST" });
        if (res) {
            setStatusMsg("✅ Reindex Complete.");
            fetchIndexStatus();
        }
    }

    // --- Renderers ---
    return (
        <div className="admin-container">
            <header className="admin-header">
                <h1>🧠 Hotel Brain Admin</h1>

                {/* Admin Key Input */}
                <div className="admin-key-section">
                    <label>🔑 Admin Key:</label>
                    <input
                        type="password"
                        value={adminKey}
                        onChange={(e) => setAdminKey(e.target.value)}
                        placeholder="Enter endpoint key..."
                    />
                </div>

                <div className="admin-tabs">
                    <button className={activeTab === "analytics" ? "active" : ""} onClick={() => setActiveTab("analytics")}>Analytics 📊</button>
                    <button className={activeTab === "bookings" ? "active" : ""} onClick={() => setActiveTab("bookings")}>Bookings 📅</button>
                    <button className={activeTab === "tools" ? "active" : ""} onClick={() => setActiveTab("tools")}>Tool Stats 🛠️</button>
                    <button className={activeTab === "files" ? "active" : ""} onClick={() => setActiveTab("files")}>Knowledge 📚</button>
                </div>

                {statusMsg && <div className="status-msg" style={{ textAlign: "center", marginTop: "1rem", color: statusMsg.includes("❌") ? "red" : "green" }}>{statusMsg}</div>}
            </header>

            {!adminKey && (
                <div style={{ textAlign: "center", padding: "2rem" }}>
                    <h2>Please enter Admin API Key to proceed.</h2>
                </div>
            )}

            {/* TAB: ANALYTICS (Existing Logic) */}
            {activeTab === "analytics" && analytics && adminKey && (
                <div className="dashboard-grid">
                    <div className="stats-row">
                        <div className="stat-card">
                            <h3>Active Chats</h3>
                            <div className="stat-value">{analytics.daily_stats.active_chats}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Queries Today</h3>
                            <div className="stat-value">{analytics.daily_stats.queries_today}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Total Bookings</h3>
                            <div className="stat-value">{bookingsData?.summary?.total || "-"}</div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB: BOOKINGS */}
            {activeTab === "bookings" && bookingsData && adminKey && (
                <div>
                    <div className="filter-bar">
                        <input type="date" value={filters.date} onChange={e => setFilters({ ...filters, date: e.target.value })} />
                        <select value={filters.room_type} onChange={e => setFilters({ ...filters, room_type: e.target.value })}>
                            <option value="">All Rooms</option>
                            <option value="Standard">Standard</option>
                            <option value="Deluxe">Deluxe</option>
                            <option value="Suite">Suite</option>
                        </select>
                        <select value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })}>
                            <option value="">All Statuses</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                        <button className="btn-primary" onClick={fetchBookings}>Apply Filters</button>
                    </div>

                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Booking ID</th>
                                    <th>Guest</th>
                                    <th>Room</th>
                                    <th>Date</th>
                                    <th>Status</th>
                                    <th>Created At</th>
                                </tr>
                            </thead>
                            <tbody>
                                {bookingsData.bookings.map(b => (
                                    <tr key={b.booking_id}>
                                        <td>{b.booking_id}</td>
                                        <td>{b.guest_name}</td>
                                        <td>{b.room_type}</td>
                                        <td>{b.date}</td>
                                        <td>
                                            <span className={`status-badge status-${b.status.toLowerCase()}`}>{b.status}</span>
                                        </td>
                                        <td>{b.created_at}</td>
                                    </tr>
                                ))}
                                {bookingsData.bookings.length === 0 && <tr><td colSpan="6" style={{ textAlign: "center" }}>No bookings found.</td></tr>}
                            </tbody>
                        </table>
                    </div>

                    <div className="pagination">
                        <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous</button>
                        <span>Page {page + 1}</span>
                        <button disabled={bookingsData.bookings.length < LIMIT} onClick={() => setPage(p => p + 1)}>Next</button>
                    </div>
                </div>
            )}

            {/* TAB: TOOLS */}
            {activeTab === "tools" && toolStats && adminKey && (
                <div>
                    <div className="filter-bar">
                        <label>Days: </label>
                        <select value={filters.days} onChange={e => setFilters({ ...filters, days: e.target.value })}>
                            <option value="1">Last 24h</option>
                            <option value="7">Last 7 Days</option>
                            <option value="30">Last 30 Days</option>
                        </select>
                    </div>

                    <div className="stats-row" style={{ marginBottom: "2rem" }}>
                        <div className="stat-card">
                            <h3>Total Calls</h3>
                            <div className="stat-value">{toolStats.totals.tool_calls}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Success</h3>
                            <div className="stat-value" style={{ color: "green" }}>{toolStats.totals.success}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Avg Latency</h3>
                            <div className="stat-value">{toolStats.totals.avg_latency_ms}ms</div>
                        </div>
                    </div>

                    <h3>Tool Usage Breakdown</h3>
                    <div className="table-container">
                        <table className="data-table">
                            <thead><tr><th>Tool</th><th>Calls</th><th>Success</th><th>Failed</th><th>Avg Latency</th></tr></thead>
                            <tbody>
                                {toolStats.by_tool.map(t => (
                                    <tr key={t.tool_name}>
                                        <td>{t.tool_name}</td>
                                        <td>{t.tool_calls}</td>
                                        <td>{t.success}</td>
                                        <td>{t.failed}</td>
                                        <td>{t.avg_latency_ms}ms</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* TAB: FILES (Knowledge) */}
            {activeTab === "files" && adminKey && (
                <div className="admin-grid">
                    <div className="admin-card">
                        <h2>Manage Files</h2>
                        <div className="file-list">
                            <h3>Guest Docs</h3>
                            <ul>{files.guest.map(f => <li key={f}>{f}</li>)}</ul>
                            <div className="upload-zone" style={{ marginTop: "1rem" }}>
                                <input type="file" onChange={(e) => handleUpload(e, "guest")} disabled={uploading} />
                            </div>
                        </div>
                        <div className="file-list" style={{ marginTop: "2rem" }}>
                            <h3>Staff Docs</h3>
                            <ul>{files.staff.map(f => <li key={f}>{f}</li>)}</ul>
                            <div className="upload-zone" style={{ marginTop: "1rem" }}>
                                <input type="file" onChange={(e) => handleUpload(e, "staff")} disabled={uploading} />
                            </div>
                        </div>
                    </div>

                    <div className="admin-card">
                        <h2>Index Status 🧠</h2>
                        {idxStatus ? (
                            <div>
                                <p><strong>Guest Docs Indexed:</strong> {idxStatus.guest_docs}</p>
                                <p><strong>Staff Docs Indexed:</strong> {idxStatus.staff_docs}</p>
                                <p><strong>Last Reindex:</strong> {idxStatus.last_reindex_time || "Never"}</p>
                                {idxStatus.last_reindex_error && <p style={{ color: "red" }}>Last Error: {idxStatus.last_reindex_error}</p>}
                            </div>
                        ) : <p>Loading status...</p>}

                        <div style={{ display: "flex", gap: "10px", marginTop: "2rem" }}>
                            <button className="btn-primary" onClick={() => handleReindex("guest")}>Reindex Guest</button>
                            <button className="btn-primary" onClick={() => handleReindex("staff")}>Reindex Staff</button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}
