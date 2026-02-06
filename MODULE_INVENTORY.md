# 📊 Module Inventory & Endpoint Mapping

## Backend API Endpoints by Feature

### 🔐 Authentication (`/auth/*`)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- **Files:** `backend/app/api/routes/auth.py`
- **Dependencies:** `core/security/`, `schemas/auth.py`

---

### 💬 Chatbot (`/ask/*`)
- `POST /ask/guest` - Guest questions
- `POST /ask/staff` - Staff questions  
- `POST /ask/agent` - AI agent requests
- `POST /ask/agent/confirm` - Confirm agent actions
- **Files:** 
  - `backend/app/api/routes/ask.py`
  - `backend/app/api/routes/agent.py`
  - `backend/app/agent/orchestrator.py`
  - `backend/app/agent/planner/`
  - `backend/app/agent/tools.py`
- **Dependencies:** RAG service, LLM service, tools registry

---

### 🏨 Booking (`/admin/reservations/*`)
- `POST /admin/reservations` - Create reservation
- `GET /admin/reservations` - List reservations
- `PUT /admin/reservations/{id}/checkin` - Check-in
- `PUT /admin/reservations/{id}/checkout` - Check-out
- **Files:**
  - `backend/app/api/routes/admin_rooms.py` (reservation endpoints)
  - `backend/app/integrations/mock_room.py`
  - `backend/app/db/room_queries.py`
- **Dependencies:** Rooms module, payment module

---

### 🍽️ Commerce (`/catalog/*`, `/admin/commerce/*`)
- `GET /catalog/restaurants` - List restaurants
- `GET /catalog/restaurants/{id}/menus` - Get restaurant menus
- `GET /catalog/menus/{id}/items` - Get menu items
- `GET /catalog/events` - List events
- `POST /admin/commerce/seed` - Seed commerce data
- `GET /admin/restaurants` - Admin: List restaurants
- `POST /admin/restaurants` - Admin: Create restaurant
- `GET /admin/restaurants/{id}/menus` - Admin: Get menus
- `POST /admin/menu_items` - Admin: Create menu item
- `GET /admin/events` - Admin: List events
- `POST /admin/events` - Admin: Create event
- `GET /admin/restaurant-bookings` - Restaurant bookings
- `GET /admin/event-bookings` - Event bookings
- `GET /admin/quotes` - Get quotes
- **Files:**
  - `backend/app/api/routes/catalog.py`
  - `backend/app/api/routes/admin_commerce.py`
  - `backend/app/integrations/mock_dining.py`
  - `backend/app/integrations/mock_event.py`
- **Dependencies:** Payment module

---

### 💳 Payments (`/payments/*`)
- `POST /payments/checkout/{quote_id}` - Create checkout session
- `POST /payments/webhook/stripe` - Stripe webhook handler
- **Files:**
  - `backend/app/api/routes/payments.py`
  - `backend/app/payments/stripe_provider.py`
  - `backend/app/payments/payment_service.py`
- **Dependencies:** Commerce module, booking module

---

### 👨‍💼 Admin Dashboard (`/admin/*`)
- `GET /admin/analytics` - Analytics data
- `GET /admin/bookings` - List bookings
- `GET /admin/tools/stats` - Tool usage stats
- `GET /admin/chats` - Chat history
- `GET /admin/chats/thread` - Get chat thread
- `GET /admin/operations` - Operations summary
- `GET /admin/payments` - Payment transactions
- `GET /admin/receipts` - Receipts list
- `GET /admin/system/status` - System health
- `GET /admin/jobs` - Background jobs
- `GET /admin/jobs/{id}` - Get job details
- **Files:**
  - `backend/app/api/routes/admin_analytics.py`
  - `backend/app/api/routes/admin_monitoring.py`
  - `backend/app/api/routes/admin_jobs.py`
- **Dependencies:** All other modules

---

### 🛏️ Rooms (`/admin/rooms/*`)
- `POST /admin/rooms` - Create room
- `GET /admin/rooms` - List rooms
- `GET /admin/rooms/statistics` - Room statistics
- `PUT /admin/rooms/{id}/status` - Update room status
- **Files:**
  - `backend/app/api/routes/admin_rooms.py` (room endpoints)
  - `backend/app/db/room_queries.py`
- **Dependencies:** None (base module)

---

### 🧹 Housekeeping (`/admin/housekeeping/*`)
- `POST /admin/housekeeping/tasks` - Create task
- `GET /admin/housekeeping/tasks` - List tasks
- `PUT /admin/housekeeping/tasks/{id}/start` - Start task
- `PUT /admin/housekeeping/tasks/{id}/complete` - Complete task
- `GET /admin/housekeeping/statistics` - Statistics
- **Files:**
  - `backend/app/api/routes/admin_rooms.py` (housekeeping endpoints)
