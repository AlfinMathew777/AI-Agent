# A2A Nexus — Hotel AI Platform PRD

## Product Overview
A2A Nexus is a multi-agent AI hotel management system where 8 specialized AI agents communicate in real-time to handle bookings, pricing, negotiation, and operations.

## Architecture
- **Backend**: FastAPI (Python), port 8001, SQLite + ChromaDB + Redis
- **Frontend**: React 18 + CRA, port 3000, dark SaaS theme
- **AI**: Google Gemini 2.0 Flash via emergentintegrations
- **A2A Protocol**: WebSocket + REST for real-time agent feed

## Design System
- Background: #0F172A | Panels: #1E293B | Accent: #38BDF8
- Success: #22C55E | Warning: #F59E0B | Error: #EF4444
- Font: Chivo (headings) + Inter (body) + JetBrains Mono (terminal)

## 8 Agents
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
2. **Login Page** - Glassmorphic card auth
3. **A2A Dashboard** - Live WebSocket feed + 8 agent status cards + pipeline trigger
4. **Guest Chat** - Full AI concierge with markdown rendering
5. **Admin Panel** - Rooms/Reservations/Payments tables with search
6. **Operations Dashboard** - Today stats + housekeeping task board
7. **Analytics Dashboard** - Revenue charts (Recharts) + agent performance

## API Endpoints
- `GET /api/a2a/status` — Agent statuses
- `POST /api/a2a/chat` — Main A2A pipeline chat
- `WS /api/ws/a2a` — Live WebSocket agent feed
- `GET /api/analytics/summary` — KPI metrics
- `GET /api/analytics/revenue?days=N` — Revenue chart
- `GET /api/analytics/agents` — Agent performance
- `GET /api/analytics/occupancy` — Room occupancy
- `GET /api/admin/rooms` — Room list (JWT required)
- `GET /api/admin/reservations` — Reservation list
- `POST /api/auth/register` — Register
- `POST /api/auth/login` — Login

## Credentials (Dev)
- Admin: admin@hotel.com / admin123
- Admin API Key: shhg_admin_secure_key_2024
- Gemini Key: configured in backend/.env

## What's Been Implemented (2026-03-08)
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

## Known Limitations / Next Steps
- P1: Add price_per_night to rooms schema (currently shows "—")
- P1: Reservations table needs guest-booking join query
- P2: Add real Stripe checkout flow in Admin
- P2: Room status should reflect actual bookings (available vs occupied)
- P3: Multi-tenant property switcher in sidebar
- P3: Real-time notifications (browser push)
- P3: Playwright e2e test suite for A2A flows
- Backlog: Voice input for guest chat
- Backlog: Mobile responsive sidebar (bottom nav)
