# 🚀 Modularization Execution Plan

## Phase 1: Preparation (Day 1-2)

### Step 1.1: Create Directory Structure
```bash
mkdir -p modules/{auth,chatbot,booking,commerce,payments,admin,rooms,housekeeping,knowledge-base}/{backend/{routes,services,schemas},frontend/{components,pages,hooks,api},tests}
mkdir -p shared/{backend/{db,core,utils},frontend/{api,hooks,utils},types}
```

### Step 1.2: Create Module Templates
Each module gets:
- `README.md` - Module documentation
- `__init__.py` - Python module initialization
- `.gitkeep` - Keep empty directories in git

### Step 1.3: Set Up Module Registration System
Create `modules/__init__.py` with module registry

---

## Phase 2: Extract Auth Module (Day 3-5)

### Step 2.1: Move Backend Code
```bash
# Move auth routes
mv backend/app/api/routes/auth.py modules/auth/backend/routes/auth.py

# Move security code
mv backend/app/core/security/* modules/auth/backend/security/

# Move auth schemas
mv backend/app/schemas/auth.py modules/auth/backend/schemas/auth.py
```

### Step 2.2: Update Imports
- Update all imports in moved files
- Update main.py to import from new location
- Test auth endpoints

### Step 2.3: Move Frontend Code
```bash
# Move login component
mv frontend/src/components/Login.jsx modules/auth/frontend/components/Login.jsx
```

### Step 2.4: Create Auth Hooks
Create `modules/auth/frontend/hooks/useAuth.js`

### Step 2.5: Test Auth Module
- Test login/register endpoints
- Test frontend login flow
- Verify no broken imports

**Success Criteria:**
- ✅ Auth endpoints work
- ✅ Login page works
- ✅ No import errors

---

## Phase 3: Extract Chatbot Module (Day 6-10)

### Step 3.1: Move Backend Code
```bash
# Move ask routes
mv backend/app/api/routes/ask.py modules/chatbot/backend/routes/ask.py
mv backend/app/api/routes/agent.py modules/chatbot/backend/routes/agent.py

# Move agent code
mv backend/app/agent/* modules/chatbot/backend/agent/

# Move RAG service
mv backend/app/services/rag_service.py modules/chatbot/backend/services/rag_service.py
```

### Step 3.2: Split ChatBox Component
**Current:** `ChatBox.jsx` (large file)
**Split into:**
- `ChatBox.jsx` - Main container
- `MessageList.jsx` - Message display
- `MessageInput.jsx` - Input form
- `AgentStatus.jsx` - Agent status indicator
- `hooks/useChat.js` - Chat logic hook
- `hooks/useAgent.js` - Agent logic hook

### Step 3.3: Move Frontend Components
```bash
mv frontend/src/components/ChatBox.jsx modules/chatbot/frontend/components/ChatBox.jsx
mv frontend/src/components/ChatWidget.jsx modules/chatbot/frontend/components/ChatWidget.jsx
mv frontend/src/pages/Guest.jsx modules/chatbot/frontend/pages/Guest.jsx
mv frontend/src/pages/Staff.jsx modules/chatbot/frontend/pages/Staff.jsx
```

### Step 3.4: Create Chat API Client
Create `modules/chatbot/frontend/api/chatApi.js`

### Step 3.5: Test Chatbot Module
- Test `/ask/guest` endpoint
- Test `/ask/staff` endpoint
- Test `/ask/agent` endpoint
- Test frontend chat interface

**Success Criteria:**
- ✅ All chat endpoints work
- ✅ ChatBox component works
- ✅ ChatWidget works
- ✅ No import errors

---

## Phase 4: Split AdminPage Component (Day 11-15)

### Step 4.1: Analyze AdminPage.jsx
**Current:** 1700+ lines, handles:
- Authentication
- Analytics
- Chats
- Payments
- Rooms
- Reservations
- Housekeeping
- Properties
- System Health
- Knowledge Base

### Step 4.2: Create Component Structure
```
modules/admin/frontend/components/
├── AdminLayout.jsx          # Main layout with sidebar
├── AdminAuth.jsx            # Login form
├── Dashboard.jsx            # Overview tab
├── Analytics.jsx            # Analytics tab
├── Chats.jsx                # Chats tab
├── Payments.jsx             # Payments tab
├── Rooms.jsx                # Rooms tab
├── Reservations.jsx         # Reservations tab
├── Housekeeping.jsx         # Housekeeping tab
├── Properties.jsx           # Properties tab
├── SystemHealth.jsx         # System health tab
└── KnowledgeBase.jsx       # Knowledge base tab
```

### Step 4.3: Extract Shared Admin Logic
Create:
- `modules/admin/frontend/hooks/useAdminAuth.js`
- `modules/admin/frontend/hooks/useAdminData.js`
- `modules/admin/frontend/api/adminApi.js`

