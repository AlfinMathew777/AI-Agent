"""
AI Hotel Assistant - Server Entry Point (Emergent Environment)
Wraps the hotel app with /api prefix for Emergent proxy compatibility.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Add backend dir to path so imports work
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create main app
app = FastAPI(
    title="AI Hotel Assistant",
    version="1.0.0",
)

# CORS - allow everything for Emergent environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed demo data on startup"""
    try:
        from app.db.session import init_db
        init_db()
        print("[Server] Database initialized successfully")
    except Exception as e:
        print(f"[Server] Database init warning: {e}")

    try:
        from app.db.seed_data import seed_demo_data
        seed_demo_data()
    except Exception as e:
        print(f"[Server] Seed warning: {e}")

# Import and include all routers with /api prefix
def _include_routers():
    try:
        from app.api.routes import auth
        app.include_router(auth.router, prefix="/api")
    except Exception as e:
        import traceback
        print(f"[Server] auth router: {e}")
        traceback.print_exc()

    try:
        from app.api.routes import health
        app.include_router(health.router, prefix="/api")
    except Exception as e:
        print(f"[Server] health router: {e}")

    try:
        from app.api.routes import ask
        app.include_router(ask.router, prefix="/api")
    except Exception as e:
        print(f"[Server] ask router: {e}")

    try:
        from app.api.routes import agent
        app.include_router(agent.router, prefix="/api")
    except Exception as e:
        print(f"[Server] agent router: {e}")

    try:
        from app.api.routes import admin_kb
        app.include_router(admin_kb.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_kb router: {e}")

    try:
        from app.api.routes import admin_analytics
        app.include_router(admin_analytics.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_analytics router: {e}")

    try:
        from app.api.routes import admin_commerce
        app.include_router(admin_commerce.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_commerce router: {e}")

    try:
        from app.api.routes import admin_monitoring
        app.include_router(admin_monitoring.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_monitoring router: {e}")

    try:
        from app.api.routes import admin_rooms
        app.include_router(admin_rooms.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_rooms router: {e}")

    try:
        from app.api.routes import catalog
        app.include_router(catalog.router, prefix="/api")
    except Exception as e:
        print(f"[Server] catalog router: {e}")

    try:
        from app.api.routes import payments
        app.include_router(payments.router, prefix="/api")
    except Exception as e:
        print(f"[Server] payments router: {e}")

    try:
        from app.api.routes import admin_jobs
        app.include_router(admin_jobs.router, prefix="/api")
    except Exception as e:
        print(f"[Server] admin_jobs router: {e}")

    try:
        from app.api.routes import a2a as a2a_route
        app.include_router(a2a_route.router, prefix="/api")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[Server] a2a router: {e}")

    try:
        from app.api.routes import analytics
        app.include_router(analytics.router, prefix="/api")
    except Exception as e:
        print(f"[Server] analytics router: {e}")

    try:
        from app.acp.protocol.gateway_server import router as acp_router
        app.include_router(acp_router, prefix="/api")
    except Exception as e:
        print(f"[Server] acp_router: {e}")

    try:
        from app.acp.api.routes.properties import router as properties_router
        app.include_router(properties_router, prefix="/api")
    except Exception as e:
        print(f"[Server] properties router: {e}")

    try:
        from app.acp.api.routes.agents import router as agents_router
        app.include_router(agents_router, prefix="/api")
    except Exception as e:
        print(f"[Server] agents router: {e}")

    try:
        from app.acp.api.routes.marketplace import router as marketplace_router
        app.include_router(marketplace_router, prefix="/api")
    except Exception as e:
        print(f"[Server] marketplace router: {e}")

    try:
        from app.api.routes.staff_chat import router as staff_chat_router
        app.include_router(staff_chat_router, prefix="/api")
    except Exception as e:
        import traceback
        print(f"[Server] staff_chat router: {e}")
        traceback.print_exc()


_include_routers()


@app.get("/api")
async def root():
    return {"message": "AI Hotel Assistant API", "status": "running"}


@app.get("/api/ping")
async def ping():
    return {"pong": True}
