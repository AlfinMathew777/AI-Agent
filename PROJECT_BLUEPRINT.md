# AI Hotel Assistant - Project Blueprint

## 📋 Project Overview
This is a full-stack AI-powered hotel assistant application built with:
- **Backend**: FastAPI + Python + RAG (Retrieval-Augmented Generation)
- **Frontend**: React + Vite
- **Database**: SQLite (hotel.db) + ChromaDB (vector storage)
- **AI**: Google Gemini API with MCP integration

---

## 🗂️ Complete Folder Structure

```
ai-hotel-assistant/
│
├── 📁 backend/                          # FastAPI Backend Server
│   ├── 📁 app/                          # Main application package
│   │   ├── 📁 agent/                    # AI Agent orchestration
│   │   │   ├── guardrails.py           # Safety & content filtering
│   │   │   ├── orchestrator.py         # Main agent logic
│   │   │   ├── router.py               # Route handling
│   │   │   ├── schemas.py              # Pydantic models
│   │   │   └── tools.py                # Agent tools (booking, FAQ, etc.)
│   │   │
│   │   ├── 📁 data/                     # Knowledge base documents
│   │   │   ├── 📁 guest/               # Guest-facing information
│   │   │   │   ├── Guest_Compendium_General_Info_v1.md
│   │   │   │   ├── Guest_Dining_Breakfast_RoomService_v1.md
│   │   │   │   ├── Guest_FAQ_General_v1.md
│   │   │   │   ├── Guest_Facilities_Services_v1.md
│   │   │   │   ├── Guest_Local_Area_Attractions_v1.md
│   │   │   │   ├── casino_entertainment.md
│   │   │   │   ├── dining_guide.md
│   │   │   │   ├── events_calendar.md
│   │   │   │   ├── hobart_secrets.md
│   │   │   │   └── transport_services.md
│   │   │   │
│   │   │   └── 📁 staff/               # Staff-facing SOPs
│   │   │       ├── Guide_WHS_Safety_Hotel_Staff_v1.md
│   │   │       ├── SOP_Complaints_Service_Recovery_v1.md
│   │   │       ├── SOP_Front_Office_Checkin_Checkout_v1.md
│   │   │       ├── SOP_Housekeeping_Room_Cleaning_v1.md
│   │   │       └── Training_Service_Standards_Front_of_House_v1.md
│   │   │
│   │   ├── 📁 models/                   # Database models
│   │   │   └── database.py             # SQLAlchemy ORM models
│   │   │
│   │   ├── 📁 routers/                  # API route handlers
│   │   │   ├── admin.py                # Admin endpoints (bookings, stats)
│   │   │   ├── chat.py                 # Chat endpoints
│   │   │   └── health.py               # Health check endpoints
│   │   │
│   │   ├── ai_service.py               # AI service wrapper
│   │   ├── config.py                   # Configuration settings
│   │   ├── database.py                 # Database connection & setup
│   │   ├── knowledge.py                # Knowledge base management
│   │   ├── llm.py                      # LLM integration (Gemini)
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── mcp_client.py               # MCP (Model Context Protocol) client
│   │   └── rag_loader.py               # RAG document loader
│   │
│   ├── 📁 chroma_db/                    # Vector database storage
│   │   └── (ChromaDB files)
│   │
│   ├── 📁 venv/                         # Python virtual environment
│   │   └── (virtual environment files)
│   │
│   ├── .env                            # Environment variables (API keys)
│   ├── hotel.db                        # SQLite database
│   ├── requirements.txt                # Python dependencies
│   ├── TESTING.md                      # Testing documentation
│   │
│   └── 📄 Test Scripts/
│       ├── check_health.py
│       ├── debug_500.py
│       ├── debug_http_500.py
│       ├── debug_startup.py
│       ├── hotel_ops_server.py
│       ├── list_models.py
│       ├── list_models_check.py
│       ├── reindex.py
│       ├── reproduce_issue.py
│       ├── test_analytics.py
│       ├── test_api_key.py
│       ├── test_chat_endpoint.py
│       ├── test_database.py
│       ├── test_endpoint.py
│       ├── test_general_chat.py
│       ├── test_mcp_connection.py
│       └── run_tests.ps1
│
├── 📁 frontend/                         # React Frontend Application
│   ├── 📁 public/                       # Static assets
│   │   └── vite.svg
│   │
│   ├── 📁 src/                          # Source code
│   │   ├── 📁 assets/                   # Images & icons
│   │   │   └── react.svg
│   │   │
│   │   ├── 📁 components/              # React components
│   │   │   ├── AdminPage.jsx           # Admin dashboard
│   │   │   ├── AdminPage.css
│   │   │   ├── ChatBox.jsx             # Chat interface
│   │   │   ├── ChatBox.css
│   │   │   ├── ChatWidget.jsx          # Chat widget
│   │   │   ├── ChatWidget.css
│   │   │   ├── LandingPage.jsx         # Home/Landing page
│   │   │   ├── LandingPage.css
│   │   │   ├── Login.jsx               # Login component
│   │   │   └── ToolPages.jsx           # Tool pages
│   │   │
│   │   ├── 📁 pages/                    # Page components
│   │   │   ├── Guest.jsx               # Guest chat page
│   │   │   ├── Home.jsx                # Home page
│   │   │   └── Staff.jsx               # Staff chat page
│   │   │
│   │   ├── App.jsx                     # Main App component
│   │   ├── App.css                     # App styles
│   │   ├── main.jsx                    # Entry point
│   │   └── index.css                   # Global styles
│   │
│   ├── 📁 node_modules/                # NPM dependencies
│   │   └── (npm packages)
│   │
│   ├── eslint.config.js                # ESLint configuration
│   ├── index.html                      # HTML entry point
│   ├── package.json                    # NPM dependencies
│   ├── package-lock.json              # NPM lock file
│   ├── vite.config.js                 # Vite configuration
│   └── README.md                       # Frontend documentation
│
├── 📁 chroma_db/                        # Shared ChromaDB storage
│   └── (vector database files)
│
├── 📄 Project Documentation/
│   ├── INTELLIGENT_CHATBOT.md          # Chatbot documentation
│   ├── TECHNICAL_DEEP_DIVE_VERIFICATION_REPORT.md
│   ├── audit_verification.py
│   ├── check_db_status.py
│   └── test_upload.md
│
└── 📄 Startup Scripts/
    ├── START_BACKEND.bat               # Windows batch file to start backend
    └── START_FRONTEND.bat              # Windows batch file to start frontend
```

