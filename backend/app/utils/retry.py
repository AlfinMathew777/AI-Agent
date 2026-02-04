"""
Enhanced retry logic with exponential backoff for external API calls.

This module provides decorators and utilities for handling:
- Transient failures with exponential backoff
- Rate limiting and quota errors
- Timeout handling
- Circuit breaker pattern
"""

import time
import logging
import functools
from typing import Callable, Optional, Tuple, Type
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        timeout: Optional[float] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.timeout = timeout
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        import random
        
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Increment failure count and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Retryable errors include:
    - Network timeouts
    - Temporary service unavailability (503)
    - Rate limits (429) - with longer delays
    - Connection errors
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__
    
    # Network/connection errors
    if any(keyword in error_type.lower() for keyword in [
        "timeout", "connection", "network"
    ]):
        return True
    
    # HTTP status codes
    if any(code in error_str for code in ["503", "502", "504"]):
        return True
    
    # Rate limiting (special handling needed)
    if "429" in error_str or "rate limit" in error_str:
        return True
    
    return False


def is_quota_error(exception: Exception) -> bool:
    """Check if error is related to API quota/limits"""
    error_str = str(exception).lower()
    error_type = type(exception).__name__
    
    return any(keyword in error_str for keyword in [
        "quota", "resourceexhausted", "limit exceeded"
    ]) or "429" in error_str or "ResourceExhausted" in error_type


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    fallback_value: Optional[any] = None,
    on_retry_callback: Optional[Callable] = None
):
    """
    Decorator to retry functions with exponential backoff.
    
    Args:
        config: Retry configuration
        fallback_value: Value to return if all retries fail
        on_retry_callback: Function to call before each retry
    
    Example:
        @retry_with_backoff(config=RetryConfig(max_retries=3))
        async def call_api():
            # Your code here
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Success - log if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.error(
                            f"{func.__name__} failed with non-retryable error: {e}"
                        )
                        break
                    
                    # Last attempt - don't wait
                    if attempt == config.max_retries:
                        break
                    
                    # Calculate delay
                    delay = config.get_delay(attempt)
                    
                    # Special handling for quota errors (longer delay)
                    if is_quota_error(e):
                        delay = max(delay, 60.0)  # At least 1 minute for quota errors
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): "
                        f"{type(e).__name__}: {str(e)[:100]}"
                        f" - Retrying in {delay:.1f}s"
                    )
                    
                    # Call retry callback if provided
                    if on_retry_callback:
                        on_retry_callback(attempt, e, delay)
                    
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(delay)
            
            # All retries exhausted
            logger.error(
                f"{func.__name__} failed after {config.max_retries + 1} attempts. "
                f"Last error: {last_exception}"
            )
            
            # Return fallback value if provided
            if fallback_value is not None:
                logger.info(f"Returning fallback value for {func.__name__}")
                return fallback_value
            
            # Re-raise last exception
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_error(e):
                        logger.error(
                            f"{func.__name__} failed with non-retryable error: {e}"
                        )
                        break
                    
                    if attempt == config.max_retries:
                        break
                    
                    delay = config.get_delay(attempt)
                    
                    if is_quota_error(e):
                        delay = max(delay, 60.0)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries + 1}): "
                        f"{type(e).__name__}: {str(e)[:100]}"
                        f" - Retrying in {delay:.1f}s"
                    )
                    
                    if on_retry_callback:
                        on_retry_callback(attempt, e, delay)
                    
                    time.sleep(delay)
            
            logger.error(
                f"{func.__name__} failed after {config.max_retries + 1} attempts. "
                f"Last error: {last_exception}"
            )
            
            if fallback_value is not None:
                logger.info(f"Returning fallback value for {func.__name__}")
                return fallback_value
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
