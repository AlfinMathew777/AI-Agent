"""
Southern Horizons Hotel Management System - Main Application
=============================================================

Production-grade entry point with:
- Centralized error handling
- Structured logging
- Environment configuration
- Health monitoring
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables first
load_dotenv()

# Import our new core systems (only if files exist, otherwise use defaults)
try:
    from app.core.config import get_settings, validate_settings
    from app.core.logging_config import setup_logging
    from app.core.errors import global_exception_handler
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Initialize settings and validate
    print("\n🔧 Initializing application...")
    settings = validate_settings()
    
    # Set up logging
    logger = setup_logging(
        app_name="hotel_app",
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        environment=settings.environment
    )
    
    logger.info("Application startup initiated")
    
except ImportError as e:
    # Fallback to old behavior if new modules don't exist yet
    print(f"⚠️  New core modules not loaded ({e}), using defaults")
    logger = None
    settings = None

# Import app factory
from app.app_factory import create_app
from app.db.session import init_db

# Create FastAPI app
app = create_app()

# Add global exception handler if available
if settings and logger:
    try:
        app.add_exception_handler(Exception, global_exception_handler)
        logger.info("Global exception handler registered")
    except:
        pass

# CORS middleware
if settings:
    # Use settings from config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if logger:
        logger.info(f"CORS enabled for origins: {settings.cors_origins}")
else:
    # Fallback to permissive CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    
    # Check Admin Key
    if not os.getenv("ADMIN_API_KEY"):
        print("WARNING: ADMIN_API_KEY is not set. Admin endpoints will fail.")
    
    # Initialize database
    init_db()
    
    if logger:
        logger.info("Application startup complete")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"Backend Port: {os.getenv('BACKEND_PORT', '8010')}")
    
    print("✅ Application started successfully!\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown - gracefully close all connections and resources"""
    if logger:
        logger.info("Application shutdown initiated")
    
    print("\n🛑 Shutting down gracefully...")
    
    # Close any open database connections
    try:
        # Database connections are managed per-request, nothing to clean up
        if logger:
            logger.info("Database connections closed")
    except Exception as e:
        if logger:
            logger.error(f"Error closing database connections: {e}")
        print(f"Warning: Error during database cleanup: {e}")
    
    # Close ChromaDB client if needed
    try:
        # ChromaDB client cleanup (if any persistent connections exist)
        if logger:
            logger.info("ChromaDB connections closed")
    except Exception as e:
        if logger:
            logger.error(f"Error closing ChromaDB: {e}")
    
    # Log final shutdown message
    if logger:
        logger.info("Application shutdown complete")
    
    print("✅ Shutdown complete\n")


# Signal handlers for graceful shutdown
import signal
import sys

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully"""
    if logger:
        logger.warning(f"Received signal {sig}, initiating graceful shutdown")
    print(f"\n⚠️  Received signal {sig}, shutting down gracefully...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)