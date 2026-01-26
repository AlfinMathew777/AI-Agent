# Operational Runbook / Deployment Guide

## System Overview
- **Backend**: FastAPI (Port 8002) - REST API, Agent Logic, Vector DB (Chroma).
- **Frontend**: React + Vite (Port 80/5173) - User Interface.
- **Database**: SQLite (`hotel.db`) - Relational data (Bookings, Logs, Plans).
- **Storage**: ChromaDB (`chroma_db/`) - Vector embeddings for RAG.
- **Data**: `app/data/` - Uploaded knowledge base files.

## 1. Startup (Docker - Recommended)
The system is containerized for easy deployment.

### Prerequisites
- Docker & Docker Compose installed.
- `.env` file created (Copy from `.env.example`).
  ```bash
  cp .env.example .env
  # Edit .env with your keys
  ```

### Start System
```bash
docker compose up -d --build
```
- Access Frontend: http://localhost:5173 (or http://localhost:80 if mapped)
- Access Backend Health: http://localhost:8002/health

### Stop System
```bash
docker compose down
```

## 2. Startup (Manual / Dev)
If running locally without Docker:

### Backend
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

## 3. Data Persistence
All data is persisted via Docker Volumes mapping to local directories:
- **Relational DB**: `backend/hotel.db`
- **Vector DB**: `backend/chroma_db/`
- **Files**: `backend/app/data/`

**Backup**: Simply copy these folders/files to a secure location.

## 4. Common Tasks

### Re-indexing Knowledge Base
Trigger a re-index if you manually add files or suspect sync issues.
```bash
curl -X POST -H "x-admin-key: YOUR_KEY" "http://localhost:8002/admin/reindex?audience=guest"
```

### Viewing Logs
Docker logs:
```bash
docker compose logs -f backend
```
Backend logs are structured (JSON-like) for easy parsing.

### Admin Dashboard
Visit the frontend and click the "Admin" tab. Ensure your `ADMIN_API_KEY` in `.env` matches the one required by the frontend/docs.

## 5. Troubleshooting

### "Admin Key Missing" Error
- **Cause**: `ADMIN_API_KEY` is not set in `.env` or Docker environment.
- **Fix**: Check `.env` file, restart container.

### "Backend Unreachable"
- **Cause**: Backend container crashed or port conflict.
- **Fix**: `docker compose ps` to check status. `docker compose logs backend` to see errors.

### "Quota Exceeded" (LLM)
- **Cause**: Google Gemini free tier limit reached.
- **Fix**: Wait 1 hour (auto-reset) or switch API keys. System falls back to "Offline Mode" automatically.
