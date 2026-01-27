from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from app.api.routes import health, ask, agent, admin_kb, admin_analytics, admin_commerce, catalog, admin_monitoring
from app.core.structured_logger import get_logger

logger = get_logger("app.middleware")

def create_app() -> FastAPI:
    app = FastAPI(
      title="Southern Horizons Hospitality Group AI Concierge & Staff Assistant",
      description="Backend service for guest concierge and staff knowledge assistant.",
      version="0.2.0",
    )

    # Allow local dev frontends
    origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4()) # Placeholder, strictly we might parse from body but stream body is tricky
        
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Request processed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=f"{process_time:.2f}",
            req_id=request_id
        )
        
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        MAX_SIZE = 2000000 # 2MB (approx text limit + small overhead)
        # For file uploads, Nginx/FastAPI handles it differently (stream).
        # This checks Content-Length header for quick rejection.
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_SIZE:
             from fastapi import Response
             return Response("Request too large", status_code=413)
        return await call_next(request)

    from app.api.routes import auth
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(ask.router)
    app.include_router(agent.router)
    app.include_router(admin_kb.router)
    app.include_router(admin_analytics.router)
    app.include_router(admin_commerce.router)
    app.include_router(admin_monitoring.router)
    app.include_router(catalog.router)
    
    from app.api.routes import payments, admin_jobs
    app.include_router(payments.router)
    app.include_router(admin_jobs.router)

    return app