---

## 🏗️ Architecture Overview

### Backend (Port 8002)
```
FastAPI Application
├── Main Entry: app/main.py
├── Endpoints:
│   ├── /ask/guest - Guest chat endpoint
│   ├── /ask/staff - Staff chat endpoint
│   ├── /admin/bookings - Get bookings
│   ├── /admin/tool-stats - Get tool usage stats
│   ├── /admin/index-status - Get index status
│   ├── /admin/reindex - Trigger reindexing
│   └── /health - Health check
│
├── AI Agent Pipeline:
│   ├── orchestrator.py - Orchestrates agent flow
│   ├── router.py - Routes to correct tools
│   ├── guardrails.py - Safety checks
│   └── tools.py - Agent tools (booking, FAQ, etc.)
│
├── Data Layer:
│   ├── hotel.db (SQLite) - Bookings, rooms, guests
│   └── chroma_db (Vector Store) - RAG documents
│
└── AI Integration:
    ├── llm.py - Gemini API wrapper
    ├── mcp_client.py - MCP integration
    └── rag_loader.py - Document ingestion
```

### Frontend (Port 5173)
```
React + Vite Application
├── Main Entry: src/main.jsx
├── Pages:
│   ├── Home.jsx - Landing page
│   ├── Guest.jsx - Guest chat interface
│   ├── Staff.jsx - Staff chat interface
│   └── AdminPage.jsx - Admin dashboard
│
├── Components:
│   ├── LandingPage.jsx - Hero section
│   ├── ChatBox.jsx - Main chat UI
│   ├── ChatWidget.jsx - Chat widget component
│   └── Login.jsx - Authentication
│
└── Routing:
    └── App.jsx - Main router & layout
```

---

## 🚀 How to Run

### Backend
```bash
cd backend
call venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```
Or double-click: `START_BACKEND.bat`

### Frontend
```bash
cd frontend
npm run dev
```
Or double-click: `START_FRONTEND.bat`

### Access Points
- Frontend: http://localhost:5173/
- Backend API: http://localhost:8002/
- API Docs: http://localhost:8002/docs

---

## 📦 Key Dependencies

### Backend (requirements.txt)
- fastapi
- uvicorn
- sqlalchemy
- chromadb
- google-generativeai
- pydantic
- python-dotenv

### Frontend (package.json)
- react ^19.2.0
- react-dom ^19.2.0
- vite ^5.1.0
- eslint

---

## 🔑 Environment Variables (.env)
```
GEMINI_API_KEY=your_api_key_here
ADMIN_KEY=your_admin_key_here
```

---

## 📊 Features

### Guest Features
- AI-powered chat for hotel inquiries
- Information about facilities, dining, attractions
- Event calendar and local recommendations

### Staff Features
- SOP (Standard Operating Procedures) access
- Housekeeping guidelines
- Front office procedures
- Safety protocols

### Admin Features
- Bookings management with filters
- Tool usage analytics
- Index status monitoring
- Reindexing controls

---

## 🗄️ Database Schema

### SQLite (hotel.db)
- **bookings** - Guest reservations
- **rooms** - Room inventory
- **guests** - Guest information

### ChromaDB (Vector Store)
- Guest knowledge documents
- Staff SOP documents
- Embeddings for semantic search

---

## 🧪 Testing
Run backend tests:
```bash
cd backend
.\run_tests.ps1
```

Individual test scripts available in `backend/` directory.

---

**Last Updated**: January 2026
**Status**: ✅ Fully Operational
