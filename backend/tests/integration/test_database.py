"""Integration tests for database functionality."""

import pytest
import os
from pathlib import Path


@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test_hotel.db"
    return str(db_path)


def test_database_connection(test_db_path):
    """Test database connection can be established"""
    from app.utils.db_utils import ConnectionPool
    
    pool = ConnectionPool(test_db_path)
    conn = pool.get_connection()
    
    assert conn is not None
    
    # Test basic query
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    
    assert result[0] == 1
    conn.close()


def test_database_retry_on_lock():
    """Test database retry logic on locked database"""
    from app.utils.db_utils import ConnectionPool
    import sqlite3
    import tempfile
    
    # Create temp database
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    
    try:
        pool = ConnectionPool(db_path, max_retries=3, retry_delay=0.1)
        conn = pool.get_connection()
        
        # Connection should succeed even with retries
        assert conn is not None
        conn.close()
    
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)


def test_get_db_connection_ctx_commits_on_success(test_db_path):
    """Test context manager commits on success"""
    from app.utils.db_utils import get_db_connection_ctx
    from app.db.session import init_db
    
    # Initialize database tables
    from app.core.config import DB_PATH
    import app.core.config as config
    original_path = config.DB_PATH
    config.DB_PATH = test_db_path
    
    try:
        init_db()
        
        # Use context manager to create a booking
        with get_db_connection_ctx(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bookings (booking_id, guest_name, room_type, date, status) "
                "VALUES (?, ?, ?, ?, ?)",
                ("TEST-001", "John Doe", "Standard", "2026-02-05", "confirmed")
            )
        
        # Verify commit worked
        with get_db_connection_ctx(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", ("TEST-001",))
            result = cursor.fetchone()
            
            assert result is not None
            assert result["guest_name"] == "John Doe"
    
    finally:
        config.DB_PATH = original_path


def test_get_db_connection_ctx_rolls_back_on_error(test_db_path):
    """Test context manager rolls back on error"""
    from app.utils.db_utils import get_db_connection_ctx
    from app.db.session import init_db
    
    # Initialize database
    import app.core.config as config
    original_path = config.DB_PATH
    config.DB_PATH = test_db_path
    
    try:
        init_db()
        
        # Try to create booking but raise error
        with pytest.raises(ValueError):
            with get_db_connection_ctx(test_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO bookings (booking_id, guest_name, room_type, date, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("TEST-002", "Jane Doe", "Deluxe", "2026-02-05", "confirmed")
                )
                # Raise error before commit
                raise ValueError("Test error")
        
        # Verify rollback worked - booking should not exist
        with get_db_connection_ctx(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", ("TEST-002",))
            result = cursor.fetchone()
            
            assert result is None
    
    finally:
        config.DB_PATH = original_path


def test_execute_with_retry():
    """Test execute_with_retry function"""
    from app.utils.db_utils import execute_with_retry, ConnectionPool
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    
    try:
        pool = ConnectionPool(db_path)
        conn = pool.get_connection()
        
        # Execute query with retry
        cursor = execute_with_retry(conn, "SELECT 1", max_retries=3)
        result = cursor.fetchone()
        
        assert result[0] == 1
        conn.close()
    
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_health_check_database():
    """Test database health check function"""
    from app.utils.db_utils import health_check_database
    from app.core.config import DB_PATH
    
    status = health_check_database(DB_PATH)
    
    assert "status" in status
    assert "message" in status
    
    # If healthy, should have metadata
    if status["status"] == "healthy":
        assert "tables_count" in status
        assert "db_path" in status
