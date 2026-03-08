# A2A Nexus — Hotel AI Platform PRD

## Product Overview
A2A Nexus is a multi-agent AI hotel management system where 8 specialized AI agents communicate in real-time to handle bookings, pricing, negotiation, and operations. The platform supports role-based access control (RBAC) for different hotel staff roles and provides a complete end-to-end guest booking experience with Stripe payment integration.

## Architecture
- **Backend**: FastAPI (Python), port 8001, SQLite + ChromaDB
- **Frontend**: React 18 + CRA, port 3000, dark SaaS theme
- **AI**: Google Gemini 2.0 Flash via emergentintegrations
- **Payments**: Stripe Checkout (test mode)
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
| **guest** | 1 page | Guest chat and guided booking only |

## AI Agents

### 8 A2A Agents (Real-time Communication)
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
- **Features**: Role-specific responses, knowledge base uploads, source references

### Management AI (ManagementAgent)
- **Purpose**: Real-time business intelligence for managers
- **Technology**: Live SQLite queries + Gemini summarization
- **Features**: KPI metrics, AI-generated insights, natural language queries

## Guided Booking Flow

### Booking Steps
1. **WELCOME** → "Book a Room" button
2. **DATES** → Date picker (check-in/check-out)
3. **GUESTS** → Guest counter (+/-)
4. **ROOMS** → Room cards (type, price, capacity, description)
5. **SERVICES** → Add-on selection grid
6. **SUMMARY** → Price breakdown + guest info
7. **PAYMENT** → Stripe Checkout redirect
8. **CONFIRMED** → Booking confirmation

### Room Types & Pricing
| Room Type | Price/Night | Capacity | Description |
|-----------|-------------|----------|-------------|
| Standard | $180 | 2 | Budget-friendly essentials |
| Deluxe | $260 | 2-3 | Premium bedding, city views |
| Ocean View | $320 | 2-3 | Panoramic views, balcony |
| Suite | $420 | 4 | Separate living area |
| Penthouse | $780 | 6 | Ultimate luxury, private terrace |

### Add-on Services
| Service | Price | Per Night |
|---------|-------|-----------|
| Daily Breakfast | $25 | Yes |
| Airport Pickup | $45 | No |
| Late Checkout | $35 | No |
| Extra Bed | $30 | Yes |
| Valet Parking | $20 | Yes |
| Spa Access | $40 | Yes |

## Screens

1. **Landing Page** - Hero + 8 agent showcase + features
2. **Login Page** - Quick-login buttons for all 6 roles
3. **A2A Dashboard** - Live WebSocket feed + agent status
4. **Guest Chat** - Guided booking flow with AI assistant
5. **Staff Assistant** - Role-aware policy AI with RAG
6. **Management Intelligence** - KPI cards + AI insights + chat
7. **Admin Panel** - Rooms/Reservations/Payments + Knowledge Base
8. **Operations Dashboard** - Today stats + housekeeping tasks
9. **Analytics Dashboard** - Revenue charts + agent performance

## API Endpoints

### Authentication
- `POST /api/auth/login` — Returns role, allowed_pages, allowed_features
- `GET /api/auth/me` — Current user permissions

### Guided Booking
- `GET /api/booking/services` — Available add-on services
- `POST /api/booking/rooms/available` — Room availability for dates
- `POST /api/booking/summary` — Price breakdown with taxes
- `POST /api/booking/checkout` — Create Stripe checkout session
- `GET /api/booking/status/{booking_id}` — Booking status
- `POST /api/booking/webhook` — Stripe payment webhook

### Staff AI
- `POST /api/staff/chat` — Staff AI chat with RAG
- `GET /api/staff/context` — Role-specific context

### Management Intelligence
- `GET /api/management/metrics` — Real-time KPIs
- `POST /api/management/chat` — AI chat with live data
- `GET /api/management/insights` — AI-generated insights

### Knowledge Base
- `POST /api/admin/upload` — Upload PDF/TXT files
- `GET /api/admin/files` — List uploaded files
- `POST /api/admin/reindex` — Reindex knowledge base

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
- [x] Dark SaaS UI redesign
- [x] 8 AI agents with Gemini integration
- [x] WebSocket real-time broadcasting
- [x] A2A booking pipeline
- [x] Admin panel with DB data
- [x] Operations & Analytics dashboards

### Phase 2: RBAC Implementation (Complete - 2026-03-08)
- [x] 6 roles with permissions
- [x] Role-based sidebar navigation
- [x] Role-based page access
- [x] Quick-login buttons
- [x] 100% test pass rate

### Phase 3: Staff AI & Knowledge Base (Complete - 2026-03-08)
- [x] PolicyAgent with ChromaDB RAG
- [x] Role-aware responses
- [x] PDF/TXT file upload
- [x] Knowledge Base management UI
- [x] 72 vectors indexed

### Phase 4: Management Intelligence AI (Complete - 2026-03-08)
- [x] ManagementAgent with live DB
- [x] Real-time KPI metrics
- [x] AI-generated insights
- [x] Dashboard with 4 KPI cards
- [x] Business chat panel

### Phase 5: Guided Booking + Stripe (Complete - 2026-03-08)
- [x] Step-by-step booking flow (7 steps)
- [x] Visual room selector cards
- [x] Service add-on selection grid
- [x] Price breakdown with 10% tax
- [x] Guest info form
- [x] Stripe Checkout integration
- [x] Webhook handler
- [x] Booking status tracking
- [x] 100% test pass rate (19 backend, all UI tests)

## Platform Complete Status

All major features implemented:
✅ **Staff AI** - Role-aware policy assistant with RAG
✅ **Management Intelligence** - Real-time business insights
✅ **Guided Booking** - Step-by-step room booking
✅ **Stripe Payments** - Secure checkout (test mode)

## Future Enhancements (P1)
- [ ] E2E testing suite (Playwright)
- [ ] Email notifications (SendGrid)
- [ ] Multi-tenant property switcher
- [ ] Mobile responsive design
- [ ] Guest loyalty program
- [ ] Room service ordering
