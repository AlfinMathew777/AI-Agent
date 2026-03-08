# A2A Nexus — Hotel AI Platform PRD

## Product Overview
A2A Nexus is a multi-agent AI hotel management system where 8 specialized AI agents communicate in real-time to handle bookings, pricing, negotiation, and operations. The platform supports role-based access control (RBAC) for different hotel staff roles.

## Architecture
- **Backend**: FastAPI (Python), port 8001, SQLite + ChromaDB + Redis
- **Frontend**: React 18 + CRA, port 3000, dark SaaS theme
- **AI**: Google Gemini 2.0 Flash via emergentintegrations
- **A2A Protocol**: WebSocket + REST for real-time agent feed
- **Auth**: JWT-based with role-based access control

## Design System
- Background: #0F172A | Panels: #1E293B | Accent: #38BDF8
- Success: #22C55E | Warning: #F59E0B | Error: #EF4444
- Font: Chivo (headings) + Inter (body) + JetBrains Mono (terminal)

## Role-Based Access Control (RBAC)

### Roles & Permissions
| Role | Pages Access | Key Features |
|------|--------------|--------------|
| **admin** | All 7 pages | Full platform access, user management, system config |
| **manager** | 6 pages (no Admin) | Business intelligence, analytics, staff management |
| **front_desk** | 4 pages | Guest check-in/out, reservations, A2A dashboard |
| **housekeeping** | 2 pages | Room cleaning tasks, operations dashboard |
| **restaurant** | 2 pages | Food service, menu management |
| **guest** | 1 page | Guest chat and booking only |

### Navigation Items by Role
- **Admin**: A2A Dashboard, Guest Chat, Staff Assistant, Intelligence, Admin Panel, Operations, Analytics
- **Manager**: A2A Dashboard, Guest Chat, Staff Assistant, Intelligence, Operations, Analytics
- **Front Desk**: A2A Dashboard, Guest Chat, Staff Assistant, Operations
- **Housekeeping**: Staff Assistant, Operations
- **Restaurant**: Staff Assistant, Operations
- **Guest**: Guest Chat

## AI Agents

### 8 A2A Agents
| Agent | Role | Color |
|-------|------|-------|
| Guest Agent | NLP & Intent | #38BDF8 |
| Booking Agent | Availability | #22C55E |
| Pricing Agent | Dynamic Pricing | #F59E0B |
| Negotiation Agent | Discounts | #A78BFA |
| Payment Agent | Transactions | #34D399 |
| Inventory Agent | Room Stock | #60A5FA |
| Operations Agent | Housekeeping | #FB923C |
| Orchestrator | Coordinator | #F472B6 |

### Staff AI (PolicyAgent)
- **Purpose**: Role-aware assistant for hotel policies and procedures
- **Technology**: ChromaDB RAG + Gemini LLM
- **Features**: 
  - Role-specific system prompts and focus areas
  - Knowledge base PDF/TXT upload
  - Source document references
- **Roles Supported**: front_desk, housekeeping, restaurant, manager, admin

### Management AI (ManagementAgent)
- **Purpose**: Real-time business intelligence for managers
- **Technology**: Live SQLite queries + Gemini summarization
- **Features**:
  - Live KPI metrics (occupancy, revenue, reservations)
  - AI-generated insights and alerts
  - Natural language queries about business performance
- **Roles Supported**: manager, admin only

## Screens

1. **Landing Page** - Hero + 8 agent showcase + features + demo chat
2. **Login Page** - Glassmorphic card auth with quick-login buttons for all roles
3. **A2A Dashboard** - Live WebSocket feed + 8 agent status cards + pipeline trigger
4. **Guest Chat** - Full AI concierge with markdown rendering
5. **Staff Assistant** - Role-aware AI assistant with RAG knowledge base
6. **Management Intelligence** - KPI cards + AI insights + business chat + arrivals panel
7. **Admin Panel** - Rooms/Reservations/Payments tables + Knowledge Base management
8. **Operations Dashboard** - Today stats + housekeeping task board
9. **Analytics Dashboard** - Revenue charts (Recharts) + agent performance

## API Endpoints

### Authentication
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login (returns role, allowed_pages, allowed_features)
- `GET /api/auth/me` — Get current user permissions

### Staff AI
- `POST /api/staff/chat` — Staff AI chat (requires staff role)
- `GET /api/staff/context` — Get role-specific context
- `GET /api/staff/examples` — Get example questions per role

