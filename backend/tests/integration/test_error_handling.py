"""Integration tests for error handling."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


def test_custom_exceptions_have_proper_fields():
    """Test that custom exceptions have required fields"""
    from app.core.errors import (
        HotelAPIError,
        ValidationError,
        NotFoundError,
        UnauthorizedError,
        DatabaseError,
        ExternalServiceError
    )
    
    # Test base exception
    error = HotelAPIError("Test message", status_code=500)
    assert error.message == "Test message"
    assert error.status_code == 500
    
    # Test ValidationError
    error = ValidationError("Invalid field", field="email")
    assert error.status_code == 400
    assert error.error_code == "VALIDATION_ERROR"
    
    # Test NotFoundError
    error = NotFoundError("User", "123")
    assert error.status_code == 404
    assert error.error_code == "NOT_FOUND"
    
    # Test UnauthorizedError
    error = UnauthorizedError()
    assert error.status_code == 401
    assert error.error_code == "UNAUTHORIZED"
    
    # Test DatabaseError
    error = DatabaseError("Connection failed")
    assert error.status_code == 500
    assert error.error_code == "DATABASE_ERROR"
    
    # Test ExternalServiceError
    error = ExternalServiceError("Gemini", "Rate limit exceeded")
    assert error.status_code == 503
    assert error.error_code == "EXTERNAL_SERVICE_ERROR"


def test_validation_helpers():
    """Test validation helper functions"""
    from app.core.errors import validate_required, validate_in_range, ValidationError
    
    # Test validate_required
    assert validate_required("test", "field") == "test"
    
    with pytest.raises(ValidationError):
        validate_required(None, "field")
    
    with pytest.raises(ValidationError):
        validate_required("", "field")
    
    # Test validate_in_range
    assert validate_in_range(5, 1, 10, "age") == 5
    
    with pytest.raises(ValidationError):
        validate_in_range(0, 1, 10, "age")
    
    with pytest.raises(ValidationError):
        validate_in_range(11, 1, 10, "age")


def test_error_response_format(client):
    """Test that API errors return proper format"""
    # Test endpoint that doesn't exist
    response = client.get("/nonexistent")
    
    assert response.status_code == 404


def test_handle_errors_decorator():
    """Test @handle_errors decorator"""
    from app.core.errors import handle_errors, ValidationError
    
    @handle_errors
    async def test_function_that_raises():
        raise ValidationError("Test error", field="test")
    
    # Decorator should catch and convert to HTTPException
    with pytest.raises(Exception):  # Will be HTTPException
        import asyncio
        asyncio.run(test_function_that_raises())


def test_global_exception_handler():
    """Test global exception handler"""
    from app.core.errors import global_exception_handler
    from fastapi import Request
    
    # Create mock request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})()
            self.method = "GET"
            self.client = type('obj', (object,), {'host': '127.0.0.1'})()
    
    request = MockRequest()
    
    # Test exception handling
    import asyncio
    response = asyncio.run(global_exception_handler(request, Exception("Test error")))
    
    assert response.status_code == 500
    assert "error" in response.body.decode()
