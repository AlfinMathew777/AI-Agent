# Southern Horizons Hotel

A world-class luxury hotel website powered by AI intelligence. Built with React, FastAPI, and Google Gemini.

![Luxury Hotel](https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1200&q=80)

## Overview

Southern Horizons is a premium hotel booking platform that combines **luxury hospitality design** with **AI-powered intelligence**. The public website feels like Aman, Four Seasons, and Ritz-Carlton, while the backend is powered by a sophisticated multi-agent AI system.

### Key Features

- **Luxury Public Website** — Cinematic hero, elegant typography, champagne gold accents
- **AI Concierge** — Intelligent booking assistant that guides guests through reservations
- **Guided Booking Flow** — Step-by-step room selection, services, and Stripe checkout
- **Staff AI Assistant** — Role-aware policy chatbot with RAG knowledge base
- **Management Intelligence** — Real-time KPIs and business insights for managers
- **Role-Based Access Control** — 6 roles with granular permissions

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Tailwind CSS, Lucide Icons |
| Backend | FastAPI (Python), SQLAlchemy |
| Database | SQLite, ChromaDB (vector store) |
| AI | Google Gemini 2.0 Flash |
| Payments | Stripe Checkout |
| Auth | JWT with RBAC |

## Design System

### Luxury Theme (Public Website)
```
Champagne Gold: #C6A66B
Charcoal:       #0F1115
Ivory:          #F7F3EE
Stone:          #D9D2C7
Bronze:         #8C6A43
```

### Typography
- **Headings:** Cormorant Garamond (elegant serif)
- **Body:** Manrope (clean sans-serif)

## Project Structure

```
/app
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── agents/          # AI agents (Policy, Management, Booking)
│   │   ├── core/            # Config, auth, database
│   │   └── services/        # RAG, LLM services
│   └── server.py
├── frontend/
│   └── src/
│       ├── components/      # Reusable UI components
│       ├── pages/           # Page components
│       │   ├── LuxuryLanding.jsx   # Public homepage
│       │   ├── GuestChat.jsx       # AI Concierge booking
│       │   ├── StaffChat.jsx       # Staff AI assistant
│       │   └── ManagementDashboard.jsx
│       └── index.css        # Design system
└── memory/
    └── PRD.md               # Product requirements
```

## Pages

### Public Website
| Page | Description |
|------|-------------|
| **Home** | Cinematic hero, booking bar, experiences grid, rooms preview |
| **AI Concierge** | Guided booking flow with AI assistance |

### Internal Portals
| Page | Access | Description |
|------|--------|-------------|
| Staff Chat | All Staff | AI assistant for hotel policies |
| Management | Managers | KPIs, insights, business chat |
| A2A Dashboard | Front Desk+ | Real-time agent activity |
| Operations | Housekeeping+ | Task management |
| Analytics | Managers+ | Revenue & occupancy trends |
| Admin Panel | Admins | User & system management |

## User Roles

| Role | Access Level |
|------|--------------|
| `guest` | AI Concierge booking only |
| `front_desk` | + Operations, A2A Dashboard |
| `housekeeping` | Operations Dashboard |
| `restaurant` | Operations Dashboard |
| `manager` | + Analytics, Management AI |
| `admin` | Full access |

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/southern-horizons-hotel.git
   cd southern-horizons-hotel
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   python server.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   yarn start
   ```

4. **Seed Data**
   ```bash
   cd backend
   python scripts/seed_data.py
   ```

### Test Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hotel.com | admin123 |
| Manager | manager@hotel.com | manager123 |
| Front Desk | frontdesk@hotel.com | frontdesk123 |
| Guest | guest@hotel.com | guest123 |

## AI Architecture

### Multi-Agent System (A2A Protocol)

```
┌─────────────────────────────────────────────────┐
│                  Orchestrator                    │
│            (Coordinates all agents)              │
└─────────────────────────────────────────────────┘
        │         │         │         │
   ┌────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼────┐
   │ Guest  │ │Booking │ │Price │ │Payment │
   │ Agent  │ │ Agent  │ │Agent │ │ Agent  │
   └────────┘ └────────┘ └──────┘ └────────┘
```

### AI Assistants

| Assistant | Purpose | Technology |
|-----------|---------|------------|
| **AI Concierge** | Guest booking guidance | Gemini + Guided Flow |
| **Staff AI** | Policy questions | ChromaDB RAG + Gemini |
| **Management AI** | Business insights | Live DB + Gemini |

## API Endpoints

### Public
- `POST /api/booking/rooms/available` — Check room availability
- `POST /api/booking/checkout` — Create Stripe session
- `POST /api/booking/webhook` — Stripe webhook handler

### Authenticated
- `POST /api/staff/chat` — Staff AI assistant
- `GET /api/management/kpis` — Dashboard metrics
- `POST /api/management/chat` — Business intelligence chat

## Roadmap

- [x] Phase 1: Luxury Landing Page & Brand System
- [x] Phase 1: AI Concierge Booking Flow
- [x] Phase 1: Staff AI with Knowledge Base
- [x] Phase 1: Management Intelligence Dashboard
- [ ] Phase 2: Rooms & Suites Detail Page
- [ ] Phase 2: Dining & Experiences Pages
- [ ] Phase 3: Internal Portal Polish
- [ ] Phase 3: Mobile Responsive Design

## License

MIT License

## Acknowledgments

- Design inspired by Aman, Four Seasons, and Ritz-Carlton
- Built with [Emergent](https://emergentagent.com)
- AI powered by Google Gemini

---

<p align="center">
  <strong>Southern Horizons Hotel</strong><br>
  <em>Where Luxury Meets Intelligence</em>
</p>
