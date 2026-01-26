# AI Hotel Assistant - Agentic Commerce Platform

A sophisticated AI-powered hotel management system with intelligent agent capabilities, multi-tenant architecture, and integrated commerce features.

## 🌟 Features

### Core Capabilities
- **Intelligent AI Agent**: Context-aware conversational AI with RAG (Retrieval-Augmented Generation)
- **Multi-Tenant Architecture**: Secure tenant isolation with JWT authentication
- **Agentic Commerce**: Automated booking workflows for rooms, dining, and events
- **Payment Integration**: Stripe checkout with webhook handling
- **Queue System**: Redis + RQ for reliable background job processing

### Technical Highlights
- **Backend**: FastAPI + SQLite + ChromaDB
- **Frontend**: React + Vite
- **AI/ML**: Google Gemini API with custom planner and tool execution
- **Infrastructure**: Docker-ready with comprehensive testing suite

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redis (for queue system)

### Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

## 📁 Project Structure

```
ai-hotel-assistant/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI agent & planner
│   │   ├── api/            # FastAPI routes
│   │   ├── services/       # Business logic
│   │   ├── payments/       # Stripe integration
│   │   ├── queue/          # Background jobs
│   │   └── db/             # Database models
│   ├── tests/              # 30+ test files
│   └── docs/               # Documentation
├── frontend/
│   └── src/
│       ├── components/     # React components
│       └── pages/          # Page layouts
└── docker-compose.yml      # Multi-container setup
```

## 🧪 Testing

```bash
cd backend
python -m pytest tests/
```

## 🔑 Key Components

### AI Agent System
- **Planner**: Generates multi-step execution plans
- **Runner**: Executes plans with confirmation checkpoints
- **Tools**: 15+ integrated tools for hotel operations

### Commerce Features
- Room booking with availability checking
- Restaurant table reservations
- Event ticket purchasing
- Dynamic pricing with quotes and receipts

### Security
- JWT-based authentication
- Tenant isolation at database level
- API key protection for admin endpoints
- Webhook signature verification

## 📚 Documentation

- [RUNBOOK.md](backend/docs/RUNBOOK.md) - Deployment guide
- [workflows.md](backend/docs/workflows.md) - Development workflows

## 🛠️ Tech Stack

**Backend:**
- FastAPI, SQLite, ChromaDB
- Google Gemini API
- Stripe, Redis, RQ

**Frontend:**
- React 18, Vite
- Modern CSS with responsive design

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributing

This is a demonstration project showcasing agentic AI capabilities in hospitality management.

---

Built with ❤️ using AI-assisted development
