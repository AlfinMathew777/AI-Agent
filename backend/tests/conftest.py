"""pytest configuration for tests."""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["ADMIN_API_KEY"] = "test-admin-key-12345"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Don't require AI service for tests
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "test-key-not-real"
    
    yield
    
    # Cleanup handled automatically


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for tests"""
    db_path = tmp_path / "test.db"
    return str(db_path)
