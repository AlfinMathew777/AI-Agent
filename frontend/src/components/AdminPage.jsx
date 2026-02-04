
import { useState, useEffect } from "react";
import "./AdminPage.css";

// Backend server runs on port 8002
const API_BASE = "http://127.0.0.1:8002";

export default function AdminPage() {
    // --- State ---
    // Auth - Always start with empty key to require authentication
    // Don't load from localStorage - force fresh login each time
    const [adminKey, setAdminKey] = useState(() => {
        // Always start empty - require login every time
        return "";
    });
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    // Tabs - Enhanced with room management and properties
    const [activeTab, setActiveTab] = useState("overview"); // overview | system | chats | payments | health | rooms | reservations | housekeeping | properties

    // Data State
    const [analytics, setAnalytics] = useState(null);
    const [files, setFiles] = useState({ guest: [], staff: [] });
    const [bookingsData, setBookingsData] = useState({ bookings: [], summary: {} });
    const [toolStats, setToolStats] = useState(null);
    const [idxStatus, setIdxStatus] = useState(null);
    const [chatsData, setChatsData] = useState({ chats: [], total: 0 });
    const [operationsData, setOperationsData] = useState(null);
    const [paymentsData, setPaymentsData] = useState({ payments: [] });
    const [receiptsData, setReceiptsData] = useState({ receipts: [] });
    const [healthData, setHealthData] = useState(null);
    const [roomsData, setRoomsData] = useState({ rooms: [], statistics: {} });
    const [reservationsData, setReservationsData] = useState({ reservations: [], total: 0 });
    const [housekeepingData, setHousekeepingData] = useState({ tasks: [], total: 0, statistics: {} });
    const [propertiesData, setPropertiesData] = useState({ properties: [] });
    const [marketplaceData, setMarketplaceData] = useState({ properties: [] });
    const [systemStatus, setSystemStatus] = useState(null);
    const [featureStatus, setFeatureStatus] = useState([]);

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
    // On mount, check if there's a saved admin key and validate it
    useEffect(() => {
        const savedKey = localStorage.getItem("adminKey");
        if (savedKey && savedKey.trim()) {
            // Auto-validate the saved key on mount
            const validateSavedKey = async () => {
                try {
                    const response = await fetch(`${API_BASE}/admin/system/status`, {
                        method: "GET",
                        headers: {
                            "x-admin-key": savedKey.trim(),
                            "X-Tenant-ID": "default-tenant-0000"
                        }
                    });

                    if (response.ok) {
                        setAdminKey(savedKey.trim());
                        setIsAuthenticated(true);
                    } else {
                        // Invalid saved key, clear it
                        localStorage.removeItem("adminKey");
                        setAdminKey("");
                        setIsAuthenticated(false);
                    }
                } catch (error) {
                    // Connection error, clear saved key
                    localStorage.removeItem("adminKey");
                    setAdminKey("");
                    setIsAuthenticated(false);
                }
            };
            validateSavedKey();
        } else {
            // No saved key, show login form
            setAdminKey("");
            setIsAuthenticated(false);
        }
    }, []); // Only run on mount

    // Validate admin key function (called on button click)
    async function validateAndSetAdminKey(keyToValidate) {
        if (!keyToValidate || !keyToValidate.trim()) {
            setStatusMsg("⚠️ Please enter an admin key");
            return;
        }

        setStatusMsg("⏳ Validating admin key...");

        try {
            const trimmedKey = keyToValidate.trim();
            console.log("🔐 Attempting login with key length:", trimmedKey.length);

            const response = await fetch(`${API_BASE}/admin/system/status`, {
                method: "GET",
                headers: {
                    "x-admin-key": trimmedKey,
                    "X-Tenant-ID": "default-tenant-0000",
                    "Content-Type": "application/json"
                }
            });

            console.log("🔐 Login response status:", response.status);

            if (response.ok) {
                const trimmedKey = keyToValidate.trim();
                setAdminKey(trimmedKey);
                setIsAuthenticated(true);
                setStatusMsg("✅ Admin key validated successfully");
                // Save to localStorage for this session
                localStorage.setItem("adminKey", trimmedKey);
            } else {
                setIsAuthenticated(false);
                const err = await response.json().catch(() => ({ detail: "Invalid admin key" }));
                setStatusMsg(`❌ ${err.detail || "Invalid admin key. Please try again."}`);
                setAdminKey("");
            }
        } catch (error) {
            setIsAuthenticated(false);
            console.error("Admin key validation error:", error);
            const errorMsg = error.message || "Could not validate admin key";
            if (errorMsg.includes("Failed to fetch") || errorMsg.includes("NetworkError")) {
                setStatusMsg(`❌ Connection error: Backend not running on port 8002. Please start the backend server.`);
            } else {
                setStatusMsg(`❌ Error: ${errorMsg}. Please check your connection.`);
            }
            setAdminKey("");
        }
    }

    // Keep adminKey state in sync with localStorage
    useEffect(() => {
        const savedKey = localStorage.getItem("adminKey");
        if (savedKey && savedKey !== adminKey && isAuthenticated) {
            // Update state if localStorage has a different (newer) key
            setAdminKey(savedKey);
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (!adminKey || !isAuthenticated) {
            // Don't fetch data if not authenticated
            return;
        }

        // Ensure adminKey is saved to localStorage
        if (adminKey && !localStorage.getItem("adminKey")) {
            localStorage.setItem("adminKey", adminKey);
        }

        // Reset page on tab switch
        setPage(0);
        setStatusMsg("");

        // Fetch data based on active tab
        if (activeTab === "overview") {
            fetchAnalytics();
            fetchOperations();
            fetchHealth();
            fetchRoomStatistics();
        }
        if (activeTab === "chats") fetchChats();
        if (activeTab === "payments") {
            fetchPayments();
            fetchReceipts();
        }
        if (activeTab === "health") fetchHealth();
        if (activeTab === "rooms") {
            fetchRooms();
            fetchRoomStatistics();
        }
        if (activeTab === "reservations") fetchReservations();
        if (activeTab === "housekeeping") {
            fetchHousekeeping();
            fetchHousekeepingStatistics();
        }
        if (activeTab === "properties") {
            fetchProperties();
            fetchMarketplace();
        }
        if (activeTab === "system") {
            fetchSystemStatus();
            fetchAnalytics();
            fetchProperties();
            fetchRoomStatistics();
            fetchHousekeepingStatistics();
        }
    }, [activeTab, adminKey, isAuthenticated, filters, page]);

    // --- API Helper ---
    async function adminFetch(path, options = {}) {
        // Get admin key from state or localStorage (fallback)
        // Always check localStorage as fallback to ensure we have the key
        const currentAdminKey = adminKey || localStorage.getItem("adminKey") || "";

        // CRITICAL: Check for admin key FIRST before creating headers
        if (!currentAdminKey || !currentAdminKey.trim()) {
            console.error("❌ Admin key missing in adminFetch for path:", path);
            console.error("   adminKey state:", adminKey);
            console.error("   localStorage adminKey:", localStorage.getItem("adminKey"));
            setStatusMsg("❌ Admin key missing. Please log in again.");
            setIsAuthenticated(false);
            return null;
        }

        // If no admin key and we're authenticated, something is wrong
        if (!currentAdminKey && isAuthenticated) {
            console.warn("Admin key missing but authenticated - re-validating...");
            setIsAuthenticated(false);
            return null;
        }

        // Get JWT token if available (for production auth)
        const token = localStorage.getItem("access_token") || localStorage.getItem("token");

        // ALWAYS include admin key - this is REQUIRED for admin endpoints
        const trimmedKey = currentAdminKey.trim();
        const headers = {
            "Content-Type": "application/json",
            "x-admin-key": trimmedKey,  // ALWAYS include - required for admin endpoints
            ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            "X-Tenant-ID": "default-tenant-0000",
            ...options.headers
        };

        // Debug: Log the headers being sent (without showing the full key)
        console.log(`📤 Request to ${path}`, {
            hasAdminKey: !!trimmedKey,
            keyLength: trimmedKey.length,
            keyPrefix: trimmedKey.substring(0, 10) + "..."
        });

        try {
            const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

            if (res.status === 401) {
                const err = await res.json().catch(() => ({ detail: "Unauthorized" }));
                // Only show error if we're authenticated (to avoid showing error during login)
                if (isAuthenticated) {
                    setStatusMsg(`❌ Unauthorized: ${err.detail || "Please check your Admin Key or login."}`);
                    // Clear authentication on 401
                    setIsAuthenticated(false);
                    setAdminKey("");
                    localStorage.removeItem("adminKey");
                }
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

            // Clear any previous error messages on successful request
            // Use functional update to ensure we have the latest statusMsg
            setStatusMsg(prev => {
                if (prev && prev.includes("❌")) {
                    return ""; // Clear error messages
                }
                return prev; // Keep success/info messages
            });

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

    async function fetchChats() {
        const query = new URLSearchParams({
            limit: LIMIT,
            offset: page * LIMIT
        });
        if (filters.audience) query.append("audience", filters.audience);

        const data = await adminFetch(`/admin/chats?${query.toString()}`);
        if (data) setChatsData(data);
    }

    async function fetchOperations() {
        const data = await adminFetch("/admin/operations");
        if (data) {
            // Transform to match expected format
            const transformed = {
                summary: {
                    bookings_today: data.summary.by_type?.booking?.count || 0,
                    reservations_today: data.summary.by_type?.reservation?.count || 0,
                    tickets_today: data.summary.by_type?.ticket?.count || 0,
                    revenue_today_cents: data.summary.revenue_today_cents || 0
                },
                recent_operations: data.recent_operations || []
            };
            setOperationsData(transformed);
        }
    }

    async function fetchPayments() {
        const query = new URLSearchParams({ limit: LIMIT });
        if (filters.payment_status) query.append("status", filters.payment_status);

        const data = await adminFetch(`/admin/payments?${query.toString()}`);
        if (data) setPaymentsData(data);
    }

    async function fetchReceipts() {
        const query = new URLSearchParams({ limit: LIMIT });
        if (filters.date_from) query.append("date_from", filters.date_from);
        if (filters.date_to) query.append("date_to", filters.date_to);

        const data = await adminFetch(`/admin/receipts?${query.toString()}`);
        if (data) setReceiptsData(data);
    }

    async function fetchHealth() {
        const data = await adminFetch("/admin/system/status");
        if (data) {
            // Transform to match expected format
            setHealthData({
                database: data.database,
                ai_service: data.ai_service,
                redis: data.queue || "unavailable",
                recent_errors: data.recent_errors || []
            });
        }
    }

    async function fetchRooms() {
        const query = new URLSearchParams();
        if (filters.floor) query.append("floor", filters.floor);
        if (filters.room_type) query.append("room_type", filters.room_type);
        if (filters.status) query.append("status", filters.status);

        const data = await adminFetch(`/admin/rooms?${query.toString()}`);
        if (data) setRoomsData(prev => ({ ...prev, rooms: data.rooms || [] }));
    }

    async function fetchRoomStatistics() {
        const data = await adminFetch("/admin/rooms/statistics");
        if (data) setRoomsData(prev => ({ ...prev, statistics: data }));
    }

    async function fetchReservations() {
        const query = new URLSearchParams({
            limit: LIMIT,
            offset: page * LIMIT
        });
        if (filters.status) query.append("status", filters.status);
        if (filters.room_number) query.append("room_number", filters.room_number);

        const data = await adminFetch(`/admin/reservations?${query.toString()}`);
        if (data) setReservationsData(data);
    }

    async function fetchHousekeeping() {
        const query = new URLSearchParams({
            limit: LIMIT,
            offset: page * LIMIT
        });
        if (filters.status) query.append("status", filters.status);

        const data = await adminFetch(`/admin/housekeeping/tasks?${query.toString()}`);
        if (data) setHousekeepingData(prev => ({ ...prev, tasks: data.tasks || [], total: data.total || 0 }));
    }

    async function fetchHousekeepingStatistics() {
        const data = await adminFetch("/admin/housekeeping/statistics");
        if (data) setHousekeepingData(prev => ({ ...prev, statistics: data }));
    }

    async function fetchProperties() {
        const data = await adminFetch("/admin/properties");
        if (data) setPropertiesData(data);
    }

    async function fetchMarketplace() {
        const data = await adminFetch("/marketplace/properties");
        if (data) setMarketplaceData(data);
    }

    async function pauseProperty(propertyId) {
        setStatusMsg("⏳ Pausing property...");
        const data = await adminFetch(`/admin/properties/${propertyId}/pause`, { method: "POST" });
        if (data) {
            setStatusMsg("✅ Property paused successfully");
            await fetchProperties();
            await fetchMarketplace();
        }
    }

    async function resumeProperty(propertyId) {
        setStatusMsg("⏳ Resuming property...");
        const data = await adminFetch(`/admin/properties/${propertyId}/resume`, { method: "POST" });
        if (data) {
            setStatusMsg("✅ Property resumed successfully");
            await fetchProperties();
            await fetchMarketplace();
        }
    }

    async function fetchSystemStatus() {
        const data = await adminFetch("/admin/system/status");
        if (data) setSystemStatus(data);
    }

    async function checkAllFeatures() {
        const features = [];
        setStatusMsg("⏳ Testing all features...");

        // Test Marketplace
        try {
            const marketplace = await adminFetch("/marketplace/properties");
            features.push({
                name: "Marketplace Properties",
                endpoint: "GET /marketplace/properties",
                page: "Properties",
                status: marketplace ? "✅ Working" : "⚠️ Partial",
                notes: `${marketplace?.properties?.length || 0} active properties`
            });
        } catch (e) {
            features.push({
                name: "Marketplace Properties",
                endpoint: "GET /marketplace/properties",
                page: "Properties",
                status: "❌ Broken",
                notes: e.message
            });
        }

        // Test Properties
        try {
            const props = await adminFetch("/admin/properties");
            features.push({
                name: "Properties Management",
                endpoint: "GET /admin/properties",
                page: "Properties",
                status: props ? "✅ Working" : "⚠️ Partial",
                notes: `${props?.properties?.length || 0} total properties`
            });
        } catch (e) {
            features.push({
                name: "Properties Management",
                endpoint: "GET /admin/properties",
                page: "Properties",
                status: "❌ Broken",
                notes: e.message
            });
        }

        // Test Rooms
        try {
            const rooms = await adminFetch("/admin/rooms");
            features.push({
                name: "Rooms Management",
                endpoint: "GET /admin/rooms",
                page: "Rooms",
                status: rooms ? "✅ Working" : "⚠️ Partial",
                notes: `${rooms?.rooms?.length || 0} rooms`
            });
        } catch (e) {
            features.push({
                name: "Rooms Management",
                endpoint: "GET /admin/rooms",
                page: "Rooms",
                status: "❌ Broken",
                notes: e.message
            });
        }

        // Test Housekeeping
        try {
            const hk = await adminFetch("/admin/housekeeping/tasks");
            features.push({
                name: "Housekeeping Tasks",
                endpoint: "GET /admin/housekeeping/tasks",
                page: "Housekeeping",
                status: hk ? "✅ Working" : "⚠️ Partial",
                notes: `${hk?.tasks?.length || 0} tasks`
            });
        } catch (e) {
            features.push({
                name: "Housekeeping Tasks",
                endpoint: "GET /admin/housekeeping/tasks",
                page: "Housekeeping",
                status: "❌ Broken",
                notes: e.message
            });
        }

        // Test Index
        try {
            const idx = await adminFetch("/admin/index/status");
            features.push({
                name: "Document Index",
                endpoint: "GET /admin/index/status",
                page: "Knowledge Base",
                status: idx ? "✅ Working" : "⚠️ Partial",
                notes: `${idx?.total_docs || 0} docs indexed`
            });
        } catch (e) {
            features.push({
                name: "Document Index",
                endpoint: "GET /admin/index/status",
                page: "Knowledge Base",
                status: "❌ Broken",
                notes: e.message
            });
        }

        setFeatureStatus(features);
        setStatusMsg("✅ Feature status check complete");
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
    if (!adminKey || !isAuthenticated) {
        return (
            <div className="admin-container">
                <div className="admin-key-section">
                    <h2>🔑 Admin Access</h2>
                    <label>Enter Admin API Key:</label>
                    <input
                        type="password"
                        value={adminKey}
                        onChange={(e) => setAdminKey(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && adminKey.trim()) {
                                e.preventDefault();
                                validateAndSetAdminKey(adminKey);
                            }
                        }}
                        placeholder="Enter your admin key (shhg_admin_secure_key_2024)..."
                    />
                    <small style={{ color: "#666", marginTop: "0.5rem", display: "block" }}>
                        Default key: shhg_admin_secure_key_2024
                    </small>
                    <button
                        className="btn-primary"
                        style={{ width: "100%" }}
                        onClick={() => validateAndSetAdminKey(adminKey)}
                        disabled={!adminKey.trim()}
                    >
                        Access Dashboard
                    </button>
                    {statusMsg && (
                        <div className="status-msg" style={{ marginTop: "1rem", color: statusMsg.includes("❌") ? "#dc2626" : statusMsg.includes("✅") ? "#059669" : "#666" }}>
                            {statusMsg}
                        </div>
                    )}
                    <div style={{ marginTop: "1rem", fontSize: "0.85rem", color: "#666" }}>
                        <strong>Backend URL:</strong> {API_BASE}<br />
                        <strong>Admin Key:</strong> shhg_admin_secure_key_2024
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-container">
            {/* Exit Button - Return to Main Site */}
            <button
                className="admin-exit-btn"
                onClick={() => {
                    // Clear admin session
                    localStorage.removeItem("adminKey");
                    setIsAuthenticated(false);
                    setAdminKey("");
                    // Navigate back to main site
                    window.location.href = "/";
                }}
                title="Return to Main Site"
            >
                ← Back to Site
            </button>

            {/* Sidebar */}
            <aside className="admin-sidebar">
                <div className="sidebar-logo">
                    <h1>SOUTHERN HORIZONS</h1>
                    <p>HOTEL MANAGEMENT</p>
                </div>

                <div className="sidebar-profile">
                    <div className="profile-avatar">A</div>
                    <div className="profile-info">
                        <div className="profile-name">Admin</div>
                        <div className="profile-role">Admin</div>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <div
                        className={`nav-item ${activeTab === "overview" ? "active" : ""}`}
                        onClick={() => setActiveTab("overview")}
                    >
                        <div className="nav-icon">📊</div>
                        <span>Dashboard</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "system" ? "active" : ""}`}
                        onClick={() => setActiveTab("system")}
                    >
                        <div className="nav-icon">🏥</div>
                        <span>System Status</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "chats" ? "active" : ""}`}
                        onClick={() => setActiveTab("chats")}
                    >
                        <div className="nav-icon">💬</div>
                        <span>Chats</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "payments" ? "active" : ""}`}
                        onClick={() => setActiveTab("payments")}
                    >
                        <div className="nav-icon">💳</div>
                        <span>Payments</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "rooms" ? "active" : ""}`}
                        onClick={() => setActiveTab("rooms")}
                    >
                        <div className="nav-icon">🛏️</div>
                        <span>Rooms</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "reservations" ? "active" : ""}`}
                        onClick={() => setActiveTab("reservations")}
                    >
                        <div className="nav-icon">📅</div>
                        <span>Reservations</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "housekeeping" ? "active" : ""}`}
                        onClick={() => setActiveTab("housekeeping")}
                    >
                        <div className="nav-icon">🧹</div>
                        <span>Housekeeping</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "users" ? "active" : ""}`}
                        onClick={() => setActiveTab("users")}
                    >
                        <div className="nav-icon">👥</div>
                        <span>Users</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "properties" ? "active" : ""}`}
                        onClick={() => setActiveTab("properties")}
                    >
                        <div className="nav-icon">🏨</div>
                        <span>Properties</span>
                    </div>
                    <div
                        className={`nav-item ${activeTab === "health" ? "active" : ""}`}
                        onClick={() => setActiveTab("health")}
                    >
                        <div className="nav-icon">🏥</div>
                        <span>System Health</span>
                    </div>
                </nav>

                <div className="sidebar-logout">
                    <button className="logout-btn" onClick={() => {
                        // Clear localStorage first
                        localStorage.removeItem("adminKey");
                        // Clear authentication state
                        setIsAuthenticated(false);
                        // Clear admin key - this will trigger the login screen to show
                        setAdminKey("");
                        // Clear all state to reset the component
                        setStatusMsg("");
                        setActiveTab("overview");
                        setPage(0);
                        setAnalytics(null);
                        setChatsData({ chats: [], total: 0 });
                        setOperationsData(null);
                        setPaymentsData({ payments: [] });
                        setReceiptsData({ receipts: [] });
                        setHealthData(null);
                        setRoomsData({ rooms: [], statistics: {} });
                        setReservationsData({ reservations: [], total: 0 });
                        setHousekeepingData({ tasks: [], total: 0, statistics: {} });
                        setFiles({ guest: [], staff: [] });
                        setIdxStatus(null);
                        setToolStats(null);
                    }}>
                        <span>Logout</span>
                        <span>→</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="admin-main">
                {statusMsg && (
                    <div className="status-msg" style={{ color: statusMsg.includes("❌") ? "#dc2626" : "#059669", background: statusMsg.includes("❌") ? "#fee2e2" : "#d1fae5" }}>
                        {statusMsg}
                    </div>
                )}

                {/* TAB: OVERVIEW - Professional dashboard */}
                {activeTab === "overview" && (
                    <>
                        {/* Welcome Section */}
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Welcome back, <span>Admin</span> 👋</h2>
                            </div>
                            <div className="overview-box">
                                Today's Overview
                            </div>
                        </div>

                        {/* Today's Stats - Compact Room Statistics */}
                        <div className="stats-row compact">
                            <div className="stat-card beige">
                                <div className="stat-header">
                                    <div className="stat-label">TOTAL ROOMS</div>
                                    <div className="stat-icon beige">🚪</div>
                                </div>
                                <div className="stat-value">{roomsData?.statistics?.total || 0}</div>
                            </div>

                            <div className="stat-card green">
                                <div className="stat-header">
                                    <div className="stat-label">AVAILABLE</div>
                                    <div className="stat-icon green">✅</div>
                                </div>
                                <div className="stat-value">{roomsData?.statistics?.available || 0}</div>
                            </div>

                            <div className="stat-card red">
                                <div className="stat-header">
                                    <div className="stat-label">OCCUPIED</div>
                                    <div className="stat-icon red">🛏️</div>
                                </div>
                                <div className="stat-value">{roomsData?.statistics?.occupied || 0}</div>
                            </div>

                            <div className="stat-card blue">
                                <div className="stat-header">
                                    <div className="stat-label">CLEANING NEEDED</div>
                                    <div className="stat-icon blue">🧹</div>
                                </div>
                                <div className="stat-value">{roomsData?.statistics?.cleaning_needed || 0}</div>
                            </div>

                            <div className="stat-card beige">
                                <div className="stat-header">
                                    <div className="stat-label">CLEANERS AVAILABLE</div>
                                    <div className="stat-icon beige">👷</div>
                                </div>
                                <div className="stat-value">{housekeepingData?.statistics?.in_progress ? 1 : 0}</div>
                            </div>

                            <div className="stat-card gold">
                                <div className="stat-header">
                                    <div className="stat-label">UNDER MAINTENANCE</div>
                                    <div className="stat-icon gold">🔧</div>
                                </div>
                                <div className="stat-value">{roomsData?.statistics?.maintenance || 0}</div>
                                <div className="stat-subtitle">Rooms being serviced</div>
                            </div>
                        </div>

                        {/* Recent Activity */}
                        {operationsData && operationsData.recent_operations && operationsData.recent_operations.length > 0 && (
                            <div className="content-section">
                                <h2 className="section-title">Recent Operations</h2>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr><th>Type</th><th>Reference</th><th>Customer</th><th>Time</th><th>Status</th></tr>
                                        </thead>
                                        <tbody>
                                            {operationsData.recent_operations.slice(0, 10).map((op, idx) => (
                                                <tr key={idx}>
                                                    <td>{op.type}</td>
                                                    <td>{op.ref || op.entity_id || "-"}</td>
                                                    <td>{op.customer || "-"}</td>
                                                    <td>{new Date(op.created_at).toLocaleString()}</td>
                                                    <td><span className={`status-badge status-${op.status || "pending"}`}>{op.status || "Pending"}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </>
                )}

                {/* TAB: SYSTEM STATUS */}
                {activeTab === "system" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>System Status</h2>
                                <p>Monitor system health and feature availability</p>
                            </div>
                        </div>

                        {/* Health Status Cards */}
                        <div className="stats-row">
                            <div className="stat-card green">
                                <div className="stat-header">
                                    <span className="stat-label">Database</span>
                                    <div className="stat-icon green">
                                        {systemStatus?.database === "healthy" ? "✅" : "❌"}
                                    </div>
                                </div>
                                <div className="stat-value" style={{ fontSize: "1.25rem" }}>
                                    {systemStatus?.database || "Unknown"}
                                </div>
                            </div>

                            <div className="stat-card blue">
                                <div className="stat-header">
                                    <span className="stat-label">AI Service</span>
                                    <div className="stat-icon blue">🤖</div>
                                </div>
                                <div className="stat-value" style={{ fontSize: "1.25rem" }}>
                                    {systemStatus?.ai_service || "Unknown"}
                                </div>
                            </div>

                            <div className="stat-card gold">
                                <div className="stat-header">
                                    <span className="stat-label">Queue</span>
                                    <div className="stat-icon gold">⚡</div>
                                </div>
                                <div className="stat-value" style={{ fontSize: "1.25rem" }}>
                                    {systemStatus?.queue || "Unknown"}
                                </div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-header">
                                    <span className="stat-label">Index Docs</span>
                                    <div className="stat-icon">📚</div>
                                </div>
                                <div className="stat-value">
                                    {idxStatus?.total_docs || 0}
                                </div>
                                <div className="stat-subtitle">documents indexed</div>
                            </div>
                        </div>

                        {/* Quick Summary Cards */}
                        <div className="stats-row">
                            <div className="stat-card">
                                <div className="stat-header">
                                    <span className="stat-label">Properties</span>
                                    <div className="stat-icon">🏨</div>
                                </div>
                                <div className="stat-value">
                                    {propertiesData?.properties?.filter(p => p.is_active).length || 0} / {propertiesData?.properties?.length || 0}
                                </div>
                                <div className="stat-subtitle">active / total</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-header">
                                    <span className="stat-label">Rooms</span>
                                    <div className="stat-icon">🛏️</div>
                                </div>
                                <div className="stat-value">
                                    {roomsData?.statistics?.total_rooms || 0}
                                </div>
                                <div className="stat-subtitle">total rooms</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-header">
                                    <span className="stat-label">HK Tasks</span>
                                    <div className="stat-icon">🧹</div>
                                </div>
                                <div className="stat-value">
                                    {housekeepingData?.statistics?.pending || 0}
                                </div>
                                <div className="stat-subtitle">pending tasks</div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-header">
                                    <span className="stat-label">Chats Today</span>
                                    <div className="stat-icon">💬</div>
                                </div>
                                <div className="stat-value">
                                    {analytics?.total_today || 0}
                                </div>
                                <div className="stat-subtitle">conversations</div>
                            </div>
                        </div>

                        {/* Feature Status Board */}
                        <div className="content-section">
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                                <h3>Feature Status Board</h3>
                                <button className="btn-primary" onClick={checkAllFeatures}>
                                    🧪 Test All Features
                                </button>
                            </div>
                            <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "1rem" }}>
                                Click "Test All Features" to ping each endpoint and verify system health
                            </p>

                            {featureStatus.length > 0 ? (
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Feature</th>
                                                <th>Endpoint</th>
                                                <th>UI Page</th>
                                                <th>Status</th>
                                                <th>Notes</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {featureStatus.map((feature, idx) => (
                                                <tr key={idx}>
                                                    <td>{feature.name}</td>
                                                    <td><code style={{ fontSize: "0.8rem", background: "#f3f4f6", padding: "0.25rem 0.5rem", borderRadius: "4px" }}>{feature.endpoint}</code></td>
                                                    <td>{feature.page}</td>
                                                    <td>{feature.status}</td>
                                                    <td style={{ fontSize: "0.875rem", color: "#666" }}>{feature.notes}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div style={{ padding: "2rem", textAlign: "center", background: "#f9fafb", borderRadius: "8px" }}>
                                    <p style={{ color: "#666" }}>No feature tests run yet. Click "Test All Features" to begin.</p>
                                </div>
                            )}
                        </div>

                        {/* Recent Errors (if any) */}
                        {systemStatus?.recent_errors && systemStatus.recent_errors.length > 0 && (
                            <div className="content-section" style={{ borderLeft: "4px solid #ef4444" }}>
                                <h3 style={{ color: "#ef4444" }}>⚠️ Recent Errors</h3>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Error</th>
                                                <th>Details</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {systemStatus.recent_errors.slice(0, 10).map((err, idx) => (
                                                <tr key={idx}>
                                                    <td>{new Date(err.timestamp).toLocaleString()}</td>
                                                    <td>{err.error_type || "Unknown"}</td>
                                                    <td style={{ fontSize: "0.875rem", color: "#666" }}>{err.message || "-"}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </>
                )}

                {/* TAB: CHATS */}
                {activeTab === "chats" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Chat History</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <div className="filter-bar">
                                <select value={filters.audience || ""} onChange={e => setFilters({ ...filters, audience: e.target.value })}>
                                    <option value="">All Audiences</option>
                                    <option value="guest">Guest</option>
                                    <option value="staff">Staff</option>
                                </select>
                                <button className="btn-primary" onClick={fetchChats}>Refresh</button>
                            </div>

                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Audience</th>
                                            <th>Question</th>
                                            <th>Answer</th>
                                            <th>Model</th>
                                            <th>Latency</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {chatsData?.chats?.map((c, idx) => (
                                            <tr key={c.id || idx}>
                                                <td>{new Date(c.timestamp).toLocaleString()}</td>
                                                <td><span className={`status-badge status-${c.audience}`}>{c.audience}</span></td>
                                                <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis" }}>{c.question}</td>
                                                <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis" }}>{c.answer}</td>
                                                <td>{c.model_used}</td>
                                                <td>{c.latency_ms}ms</td>
                                            </tr>
                                        ))}
                                        {(!chatsData?.chats || chatsData.chats.length === 0) && <tr><td colSpan="6" style={{ textAlign: "center" }}>No chats found.</td></tr>}
                                    </tbody>
                                </table>
                            </div>

                            <div className="pagination">
                                <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous</button>
                                <span>Page {page + 1} (Total: {chatsData?.total || 0})</span>
                                <button disabled={!chatsData?.chats || chatsData.chats.length < LIMIT} onClick={() => setPage(p => p + 1)}>Next</button>
                            </div>
                        </div>
                    </>
                )}

                {/* TAB: PAYMENTS - Combined Payments & Receipts */}
                {activeTab === "payments" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Payments & Receipts</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                                <button
                                    className={filters.payment_view === "payments" || !filters.payment_view ? "btn-primary" : ""}
                                    onClick={() => {
                                        setFilters({ ...filters, payment_view: "payments" });
                                        fetchPayments();
                                    }}
                                >
                                    Payments
                                </button>
                                <button
                                    className={filters.payment_view === "receipts" ? "btn-primary" : ""}
                                    onClick={() => {
                                        setFilters({ ...filters, payment_view: "receipts" });
                                        fetchReceipts();
                                    }}
                                >
                                    Receipts
                                </button>
                            </div>

                            {/* Payments View */}
                            {(!filters.payment_view || filters.payment_view === "payments") && paymentsData && (
                                <div>
                                    <div className="filter-bar">
                                        <select value={filters.payment_status || ""} onChange={e => setFilters({ ...filters, payment_status: e.target.value })}>
                                            <option value="">All Statuses</option>
                                            <option value="paid">Paid</option>
                                            <option value="pending">Pending</option>
                                            <option value="failed">Failed</option>
                                        </select>
                                        <button className="btn-primary" onClick={fetchPayments}>Apply Filter</button>
                                    </div>

                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr><th>Payment ID</th><th>Quote ID</th><th>Amount</th><th>Status</th><th>Created</th></tr>
                                            </thead>
                                            <tbody>
                                                {paymentsData.payments.map(p => (
                                                    <tr key={p.id}>
                                                        <td>{p.id}</td>
                                                        <td>{p.quote_id}</td>
                                                        <td>${(p.amount_cents / 100).toFixed(2)} {p.currency}</td>
                                                        <td><span className={`status-badge status-${p.status}`}>{p.status}</span></td>
                                                        <td>{new Date(p.created_at).toLocaleString()}</td>
                                                    </tr>
                                                ))}
                                                {paymentsData.payments.length === 0 && <tr><td colSpan="5" style={{ textAlign: "center" }}>No payments found.</td></tr>}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {/* Receipts View */}
                            {filters.payment_view === "receipts" && receiptsData && (
                                <div>
                                    <div className="filter-bar">
                                        <label>From:</label>
                                        <input type="date" value={filters.date_from || ""} onChange={e => setFilters({ ...filters, date_from: e.target.value })} />
                                        <label>To:</label>
                                        <input type="date" value={filters.date_to || ""} onChange={e => setFilters({ ...filters, date_to: e.target.value })} />
                                        <button className="btn-primary" onClick={fetchReceipts}>Apply Filter</button>
                                    </div>

                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr><th>Receipt ID</th><th>Quote ID</th><th>Subtotal</th><th>Tax</th><th>Total</th><th>Status</th><th>Created</th></tr>
                                            </thead>
                                            <tbody>
                                                {receiptsData.receipts.map(r => (
                                                    <tr key={r.id}>
                                                        <td>{r.id}</td>
                                                        <td>{r.quote_id}</td>
                                                        <td>${(r.subtotal_cents / 100).toFixed(2)}</td>
                                                        <td>${(r.tax_cents / 100).toFixed(2)}</td>
                                                        <td><strong>${(r.total_cents / 100).toFixed(2)}</strong></td>
                                                        <td><span className={`status-badge status-${r.status}`}>{r.status}</span></td>
                                                        <td>{new Date(r.created_at).toLocaleString()}</td>
                                                    </tr>
                                                ))}
                                                {receiptsData.receipts.length === 0 && <tr><td colSpan="7" style={{ textAlign: "center" }}>No receipts found.</td></tr>}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* TAB: ROOMS */}
                {activeTab === "rooms" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Room Management</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <div className="filter-bar">
                                <select value={filters.floor || ""} onChange={e => setFilters({ ...filters, floor: e.target.value })}>
                                    <option value="">All Floors</option>
                                    <option value="1">Floor 1</option>
                                    <option value="2">Floor 2</option>
                                    <option value="3">Floor 3</option>
                                </select>
                                <select value={filters.room_type || ""} onChange={e => setFilters({ ...filters, room_type: e.target.value })}>
                                    <option value="">All Types</option>
                                    <option value="standard">Standard</option>
                                    <option value="deluxe">Deluxe</option>
                                    <option value="suite">Suite</option>
                                </select>
                                <select value={filters.status || ""} onChange={e => setFilters({ ...filters, status: e.target.value })}>
                                    <option value="">All Statuses</option>
                                    <option value="available">Available</option>
                                    <option value="occupied">Occupied</option>
                                    <option value="cleaning_needed">Cleaning Needed</option>
                                    <option value="maintenance">Maintenance</option>
                                </select>
                                <button className="btn-primary" onClick={fetchRooms}>Refresh</button>
                            </div>

                            {/* Room Statistics */}
                            {roomsData?.statistics && (
                                <div className="stats-row" style={{ marginBottom: "1.5rem" }}>
                                    <div className="stat-card beige">
                                        <div className="stat-header">
                                            <div className="stat-label">Total Rooms</div>
                                            <div className="stat-icon beige">🛏️</div>
                                        </div>
                                        <div className="stat-value">{roomsData.statistics.total || 0}</div>
                                    </div>
                                    <div className="stat-card green">
                                        <div className="stat-header">
                                            <div className="stat-label">Available</div>
                                            <div className="stat-icon green">✅</div>
                                        </div>
                                        <div className="stat-value">{roomsData.statistics.available || 0}</div>
                                    </div>
                                    <div className="stat-card red">
                                        <div className="stat-header">
                                            <div className="stat-label">Occupied</div>
                                            <div className="stat-icon red">🚫</div>
                                        </div>
                                        <div className="stat-value">{roomsData.statistics.occupied || 0}</div>
                                    </div>
                                    <div className="stat-card blue">
                                        <div className="stat-header">
                                            <div className="stat-label">Cleaning Needed</div>
                                            <div className="stat-icon blue">🧹</div>
                                        </div>
                                        <div className="stat-value">{roomsData.statistics.cleaning_needed || 0}</div>
                                    </div>
                                </div>
                            )}

                            {/* Rooms Grid (Grouped by Floor) */}
                            <div className="rooms-grid">
                                {[1, 2, 3].map(floor => {
                                    const floorRooms = roomsData?.rooms?.filter(r => r.floor === floor) || [];
                                    if (floorRooms.length === 0 && filters.floor && filters.floor !== String(floor)) return null;

                                    return (
                                        <div key={floor} className="floor-section">
                                            <h3 className="floor-title">Floor {floor}</h3>
                                            <div className="rooms-row">
                                                {floorRooms.map(room => (
                                                    <div key={room.id} className={`room-card room-${room.status}`}>
                                                        <div className="room-number">{room.room_number}</div>
                                                        <div className="room-type">{room.room_type}</div>
                                                        <div className={`room-status status-${room.status}`}>
                                                            {room.status.replace('_', ' ')}
                                                        </div>
                                                        <div className="room-capacity">Capacity: {room.capacity}</div>
                                                    </div>
                                                ))}
                                                {floorRooms.length === 0 && <p style={{ padding: "1rem", color: "#666" }}>No rooms on this floor</p>}
                                            </div>
                                        </div>
                                    );
                                })}
                                {(!roomsData?.rooms || roomsData.rooms.length === 0) && (
                                    <p style={{ textAlign: "center", padding: "2rem", color: "#666" }}>No rooms found. Create rooms to get started.</p>
                                )}
                            </div>
                        </div>
                    </>
                )}

                {/* TAB: RESERVATIONS */}
                {activeTab === "reservations" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Reservations</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <div className="filter-bar">
                                <select value={filters.status || ""} onChange={e => setFilters({ ...filters, status: e.target.value })}>
                                    <option value="">All Statuses</option>
                                    <option value="pending">Pending</option>
                                    <option value="checked_in">Checked In</option>
                                    <option value="checked_out">Checked Out</option>
                                    <option value="cancelled">Cancelled</option>
                                </select>
                                <input
                                    type="text"
                                    placeholder="Room Number"
                                    value={filters.room_number || ""}
                                    onChange={e => setFilters({ ...filters, room_number: e.target.value })}
                                />
                                <button className="btn-primary" onClick={fetchReservations}>Refresh</button>
                            </div>

                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Guest Name</th>
                                            <th>Room</th>
                                            <th>Check-In</th>
                                            <th>Check-Out</th>
                                            <th>Status</th>
                                            <th>Amount</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reservationsData?.reservations?.map((res, idx) => (
                                            <tr key={res.id || idx}>
                                                <td>{res.guest_name}</td>
                                                <td>{res.room_number}</td>
                                                <td>{res.check_in_date}</td>
                                                <td>{res.check_out_date}</td>
                                                <td><span className={`status-badge status-${res.status}`}>{res.status}</span></td>
                                                <td>${(res.total_amount || 0).toFixed(2)}</td>
                                                <td>
                                                    {res.status === "pending" && (
                                                        <button className="btn-small" onClick={() => {
                                                            adminFetch(`/admin/reservations/${res.id}/checkin`, { method: "PUT" }).then(() => fetchReservations());
                                                        }}>Check In</button>
                                                    )}
                                                    {res.status === "checked_in" && (
                                                        <button className="btn-small" onClick={() => {
                                                            adminFetch(`/admin/reservations/${res.id}/checkout`, { method: "PUT" }).then(() => fetchReservations());
                                                        }}>Check Out</button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                        {(!reservationsData?.reservations || reservationsData.reservations.length === 0) && (
                                            <tr><td colSpan="7" style={{ textAlign: "center" }}>No reservations found.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            <div className="pagination">
                                <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous</button>
                                <span>Page {page + 1} (Total: {reservationsData?.total || 0})</span>
                                <button disabled={!reservationsData?.reservations || reservationsData.reservations.length < LIMIT} onClick={() => setPage(p => p + 1)}>Next</button>
                            </div>
                        </div>
                    </>
                )}

                {/* TAB: HOUSEKEEPING */}
                {activeTab === "housekeeping" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Housekeeping</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <div className="filter-bar">
                                <select value={filters.status || ""} onChange={e => setFilters({ ...filters, status: e.target.value })}>
                                    <option value="">All Statuses</option>
                                    <option value="pending">Pending</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                </select>
                                <button className="btn-primary" onClick={fetchHousekeeping}>Refresh</button>
                            </div>

                            {/* Housekeeping Statistics */}
                            {housekeepingData?.statistics && (
                                <div className="stats-row" style={{ marginBottom: "1.5rem" }}>
                                    <div className="stat-card beige">
                                        <div className="stat-header">
                                            <div className="stat-label">Pending</div>
                                            <div className="stat-icon beige">⏳</div>
                                        </div>
                                        <div className="stat-value">{housekeepingData.statistics.pending || 0}</div>
                                    </div>
                                    <div className="stat-card blue">
                                        <div className="stat-header">
                                            <div className="stat-label">In Progress</div>
                                            <div className="stat-icon blue">🧹</div>
                                        </div>
                                        <div className="stat-value">{housekeepingData.statistics.in_progress || 0}</div>
                                    </div>
                                    <div className="stat-card green">
                                        <div className="stat-header">
                                            <div className="stat-label">Completed</div>
                                            <div className="stat-icon green">✅</div>
                                        </div>
                                        <div className="stat-value">{housekeepingData.statistics.completed || 0}</div>
                                    </div>
                                    <div className="stat-card gold">
                                        <div className="stat-header">
                                            <div className="stat-label">Today</div>
                                            <div className="stat-icon gold">📅</div>
                                        </div>
                                        <div className="stat-value">{housekeepingData.statistics.today || 0}</div>
                                    </div>
                                </div>
                            )}

                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Room</th>
                                            <th>Cleaner</th>
                                            <th>Status</th>
                                            <th>Started</th>
                                            <th>Completed</th>
                                            <th>Notes</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {housekeepingData?.tasks?.map((task, idx) => (
                                            <tr key={task.id || idx}>
                                                <td>{task.room_number}</td>
                                                <td>{task.cleaner_name || "Unassigned"}</td>
                                                <td><span className={`status-badge status-${task.status}`}>{task.status}</span></td>
                                                <td>{task.started_at ? new Date(task.started_at).toLocaleString() : "-"}</td>
                                                <td>{task.completed_at ? new Date(task.completed_at).toLocaleString() : "-"}</td>
                                                <td>{task.notes || "-"}</td>
                                                <td>
                                                    {task.status === "pending" && (
                                                        <button className="btn-small" onClick={() => {
                                                            adminFetch(`/admin/housekeeping/tasks/${task.id}/start`, {
                                                                method: "PUT",
                                                                headers: { "Content-Type": "application/json" },
                                                                body: JSON.stringify({})
                                                            }).then(() => fetchHousekeeping());
                                                        }}>Start</button>
                                                    )}
                                                    {task.status === "in_progress" && (
                                                        <button className="btn-small" onClick={() => {
                                                            adminFetch(`/admin/housekeeping/tasks/${task.id}/complete`, {
                                                                method: "PUT",
                                                                headers: { "Content-Type": "application/json" },
                                                                body: JSON.stringify({ notes: "" })
                                                            }).then(() => fetchHousekeeping());
                                                        }}>Complete</button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                        {(!housekeepingData?.tasks || housekeepingData.tasks.length === 0) && (
                                            <tr><td colSpan="7" style={{ textAlign: "center" }}>No housekeeping tasks found.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            <div className="pagination">
                                <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous</button>
                                <span>Page {page + 1} (Total: {housekeepingData?.total || 0})</span>
                                <button disabled={!housekeepingData?.tasks || housekeepingData.tasks.length < LIMIT} onClick={() => setPage(p => p + 1)}>Next</button>
                            </div>
                        </div>
                    </>
                )}

                {/* TAB: PROPERTIES (Pause/Resume Control) */}
                {activeTab === "properties" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>Properties Control</h2>
                                <p>Manage property availability in the marketplace</p>
                            </div>
                        </div>

                        <div className="properties-layout">
                            {/* Left: Admin Properties Table */}
                            <div className="properties-panel">
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                                    <h3>Registered Properties</h3>
                                    <button className="btn-primary" onClick={fetchProperties}>🔄 Refresh</button>
                                </div>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Property ID</th>
                                                <th>Name</th>
                                                <th>PMS Type</th>
                                                <th>Tier</th>
                                                <th>Status</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {propertiesData?.properties?.map((property) => (
                                                <tr key={property.property_id}>
                                                    <td>{property.property_id}</td>
                                                    <td>{property.name}</td>
                                                    <td>{property.pms_type}</td>
                                                    <td>{property.tier || "standard"}</td>
                                                    <td>
                                                        <span className={`status-badge status-${property.is_active ? "active" : "paused"}`}>
                                                            {property.is_active ? "✅ Active" : "⏸️ Paused"}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        {property.is_active ? (
                                                            <button
                                                                className="btn-small"
                                                                onClick={() => pauseProperty(property.property_id)}
                                                                style={{ background: "#ef4444" }}
                                                            >
                                                                Pause
                                                            </button>
                                                        ) : (
                                                            <button
                                                                className="btn-small"
                                                                onClick={() => resumeProperty(property.property_id)}
                                                                style={{ background: "#10b981" }}
                                                            >
                                                                Resume
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                            {(!propertiesData?.properties || propertiesData.properties.length === 0) && (
                                                <tr>
                                                    <td colSpan="6" style={{ textAlign: "center", padding: "2rem" }}>
                                                        No properties registered. Register properties via API.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Right: Marketplace Preview */}
                            <div className="marketplace-panel">
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                                    <h3>Marketplace (Public View)</h3>
                                    <button className="btn-primary" onClick={fetchMarketplace}>🔄 Refresh</button>
                                </div>
                                <div className="marketplace-description">
                                    <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "1rem" }}>
                                        This shows what properties are visible to agents in the public marketplace.
                                        Only <strong>Active</strong> properties appear here.
                                    </p>
                                </div>
                                <div className="marketplace-list">
                                    {marketplaceData?.properties?.map((property) => (
                                        <div key={property.property_id} className="marketplace-item">
                                            <div>
                                                <strong>{property.name}</strong>
                                                <div style={{ fontSize: "0.875rem", color: "#666" }}>
                                                    {property.property_id} • {property.tier}
                                                </div>
                                            </div>
                                            <span className="status-badge status-active">Live in Marketplace</span>
                                        </div>
                                    ))}
                                    {(!marketplaceData?.properties || marketplaceData.properties.length === 0) && (
                                        <div style={{ padding: "2rem", textAlign: "center", background: "#f9fafb", borderRadius: "8px" }}>
                                            <p style={{ color: "#666" }}>No properties currently visible in marketplace.</p>
                                            <p style={{ color: "#666", fontSize: "0.875rem", marginTop: "0.5rem" }}>
                                                Resume a paused property to make it appear here.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {/* TAB: USERS */}
                {activeTab === "users" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>User Management</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <p style={{ padding: "2rem", textAlign: "center", color: "#666" }}>
                                User management feature coming soon...
                            </p>
                        </div>
                    </>
                )}

                {/* TAB: SYSTEM HEALTH */}
                {activeTab === "health" && (
                    <>
                        <div className="welcome-section">
                            <div className="welcome-box">
                                <h2>System Health</h2>
                            </div>
                        </div>

                        <div className="content-section">
                            <h2 className="section-title">System Status</h2>
                            <div className="stats-row">
                                <div className="stat-card">
                                    <div className="stat-header">
                                        <div className="stat-label">Database</div>
                                        <div className="stat-icon" style={{ background: healthData?.database === "healthy" ? "#d1fae5" : "#fee2e2", color: healthData?.database === "healthy" ? "#059669" : "#dc2626" }}>
                                            {healthData?.database === "healthy" ? "✅" : "❌"}
                                        </div>
                                    </div>
                                    <div className="stat-value" style={{ fontSize: "1.5rem" }}>
                                        {healthData?.database === "healthy" ? "Healthy" : "Unhealthy"}
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-header">
                                        <div className="stat-label">AI Service</div>
                                        <div className="stat-icon" style={{ background: healthData?.ai_service === "configured" ? "#d1fae5" : "#fef3c7", color: healthData?.ai_service === "configured" ? "#059669" : "#d97706" }}>
                                            {healthData?.ai_service === "configured" ? "✅" : "⚠️"}
                                        </div>
                                    </div>
                                    <div className="stat-value" style={{ fontSize: "1.5rem" }}>
                                        {healthData?.ai_service === "configured" ? "Configured" : "Not Configured"}
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-header">
                                        <div className="stat-label">Queue</div>
                                        <div className="stat-icon" style={{ background: healthData?.redis === "available" ? "#d1fae5" : "#f3f4f6", color: healthData?.redis === "available" ? "#059669" : "#6b7280" }}>
                                            {healthData?.redis === "available" ? "✅" : "➖"}
                                        </div>
                                    </div>
                                    <div className="stat-value" style={{ fontSize: "1.5rem" }}>
                                        {healthData?.redis === "available" ? "Available" : "Unavailable"}
                                    </div>
                                </div>
                            </div>

                            <button className="btn-primary" onClick={fetchHealth} style={{ marginTop: "2rem" }}>Refresh Health</button>

                            {healthData?.recent_errors && healthData.recent_errors.length > 0 && (
                                <div style={{ marginTop: "2rem" }}>
                                    <h3>Recent Errors</h3>
                                    <div className="table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr><th>Time</th><th>Type</th><th>Message</th><th>Endpoint</th></tr>
                                            </thead>
                                            <tbody>
                                                {healthData.recent_errors.slice(0, 10).map((err, idx) => (
                                                    <tr key={idx}>
                                                        <td>{new Date(err.created_at).toLocaleString()}</td>
                                                        <td>{err.error_type}</td>
                                                        <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis" }}>{err.error_message}</td>
                                                        <td>{err.endpoint || "-"}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}

            </main>
        </div>
    );
}
