"""
Resilience Patterns për Data Processing Service
Implementon retry, circuit breaker, dhe fallback mechanisms
"""
import time
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit Breaker pattern implementation"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker moved to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_success(self):
        """Record successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED (recovered)")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED (failures: {self.failure_count})")

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator me exponential backoff
    
    Args:
        max_retries: Numri maksimal i retries
        initial_delay: Delay fillestar (seconds)
        max_delay: Delay maksimal (seconds)
        exponential_base: Base për exponential backoff
        exceptions: Exceptions për të retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {str(e)}"
                        )
                        time.sleep(min(delay, max_delay))
                        delay *= exponential_base
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        return wrapper
    return decorator

def fallback(default_value: Any = None, fallback_func: Optional[Callable] = None):
    """
    Fallback decorator për të kthyer default value ose ekzekutuar fallback function
    
    Args:
        default_value: Value për të kthyer në rast dështimi
        fallback_func: Function për të ekzekutuar në rast dështimi
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback triggered for {func.__name__}: {str(e)}")
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                return default_value
        return wrapper
    return decorator

# Global circuit breakers për different operations
db_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=2
)

kafka_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=1
)

