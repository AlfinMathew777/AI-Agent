"""Redis utilities with error handling and graceful fallback."""

import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Redis is optional - application should work without it
REDIS_AVAILABLE = False
redis_client: Optional[Any] = None

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis not installed - queue functionality will be disabled")
    redis = None


class RedisConnectionError(Exception):
    """Custom exception for Redis connection issues"""
    pass


def get_redis_client(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    decode_responses: bool = True,
    max_retries: int = 3
) -> Optional[Any]:
    """
    Get Redis client with retry logic.
    Returns None if Redis is unavailable (graceful degradation).
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        decode_responses: Decode byte responses to strings
        max_retries: Maximum connection attempts
    
    Returns:
        Redis client or None if unavailable
    """
    global redis_client
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis is not available - operations will be skipped")
        return None
    
    if redis_client is not None:
        return redis_client
    
    for attempt in range(max_retries):
        try:
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            client.ping()
            
            redis_client = client
            logger.info(f"Redis connected successfully to {host}:{port}")
            return client
        
        except Exception as e:
            logger.warning(
                f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt == max_retries - 1:
                logger.error(
                    "Redis connection failed after all retries - "
                    "continuing without Redis"
                )
                return None
    
    return None


def health_check_redis() -> dict:
    """
    Check Redis health status.
    
    Returns:
        Dict with status and metadata
    """
    if not REDIS_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Redis package not installed",
            "required": False
        }
    
    try:
        client = get_redis_client(max_retries=1)
        
        if client is None:
            return {
                "status": "unavailable",
                "message": "Redis not connected",
                "required": False
            }
        
        # Test ping
        client.ping()
        
        # Get info
        info = client.info()
        
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "message": "Redis is healthy"
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Redis health check failed",
            "required": False
        }


def with_redis_fallback(fallback_value=None):
    """
    Decorator to gracefully handle Redis unavailability.
    
    If Redis is not available or operation fails, returns fallback_value.
    
    Example:
        @with_redis_fallback(fallback_value=[])
        def get_cached_items():
            client = get_redis_client()
            return client.lrange("items", 0, -1)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if not REDIS_AVAILABLE:
                    logger.debug(
                        f"{func.__name__} skipped - Redis not available"
                    )
                    return fallback_value
                
                return func(*args, **kwargs)
            
            except Exception as e:
                logger.warning(
                    f"{func.__name__} failed: {e}. "
                    f"Returning fallback value: {fallback_value}"
                )
                return fallback_value
        
        return wrapper
    return decorator


# Example usage functions

@with_redis_fallback(fallback_value=None)
def cache_set(key: str, value: str, expire: int = 300) -> bool:
    """
    Set value in Redis cache with expiration.
    Returns None if Redis unavailable.
    """
    client = get_redis_client()
    if client:
        return client.setex(key, expire, value)
    return None


@with_redis_fallback(fallback_value=None)
def cache_get(key: str) -> Optional[str]:
    """
    Get value from Redis cache.
    Returns None if Redis unavailable or key doesn't exist.
    """
    client = get_redis_client()
    if client:
        return client.get(key)
    return None


@with_redis_fallback(fallback_value=False)
def cache_delete(key: str) -> bool:
    """
    Delete key from Redis cache.
    Returns False if Redis unavailable.
    """
    client = get_redis_client()
    if client:
        return bool(client.delete(key))
    return False


def close_redis_connection():
    """Close Redis connection if exists"""
    global redis_client
    
    if redis_client:
        try:
            redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            redis_client = None