- **Dependencies:** Rooms module

---

### 📚 Knowledge Base (`/admin/reindex`, `/admin/upload`, `/admin/files/*`)
- `POST /admin/reindex` - Reindex knowledge base
- `GET /admin/index/status` - Index status
- `POST /admin/upload` - Upload document
- `GET /admin/files` - List files
- `DELETE /admin/files/{audience}/{filename}` - Delete file
- **Files:**
  - `backend/app/api/routes/admin_kb.py`
  - `backend/app/services/rag_service.py`
- **Dependencies:** RAG system

---

### 🏥 Health (`/health/*`)
- `GET /health` - Health check
- `GET /health/database` - Database health
- `GET /health/ai` - AI service health
- **Files:**
  - `backend/app/api/routes/health.py`
- **Dependencies:** Database, AI service

---

### 🌐 ACP/Marketplace (`/acp/*`, `/marketplace/*`)
- `GET /marketplace/properties` - List properties
- `GET /marketplace/agents` - List agents
- `POST /acp/submit` - Submit ACP request
- **Files:**
  - `backend/app/acp/api/routes/marketplace.py`
  - `backend/app/acp/api/routes/agents.py`
  - `backend/app/acp/api/routes/properties.py`
- **Dependencies:** Properties registry

---

## Frontend Components by Feature

### 🔐 Authentication
- `components/Login.jsx` - Login form
- **Pages:** None (modal/component)

---

### 💬 Chatbot
- `components/ChatBox.jsx` - Main chat interface (1700+ lines - NEEDS SPLITTING)
- `components/ChatWidget.jsx` - Floating chat widget
- **Pages:** 
  - `pages/Guest.jsx` - Guest assistant page
  - `pages/Staff.jsx` - Staff assistant page

---

### 🏨 Booking
- `components/ToolPages.jsx` - Contains booking forms (NEEDS SPLITTING)
- **Pages:** Booking-related pages

---

### 🍽️ Commerce
- Commerce components (embedded in various pages)
- **Pages:** Restaurant/Event pages

---

### 👨‍💼 Admin Dashboard
- `components/AdminPage.jsx` - **1700+ LINES - CRITICAL SPLIT NEEDED**
  - Should split into:
    - `Dashboard.jsx` - Overview
    - `Analytics.jsx` - Analytics tab
    - `Chats.jsx` - Chats tab
    - `Payments.jsx` - Payments tab
    - `Rooms.jsx` - Rooms tab
    - `Reservations.jsx` - Reservations tab
    - `Housekeeping.jsx` - Housekeeping tab
    - `Properties.jsx` - Properties tab
    - `SystemHealth.jsx` - System health tab
    - `KnowledgeBase.jsx` - Knowledge base tab

---

### 🏠 Landing/Home
- `components/LandingPage.jsx` - Landing page
- `pages/Home.jsx` - Home page
- `components/ToolPages.jsx` - Tool pages

---

## Code Statistics

### Backend
- **18 Route Files**
- **50+ API Endpoints**
- **~180 Python Files**
- **Multiple Services:** RAG, LLM, Payment, Queue

### Frontend
- **12 JSX Files**
- **6 CSS Files**
- **Large Components:**
  - `AdminPage.jsx` - 1700+ lines ⚠️
  - `ChatBox.jsx` - Large ⚠️
  - `ToolPages.jsx` - Mixed concerns ⚠️

---

## Critical Issues to Address

1. **AdminPage.jsx** - 1700+ lines, needs splitting into 10+ components
2. **ChatBox.jsx** - Large file, needs refactoring
3. **ToolPages.jsx** - Mixed concerns, needs splitting
4. **Cross-module dependencies** - Need to identify and document
5. **Shared code** - Need to extract common utilities
6. **API client** - Need centralized API client
7. **State management** - Need better state management strategy

---

## Module Priority Order

1. **auth/** - Foundation, no dependencies
2. **chatbot/** - Core feature, depends on auth
3. **rooms/** - Base for booking
4. **booking/** - Depends on rooms
5. **commerce/** - Standalone feature
6. **payments/** - Depends on commerce/booking
7. **admin/** - Depends on all modules
8. **housekeeping/** - Depends on rooms
9. **knowledge-base/** - Standalone feature

---

## Next Steps

1. ✅ Create module structure
2. ✅ Start with auth module
3. ✅ Split AdminPage.jsx
4. ✅ Extract shared code
5. ✅ Test each module independently
