"""
Centralized error handling for the hotel management system.

This module provides:
- Custom exception classes with proper HTTP status codes
- Error handling decorator for all API routes
- Consistent error response format
"""

from functools import wraps
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import traceback
import inspect
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================

class HotelAPIError(Exception):
    """Base exception for all hotel API operations"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(HotelAPIError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message, 
            status_code=400,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class NotFoundError(HotelAPIError):
    """Raised when a resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class UnauthorizedError(HotelAPIError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )


class DatabaseError(HotelAPIError):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {}
        )


class ExternalServiceError(HotelAPIError):
    """Raised when external services (AI, PMS, etc.) fail"""
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


# ============================================================================
# Error Handler Decorator
# ============================================================================

def handle_errors(func):
    """
    Decorator to catch and properly handle all errors in API routes.
    Works with both async and sync route functions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except HotelAPIError as e:
            logger.error(
                f"{func.__name__} failed: {e.message}",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "details": e.details,
                    "function": func.__name__,
                },
            )
            raise HTTPException(
                status_code=e.status_code,
                detail={
                    "error": e.message,
                    "code": e.error_code,
                    "details": e.details,
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(
                f"Unexpected error in {func.__name__}: {str(e)}",
                extra={
                    "function": func.__name__,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "An internal error occurred",
                    "code": "INTERNAL_ERROR",
                    "details": {},
                },
            )
    return wrapper


# ============================================================================
# Global Exception Handler (for FastAPI app)
# ============================================================================

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for uncaught exceptions.
    Add this to your FastAPI app:
        app.add_exception_handler(Exception, global_exception_handler)
    """
    
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "code": "UNHANDLED_ERROR",
            "path": request.url.path
        }
    )


# ============================================================================
# Validation Helper
# ============================================================================

def validate_required(value: Any, field_name: str) -> Any:
    """Validate that a required field is not empty"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} is required", field=field_name)
    return value


def validate_in_range(value: int, min_val: int, max_val: int, field_name: str) -> int:
    """Validate that a number is within a range"""
    if value < min_val or value > max_val:
        raise ValidationError(
            f"{field_name} must be between {min_val} and {max_val}",
            field=field_name
        )
    return value
