"""Database utilities with enhanced resilience and error handling."""

import sqlite3
import logging
import time
from contextlib import contextmanager
from typing import Optional, Generator
from functools import wraps

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class ConnectionPool:
    """
    Simple connection pooling for SQLite.
    
    Note: SQLite doesn't benefit from traditional connection pooling like PostgreSQL,
    but this helps manage connection lifecycle and retries.
    """
    
    def __init__(self, db_path: str, max_retries: int = 3, retry_delay: float = 0.5):
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with retry logic.
        
        Retries on:
        - Database locked errors
        - Disk I/O errors
        - Connection failures
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=10.0,  # Wait up to 10s on locks
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                
                # Test connection
                conn.execute("SELECT 1")
                
                return conn
            
            except sqlite3.Error as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if retryable
                if any(keyword in error_str for keyword in [
                    "locked", "busy", "i/o error"
                ]):
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Database connection attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {self.retry_delay}s..."
                        )
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                
                # Non-retryable error
                logger.error(f"Database connection failed: {e}")
                raise DatabaseError(f"Failed to connect to database: {e}")
        
        # All retries exhausted
        raise DatabaseError(
            f"Failed to connect after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )


@contextmanager
def get_db_connection_ctx(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections with automatic cleanup.
    
    Usage:
        with get_db_connection_ctx(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            conn.commit()
    """
    pool = ConnectionPool(db_path)
    conn = None
    
    try:
        conn = pool.get_connection()
        yield conn
        conn.commit()
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation failed, rolled back: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


def with_db_retry(max_retries: int = 3):
    """
    Decorator to retry database operations on transient failures.
    
    Example:
        @with_db_retry(max_retries=3)
        def get_user(user_id):
            conn = get_db_connection()
            # ... database operations
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except sqlite3.OperationalError as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Retryable errors
                    if any(keyword in error_str for keyword in [
                        "locked", "busy", "database is locked"
                    ]):
                        if attempt < max_retries - 1:
                            delay = 0.5 * (2 ** attempt)
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}): {e}. "
                                f"Retrying in {delay}s..."
                            )
                            time.sleep(delay)
                            continue
                    
                    # Non-retryable error
                    raise
                
                except Exception as e:
                    logger.error(f"{func.__name__} failed with unexpected error: {e}")
                    raise
            
            # All retries exhausted
            raise DatabaseError(
                f"{func.__name__} failed after {max_retries} attempts. "
                f"Last error: {last_error}"
            )
        
        return wrapper
    return decorator


def execute_with_retry(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    max_retries: int = 3
) -> sqlite3.Cursor:
    """
    Execute a query with retry logic for transient failures.
    
    Args:
        conn: Database connection
        query: SQL query
        params: Query parameters
        max_retries: Maximum retry attempts
    
    Returns:
        Cursor with query results
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
        
        except sqlite3.OperationalError as e:
            last_error = e
            error_str = str(e).lower()
            
            if "locked" in error_str or "busy" in error_str:
                if attempt < max_retries - 1:
                    delay = 0.5 * (2 ** attempt)
                    logger.warning(
                        f"Query execution failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
            
            raise
    
    raise DatabaseError(
        f"Query execution failed after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


def safe_execute(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False
):
    """
    Safely execute a query with automatic error handling and optional fetch.
    
    Args:
        conn: Database connection
        query: SQL string
        params: Query parameters
        fetch_one: Return single row
        fetch_all: Return all rows
    
    Returns:
        Query results or None on error
    """
    try:
        cursor = execute_with_retry(conn, query, params)
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        
        return cursor
    
    except Exception as e:
        logger.error(
            f"Safe execute failed for query: {query[:100]}... Error: {e}"
        )
        return None


def health_check_database(db_path: str) -> dict:
    """
    Perform comprehensive database health check.
    
    Returns:
        Dict with status and metadata
    """
    try:
        pool = ConnectionPool(db_path, max_retries=2)
        conn = pool.get_connection()
        
        # Basic connectivity test
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        
        # Get database stats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_bytes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "tables_count": len(tables),
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "db_path": db_path,
            "message": "Database is healthy"
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "db_path": db_path,
            "message": f"Database health check failed: {e}"
        }