### Step 4.4: Move Backend Admin Routes
```bash
mv backend/app/api/routes/admin_analytics.py modules/admin/backend/routes/analytics.py
mv backend/app/api/routes/admin_monitoring.py modules/admin/backend/routes/monitoring.py
mv backend/app/api/routes/admin_kb.py modules/admin/backend/routes/knowledge_base.py
mv backend/app/api/routes/admin_jobs.py modules/admin/backend/routes/jobs.py
```

### Step 4.5: Test Admin Module
- Test each admin tab
- Test admin authentication
- Verify all admin endpoints work

**Success Criteria:**
- ✅ AdminPage split into manageable components
- ✅ Each component < 300 lines
- ✅ All admin endpoints work
- ✅ No import errors

---

## Phase 5: Extract Booking Module (Day 16-20)

### Step 5.1: Move Backend Code
```bash
# Extract reservation endpoints from admin_rooms.py
# Create modules/booking/backend/routes/bookings.py

mv backend/app/integrations/mock_room.py modules/booking/backend/integrations/mock_room.py
mv backend/app/db/room_queries.py modules/booking/backend/queries/room_queries.py
```

### Step 5.2: Move Frontend Code
```bash
# Extract booking components from ToolPages.jsx
# Create modules/booking/frontend/components/
```

### Step 5.3: Create Booking API Client
Create `modules/booking/frontend/api/bookingApi.js`

### Step 5.4: Test Booking Module
- Test room booking flow
- Test reservation endpoints
- Test frontend booking form

**Success Criteria:**
- ✅ Booking endpoints work
- ✅ Booking form works
- ✅ No import errors

---

## Phase 6: Extract Remaining Modules (Day 21-35)

### Step 6.1: Commerce Module (Day 21-25)
- Move catalog routes
- Move admin commerce routes
- Move dining/event integrations
- Create commerce components

### Step 6.2: Payments Module (Day 26-28)
- Move payment routes
- Move Stripe provider
- Create payment components

### Step 6.3: Rooms Module (Day 29-31)
- Extract room management from admin_rooms.py
- Create room components

### Step 6.4: Housekeeping Module (Day 32-33)
- Extract housekeeping from admin_rooms.py
- Create housekeeping components

### Step 6.5: Knowledge Base Module (Day 34-35)
- Move KB routes
- Move RAG services
- Create KB components

---

## Phase 7: Extract Shared Code (Day 36-40)

### Step 7.1: Backend Shared Code
```bash
# Database
mv backend/app/db/session.py shared/backend/db/session.py
mv backend/app/db/queries.py shared/backend/db/queries.py

# Core
mv backend/app/core/config.py shared/backend/core/config.py
mv backend/app/core/logging.py shared/backend/core/logging.py

# Utils
mv backend/app/utils/* shared/backend/utils/
```

### Step 7.2: Frontend Shared Code
```bash
# API Client
# Create shared/frontend/api/apiClient.js

# Hooks
# Create shared/frontend/hooks/useApi.js
# Create shared/frontend/hooks/useAuth.js (if not in auth module)

# Utils
mv frontend/src/utils/* shared/frontend/utils/
```

### Step 7.3: Update All Imports
- Update all modules to use shared code
- Test all modules

---

## Phase 8: Testing & Documentation (Day 41-45)

### Step 8.1: Module Testing
- Test each module independently
- Integration testing
- End-to-end testing

### Step 8.2: Documentation
- Create README for each module
- Update main README
- Create architecture diagram

### Step 8.3: Code Review
- Review code quality
- Fix any issues
- Optimize imports

---

## Quick Start: Begin with Auth Module

### Right Now:
1. Create `modules/auth/` structure
2. Move `backend/app/api/routes/auth.py`
3. Update imports in `main.py`
4. Test auth endpoints

### Next:
1. Move auth frontend code
2. Create auth hooks
3. Test complete auth flow

---

## Testing Strategy

### Per Module:
1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test module endpoints
3. **Component Tests** - Test React components
4. **E2E Tests** - Test complete user flows

### After Each Phase:
1. Run all tests
2. Check for import errors
3. Verify endpoints work
4. Test frontend components

---

## Rollback Plan

If something breaks:
1. Git commit before each phase
2. Keep old code until new code is tested
3. Use feature flags if needed
4. Can rollback to previous commit

---

## Success Metrics

- ✅ Each module < 1000 lines
- ✅ Each component < 300 lines
- ✅ No circular dependencies
- ✅ All tests pass
- ✅ All endpoints work
- ✅ Frontend components work
- ✅ Documentation complete

---

**Ready to start? Let's begin with Phase 1!**
