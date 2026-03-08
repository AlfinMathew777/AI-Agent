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

## 8 AI Agents
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

## Screens
1. **Landing Page** - Hero + 8 agent showcase + features + demo chat
2. **Login Page** - Glassmorphic card auth with quick-login buttons for all roles
3. **A2A Dashboard** - Live WebSocket feed + 8 agent status cards + pipeline trigger
4. **Guest Chat** - Full AI concierge with markdown rendering
5. **Staff Assistant** - Role-aware AI assistant for hotel policies (placeholder)
6. **Management Intelligence** - Real-time business metrics AI (placeholder)
7. **Admin Panel** - Rooms/Reservations/Payments tables with search
8. **Operations Dashboard** - Today stats + housekeeping task board
9. **Analytics Dashboard** - Revenue charts (Recharts) + agent performance

## API Endpoints
### Authentication
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login (returns role, allowed_pages, allowed_features)
- `GET /api/auth/me` — Get current user permissions

### A2A System
- `GET /api/a2a/status` — Agent statuses
- `POST /api/a2a/chat` — Main A2A pipeline chat
- `WS /api/ws/a2a` — Live WebSocket agent feed

### Analytics (Manager/Admin only)
- `GET /api/analytics/summary` — KPI metrics
- `GET /api/analytics/revenue?days=N` — Revenue chart
- `GET /api/analytics/agents` — Agent performance
- `GET /api/analytics/occupancy` — Room occupancy

### Admin (Admin only)
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
- [x] Staff Assistant page (placeholder UI)
- [x] Management Intelligence page (placeholder UI)
- [x] Test accounts seeded for all 6 roles
- [x] 100% test pass rate (23 backend tests, 6 UI scenarios)

## Upcoming Tasks

### P0: Staff AI & Knowledge Base
- [ ] Create PolicyAgent using ChromaDB for RAG
- [ ] Implement PDF/text file upload for knowledge base
- [ ] Connect Staff Assistant to PolicyAgent
- [ ] Make staff chat role-aware (different answers per role)

### P0: Management Intelligence AI
- [ ] Create ManagementAgent connected to live database
- [ ] Enable real-time business queries (occupancy, revenue)
- [ ] Connect Management Dashboard to ManagementAgent

### P0: Guided Booking Flow & Stripe Integration
- [ ] Refactor GuestAgent for button-driven booking
- [ ] Integrate Stripe checkout session & webhook
- [ ] Create booking summary view with payment button

### P1: Future Enhancements
- [ ] E2E testing suite (Playwright)
- [ ] Enhanced Analytics/Operations dashboards
- [ ] Multi-tenant property switcher
- [ ] Real-time browser notifications
- [ ] Mobile responsive sidebar

## Technical Debt
- P1: Add price_per_night to rooms schema
- P1: Reservations table needs guest-booking join query
- P2: Room status should reflect actual bookings
