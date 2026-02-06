# 🏗️ Project Modularization Plan

## 📊 Current State Analysis

### Backend Structure
- **18 Route Files** across API and ACP systems
- **50+ API Endpoints** (estimated)
- **Multiple Modules**: agent, api, db, integrations, payments, queue, rag, services
- **Complex Dependencies**: Cross-module imports, shared utilities

### Frontend Structure
- **12 JSX Components/Pages**
- **Monolithic Components**: AdminPage (1700+ lines), ChatBox, etc.
- **Mixed Concerns**: UI, API calls, state management all in one place

### Key Features Identified
1. **AI Agent System** - Orchestrator, Planner, Tools
2. **RAG System** - Knowledge base, document indexing
3. **Booking System** - Rooms, Restaurants, Events
4. **Payment System** - Stripe integration
5. **Admin Dashboard** - Analytics, monitoring, management
6. **Chat/Conversation** - Guest & Staff assistants
7. **Commerce/Catalog** - Restaurants, menus, events
8. **Authentication** - JWT, admin keys
9. **Queue System** - Background jobs
10. **ACP/Marketplace** - Agent communication protocol

---

## 🎯 Modularization Strategy

### Phase 1: Feature-Based Module Structure

Break the project into **independent feature modules**, each containing:
- Backend routes
- Frontend components
- Database queries
- Business logic
- Tests
- Documentation

### Proposed Module Structure

```
ai-hotel-assistant/
├── modules/
│   ├── auth/                    # Authentication & Authorization
│   │   ├── backend/
│   │   │   ├── routes/
│   │   │   ├── services/
│   │   │   └── schemas/
│   │   ├── frontend/
│   │   │   ├── components/
│   │   │   └── pages/
│   │   └── tests/
│   │
│   ├── chatbot/                 # AI Chat System
│   │   ├── backend/
│   │   │   ├── routes/          # /ask/guest, /ask/staff
│   │   │   ├── agent/           # orchestrator, planner
│   │   │   └── rag/             # RAG service
│   │   ├── frontend/
│   │   │   ├── components/      # ChatBox, ChatWidget
│   │   │   └── hooks/           # useChat, useAgent
│   │   └── tests/
│   │
│   ├── booking/                 # Room Booking System
│   │   ├── backend/
│   │   │   ├── routes/          # Room booking endpoints
│   │   │   ├── services/        # Booking logic
│   │   │   └── integrations/   # MockRoomProvider
│   │   ├── frontend/
│   │   │   ├── components/      # BookingForm, RoomSelector
│   │   │   └── pages/           # BookingPage
│   │   └── tests/
│   │
│   ├── commerce/                # Restaurant & Event Booking
│   │   ├── backend/
│   │   │   ├── routes/          # /catalog/*, /admin/commerce/*
│   │   │   └── services/        # Commerce logic
│   │   ├── frontend/
│   │   │   └── components/      # RestaurantCard, EventCard
│   │   └── tests/
│   │
│   ├── payments/                # Payment Processing
│   │   ├── backend/
│   │   │   ├── routes/          # /payments/*
│   │   │   └── providers/      # StripeProvider
│   │   ├── frontend/
│   │   │   └── components/      # CheckoutForm
│   │   └── tests/
│   │
│   ├── admin/                   # Admin Dashboard
│   │   ├── backend/
│   │   │   ├── routes/          # /admin/*
│   │   │   └── services/        # Analytics, monitoring
│   │   ├── frontend/
│   │   │   ├── components/      # AdminPage (split into smaller components)
│   │   │   └── pages/           # Dashboard, Analytics, etc.
│   │   └── tests/
│   │
│   ├── rooms/                   # Room Management
│   │   ├── backend/
│   │   │   ├── routes/          # /admin/rooms/*
│   │   │   └── queries/         # Room queries
│   │   ├── frontend/
│   │   │   └── components/      # RoomList, RoomCard
│   │   └── tests/
│   │
│   ├── housekeeping/            # Housekeeping Management
│   │   ├── backend/
│   │   │   ├── routes/          # /admin/housekeeping/*
│   │   │   └── services/        # Task management
│   │   ├── frontend/
│   │   │   └── components/      # TaskList, TaskCard
│   │   └── tests/
│   │
│   └── knowledge-base/         # RAG & Document Management
│       ├── backend/
│       │   ├── routes/          # /admin/kb/*
│       │   └── services/        # Indexing, search
│       ├── frontend/
│       │   └── components/      # DocumentUpload, SearchResults
│       └── tests/
│
├── shared/                      # Shared Utilities
│   ├── backend/
│   │   ├── db/                  # Database connection, base queries
│   │   ├── core/               # Security, config, logging
│   │   └── utils/              # Common utilities
│   ├── frontend/
│   │   ├── api/                # API client, interceptors
│   │   ├── hooks/              # useAuth, useApi
│   │   └── utils/              # Common utilities
│   └── types/                  # Shared TypeScript types
│
└── main/                       # Main Application Entry Points
    ├── backend/
    │   ├── main.py             # FastAPI app initialization
    │   └── app_factory.py      # App factory
    └── frontend/
        ├── App.jsx             # Main React app
        └── main.jsx            # Entry point
```

