import { useState } from "react";
import ChatBox from "./ChatBox";
import "./ChatWidget.css";

export default function ChatWidget({ onNavigate }) {
    const [isOpen, setIsOpen] = useState(false);
    const [isFullPage, setIsFullPage] = useState(false);

    // Toggle full page mode
    const toggleFullPage = () => setIsFullPage(!isFullPage);

    // Handle tool click: Close sidebar AND Navigate
    const handleToolClick = (page) => {
        setIsOpen(false);
        if (onNavigate) {
            onNavigate(page);
        }
    };

    return (
        <>
            {/* 1. Floating Action Button */}
            {!isOpen && (
                <button
                    className="chat-fab"
                    onClick={() => setIsOpen(true)}
                >
                    <span className="fab-icon">✨</span>
                </button>
            )}

            {/* 2. The Sidebar (Monica Layer) */}
            <div className={`chat-sidebar ${isOpen ? "open" : ""} ${isFullPage ? "full-page" : ""}`}>

                {/* Header: Welcome & Close */}
                <div className="sidebar-header">
                    <div className="header-title">
                        <h2>Welcome 👋</h2>
                    </div>
                    <div className="header-actions">
                        <button className="icon-btn" onClick={toggleFullPage} title="Expand/Collapse">
                            {isFullPage ? "↙️" : "↗️"}
                        </button>
                        <button className="icon-btn close-btn" onClick={() => setIsOpen(false)}>×</button>
                    </div>
                </div>

                {/* Tools Grid */}
                <div className="monica-tools">
                    <div className="tools-label">Tools <span className="more-link">More {">"}</span></div>
                    <div className="tools-grid">
                        <button className="tool-item" onClick={() => handleToolClick('book')}>
                            <span className="tool-icon">📅</span>
                            <span className="tool-name">Book</span>
                        </button>
                        <button className="tool-item" onClick={() => handleToolClick('guide')}>
                            <span className="tool-icon">🗺️</span>
                            <span className="tool-name">Guide</span>
                        </button>
                        <button className="tool-item" onClick={() => handleToolClick('wifi')}>
                            <span className="tool-icon">📶</span>
                            <span className="tool-name">WiFi</span>
                        </button>
                        <button className="tool-item" onClick={() => handleToolClick('reception')}>
                            <span className="tool-icon">🛎️</span>
                            <span className="tool-name">Reception</span>
                        </button>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="sidebar-content">
                    <ChatBox endpoint="/api/ask/agent" />
                </div>
            </div>

            {/* 3. Backdrop */}
            {isOpen && <div className="backdrop" onClick={() => setIsOpen(false)} />}
        </>
    );
}
