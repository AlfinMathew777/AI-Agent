"""
Health check endpoint with comprehensive component status monitoring.

This endpoint provides detailed health status for:
- Database connectivity
- AI/LLM service configuration
- System information
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from typing import Dict, Any

router = APIRouter()


def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and status"""
    try:
        from app.db.session import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        # Get database stats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "status": "healthy",
            "tables_count": len(tables),
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }


def check_ai_service_health() -> Dict[str, Any]:
    """Check AI/LLM service configuration"""
    try:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if google_api_key and len(google_api_key) > 10:
            return {
                "status": "configured",
                "provider": "Google Gemini",
                "message": "AI service configured"
            }
        else:
            return {
                "status": "not_configured",
                "message": "AI service not configured",
                "warning": "GOOGLE_API_KEY not set or invalid"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "AI service check failed"
        }


@router.get("/health")
def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns detailed status for all system components:
    - Overall system status
    - Database health
    - AI service configuration
    - System metadata
    
    Returns:
        200: All systems healthy
        503: One or more components unhealthy
    """
    
    # Check all components
    db_health = check_database_health()
    ai_health = check_ai_service_health()
    
    # Determine overall status
    is_healthy = (
        db_health["status"] == "healthy" and
        ai_health["status"] in ["configured", "not_configured"]  # not_configured is acceptable
    )
    
    response = {
        "status": "healthy" if is_healthy else "degraded",
        "service": "shhg-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_health,
            "ai_service": ai_health
        },
        "system": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }
    }
    
    # Return 503 if unhealthy, 200 otherwise
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )


@router.get("/health/database")
def database_health():
    """Detailed database health check"""
    db_health = check_database_health()
    status_code = (
        status.HTTP_200_OK
        if db_health["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(status_code=status_code, content=db_health)


@router.get("/health/ai")
def ai_service_health():
    """Detailed AI service health check"""
    ai_health = check_ai_service_health()
    status_code = (
        status.HTTP_200_OK
        if ai_health["status"] in ["configured", "not_configured"]
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(status_code=status_code, content=ai_health)