---

## 📋 Module Breakdown Details

### 1. **auth/** - Authentication & Authorization
**Backend:**
- `routes/auth.py` → `auth/backend/routes/auth.py`
- `core/security/*` → `auth/backend/security/`
- `schemas/auth.py` → `auth/backend/schemas/`

**Frontend:**
- `components/Login.jsx` → `auth/frontend/components/Login.jsx`
- Auth hooks → `auth/frontend/hooks/useAuth.js`

**Endpoints:** `/auth/register`, `/auth/login`

---

### 2. **chatbot/** - AI Chat System
**Backend:**
- `routes/ask.py` → `chatbot/backend/routes/ask.py`
- `routes/agent.py` → `chatbot/backend/routes/agent.py`
- `agent/orchestrator.py` → `chatbot/backend/agent/orchestrator.py`
- `agent/planner/` → `chatbot/backend/agent/planner/`
- `agent/tools.py` → `chatbot/backend/agent/tools.py`
- `services/rag_service.py` → `chatbot/backend/services/rag_service.py`

**Frontend:**
- `components/ChatBox.jsx` → `chatbot/frontend/components/ChatBox.jsx`
- `components/ChatWidget.jsx` → `chatbot/frontend/components/ChatWidget.jsx`
- Chat hooks → `chatbot/frontend/hooks/useChat.js`

**Endpoints:** `/ask/guest`, `/ask/staff`, `/ask/agent`, `/ask/agent/confirm`

---

### 3. **booking/** - Room Booking System
**Backend:**
- Room booking logic from `routes/admin_rooms.py` → `booking/backend/routes/bookings.py`
- `integrations/mock_room.py` → `booking/backend/integrations/mock_room.py`
- `db/room_queries.py` → `booking/backend/queries/room_queries.py`

**Frontend:**
- Booking components from `components/ToolPages.jsx` → `booking/frontend/components/`
- `pages/` booking pages → `booking/frontend/pages/`

**Endpoints:** `/admin/reservations/*`, booking-related endpoints

---

### 4. **commerce/** - Restaurant & Event Booking
**Backend:**
- `routes/catalog.py` → `commerce/backend/routes/catalog.py`
- `routes/admin_commerce.py` → `commerce/backend/routes/admin_commerce.py`
- `integrations/mock_dining.py` → `commerce/backend/integrations/mock_dining.py`
- `integrations/mock_event.py` → `commerce/backend/integrations/mock_event.py`

**Frontend:**
- Commerce components → `commerce/frontend/components/`

**Endpoints:** `/catalog/*`, `/admin/commerce/*`, `/admin/restaurants/*`, `/admin/events/*`

---

### 5. **payments/** - Payment Processing
**Backend:**
- `routes/payments.py` → `payments/backend/routes/payments.py`
- `payments/stripe_provider.py` → `payments/backend/providers/stripe_provider.py`
- `payments/payment_service.py` → `payments/backend/services/payment_service.py`

**Frontend:**
- Payment components → `payments/frontend/components/`

**Endpoints:** `/payments/checkout/*`, `/payments/webhook/stripe`

---

### 6. **admin/** - Admin Dashboard
**Backend:**
- `routes/admin_analytics.py` → `admin/backend/routes/analytics.py`
- `routes/admin_monitoring.py` → `admin/backend/routes/monitoring.py`
- `routes/admin_kb.py` → `admin/backend/routes/knowledge_base.py`
- `routes/admin_jobs.py` → `admin/backend/routes/jobs.py`

**Frontend:**
- `components/AdminPage.jsx` → **SPLIT INTO:**
  - `admin/frontend/components/Dashboard.jsx`
  - `admin/frontend/components/Analytics.jsx`
  - `admin/frontend/components/Chats.jsx`
  - `admin/frontend/components/Payments.jsx`
  - `admin/frontend/components/SystemHealth.jsx`
  - `admin/frontend/components/KnowledgeBase.jsx`
  - `admin/frontend/components/Properties.jsx`

