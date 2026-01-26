
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Backend Root (e.g. /app in docker, or backend/ locally)
# file is app/core/config.py -> parent=core, parent=app, parent=backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "hotel.db"))

# ChromaDB
# Default to backend/chroma_db to match user request for docker volume
CHROMA_PATH = os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma_db"))

# Data Directory (Knowledge Base uploads)
# Default to backend/app/data
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "app" / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Integration
INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "mock")

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Public URLs
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5173")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8002")

# Queue (Redis)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default")
JOB_MAX_RETRIES = int(os.getenv("JOB_MAX_RETRIES", 3))
JOB_RETRY_BACKOFF_SECONDS = int(os.getenv("JOB_RETRY_BACKOFF_SECONDS", 10))