### Management Intelligence
- `GET /api/management/metrics` — Real-time KPIs (manager/admin only)
- `POST /api/management/chat` — AI chat with live data (manager/admin only)
- `GET /api/management/insights` — AI-generated business insights
- `GET /api/management/examples` — Example business queries

### Knowledge Base (Admin)
- `POST /api/admin/upload` — Upload PDF/TXT/MD files
- `GET /api/admin/files` — List uploaded files
- `DELETE /api/admin/files/{audience}/{filename}` — Delete file
- `POST /api/admin/reindex` — Reindex knowledge base
- `GET /api/admin/index/status` — Get vector index statistics

### A2A System
- `GET /api/a2a/status` — Agent statuses
- `POST /api/a2a/chat` — Main A2A pipeline chat
- `WS /api/ws/a2a` — Live WebSocket agent feed

### Admin
- `GET /api/admin/rooms` — Room list
- `GET /api/admin/reservations` — Reservation list

## Test Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hotel.com | admin123 |
| Manager | manager@hotel.com | manager123 |
| Front Desk | frontdesk@hotel.com | frontdesk123 |
| Housekeeping | housekeeping@hotel.com | housekeeping123 |
| Restaurant | restaurant@hotel.com | restaurant123 |
| Guest | guest@hotel.com | guest123 |

## What's Been Implemented

### Phase 1: Core Platform (Complete)
- [x] Complete dark SaaS redesign (#0F172A theme)
- [x] 8 AI agents with Gemini LLM integration
- [x] WebSocket real-time agent event broadcasting
- [x] A2A pipeline (booking flow confirmed working)
- [x] Guest chat with A2A routing + markdown
- [x] Admin panel with real DB data (20 rooms seeded)
- [x] Operations dashboard with HK task board
- [x] Analytics with Recharts (revenue/occupancy/agent perf)
- [x] Bug fixes: error leaks, confirmation loop, transaction history
- [x] Demo data seeding on startup per tenant

### Phase 2: RBAC Implementation (Complete - 2026-03-08)
- [x] Full RBAC backend implementation (6 roles)
- [x] Role-based API endpoint protection
- [x] Role-based sidebar navigation filtering
- [x] Role-based page access control
- [x] Quick login buttons for all roles on login page
- [x] Role labels and colors in sidebar
- [x] Test accounts seeded for all 6 roles
- [x] 100% test pass rate (23 backend tests, 6 UI scenarios)

### Phase 3: Staff AI & Knowledge Base (Complete - 2026-03-08)
- [x] PolicyAgent with ChromaDB RAG integration
- [x] Role-aware system prompts and responses
- [x] PDF/TXT/MD file upload for knowledge base
- [x] Admin Knowledge Base management UI
- [x] Source document references in responses
- [x] 3 SOP documents indexed (front_desk, housekeeping, restaurant)
- [x] 72 vectors indexed in ChromaDB
- [x] 100% test pass rate (15 backend tests)

### Phase 4: Management Intelligence AI (Complete - 2026-03-08)
- [x] ManagementAgent with live DB queries
- [x] Real-time KPI metrics (occupancy, revenue, reservations)
- [x] AI-generated business insights
- [x] Management Dashboard with 4 KPI cards
- [x] Insight cards (Low Occupancy, Arrivals Today, Strong Revenue)
- [x] AI chat for business questions
- [x] Room Availability breakdown by type
- [x] Upcoming Arrivals panel
- [x] Manager/admin only access control
- [x] 100% test pass rate (19 backend tests)

## Upcoming Tasks

### P0: Guided Booking Flow & Stripe Integration
- [ ] Refactor GuestAgent for button-driven booking
- [ ] Room selection with availability display
- [ ] Service add-ons selection
- [ ] Booking summary in chat
- [ ] Total price calculation
- [ ] Stripe checkout session integration
- [ ] Stripe webhook for payment confirmation
- [ ] Booking confirmation flow

### P1: Future Enhancements
- [ ] E2E testing suite (Playwright)
- [ ] Enhanced Analytics dashboards
- [ ] Multi-tenant property switcher
- [ ] Real-time browser notifications
- [ ] Mobile responsive sidebar

## Current Metrics Snapshot
- Occupancy Rate: 30%
- Revenue Today: $7,653
- Active Reservations: 9
- Available Rooms: 14
- Total Rooms: 20
- Arrivals Today: 9

## Technical Debt
- P1: Add price_per_night to rooms schema
- P1: Reservations table needs guest-booking join query
- P2: Room status should reflect actual bookings