**Endpoints:** `/admin/*` (all admin endpoints)

---

### 7. **rooms/** - Room Management
**Backend:**
- Room management from `routes/admin_rooms.py` → `rooms/backend/routes/rooms.py`
- `db/room_queries.py` → `rooms/backend/queries/room_queries.py`

**Frontend:**
- Room management components → `rooms/frontend/components/`

**Endpoints:** `/admin/rooms/*`

---

### 8. **housekeeping/** - Housekeeping Management
**Backend:**
- Housekeeping from `routes/admin_rooms.py` → `housekeeping/backend/routes/tasks.py`

**Frontend:**
- Housekeeping components → `housekeeping/frontend/components/`

**Endpoints:** `/admin/housekeeping/*`

---

### 9. **knowledge-base/** - RAG & Document Management
**Backend:**
- Knowledge base routes → `knowledge-base/backend/routes/`
- RAG services → `knowledge-base/backend/services/`

**Frontend:**
- Document management components → `knowledge-base/frontend/components/`

**Endpoints:** `/admin/reindex`, `/admin/upload`, `/admin/files/*`

---

## 🔄 Migration Strategy

### Step 1: Create Module Structure (Week 1)
1. Create `modules/` directory structure
2. Create `shared/` directory for common code
3. Set up module templates

### Step 2: Extract First Module - Auth (Week 1-2)
1. Move auth-related code
2. Update imports
3. Test auth module independently
4. Update main app to use auth module

### Step 3: Extract Chatbot Module (Week 2-3)
1. Move chatbot code
2. Split AdminPage into smaller components
3. Test chatbot independently

### Step 4: Extract Booking Module (Week 3-4)
1. Move booking code
2. Extract room queries
3. Test booking flow

### Step 5: Extract Remaining Modules (Week 4-6)
1. Commerce
2. Payments
3. Admin (split into sub-modules)
4. Rooms
5. Housekeeping
6. Knowledge Base

### Step 6: Refactor Shared Code (Week 6-7)
1. Move common utilities to `shared/`
2. Create shared API client
3. Create shared hooks

### Step 7: Testing & Documentation (Week 7-8)
1. Test each module independently
2. Integration testing
3. Update documentation
4. Create module READMEs

---

## 📦 Module Interface Standards

Each module should have:

### Backend Structure
```
module_name/
├── backend/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── module_routes.py
│   ├── services/
│   │   └── module_service.py
│   ├── schemas/
│   │   └── module_schemas.py
│   └── README.md
```

### Frontend Structure
```
module_name/
├── frontend/
│   ├── components/
│   │   └── ModuleComponent.jsx
│   ├── pages/
│   │   └── ModulePage.jsx
│   ├── hooks/
│   │   └── useModule.js
│   ├── api/
│   │   └── moduleApi.js
│   └── README.md
```

### Module Registration
Each module should register itself in `main.py`:

```python
# main.py
from modules.auth.backend.routes import router as auth_router
from modules.chatbot.backend.routes import router as chatbot_router
# ... etc

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chatbot_router, prefix="/ask", tags=["chatbot"])
```

---

## 🎯 Benefits of This Structure

1. **Isolated Testing**: Test each module independently
2. **Easier Debugging**: Know exactly where to look for issues
3. **Better Organization**: Related code is grouped together
4. **Scalability**: Easy to add new modules
5. **Team Collaboration**: Different developers can work on different modules
6. **Reusability**: Modules can be reused in other projects
7. **Clear Dependencies**: Easy to see what depends on what

---

## 🚀 Next Steps

1. **Review this plan** - Make sure it aligns with your vision
2. **Prioritize modules** - Which module should we start with?
3. **Create module templates** - Set up the structure
4. **Start migration** - Begin with the first module
5. **Test as we go** - Ensure nothing breaks

---

## 📝 Module Dependency Map

```
auth (no dependencies)
  ↓
chatbot → auth, knowledge-base
  ↓
booking → auth, rooms
  ↓
commerce → auth, payments
  ↓
payments → auth
  ↓
admin → auth, chatbot, booking, commerce, payments, rooms, housekeeping
  ↓
rooms → auth
  ↓
housekeeping → auth, rooms
  ↓
knowledge-base → auth
```

---

## ✅ Success Criteria

- [ ] Each module can be tested independently
- [ ] Each module has clear boundaries
- [ ] Frontend components are split into manageable sizes (< 500 lines)
- [ ] Backend routes are organized by feature
- [ ] Documentation exists for each module
- [ ] No circular dependencies
- [ ] Easy to add new features

---

**Ready to start? Let's begin with the first module!**
