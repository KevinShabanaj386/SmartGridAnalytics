"""
Enhanced Resilience Patterns për API Gateway
Implementon advanced retry, circuit breaker, dhe fallback mechanisms
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

class EnhancedCircuitBreaker:
    """Enhanced Circuit Breaker me metrics dhe adaptive thresholds"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.total_calls = 0
        self.total_failures = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_calls += 1
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.half_open_calls = 0
                logger.info("Circuit breaker moved to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                # Too many calls in half-open, close circuit again
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
                raise CircuitBreakerOpenError("Circuit breaker re-opened")
            self.half_open_calls += 1
        
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
                self.half_open_calls = 0
                logger.info("Circuit breaker CLOSED (recovered)")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPENED (failures: {self.failure_count}, "
                f"failure rate: {self.total_failures/self.total_calls*100:.2f}%)"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        failure_rate = (self.total_failures / self.total_calls * 100) if self.total_calls > 0 else 0
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'failure_rate': f"{failure_rate:.2f}%",
            'last_failure_time': self.last_failure_time
        }

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator me exponential backoff dhe jitter
    
    Args:
        max_retries: Numri maksimal i retries
        initial_delay: Delay fillestar (seconds)
        max_delay: Delay maksimal (seconds)
        exponential_base: Base për exponential backoff
        jitter: Add random jitter për të shmangur thundering herd
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
                        # Add jitter për të shmangur synchronized retries
                        if jitter:
                            import random
                            jitter_amount = delay * 0.1 * random.random()
                            actual_delay = min(delay + jitter_amount, max_delay)
                        else:
                            actual_delay = min(delay, max_delay)
                        
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {actual_delay:.2f}s: {str(e)}"
                        )
                        time.sleep(actual_delay)
                        delay *= exponential_base
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        return wrapper
    return decorator

def fallback_with_cache(
    default_value: Any = None,
    fallback_func: Optional[Callable] = None,
    cache_key: Optional[str] = None,
    cache_ttl: int = 300
):
    """
    Fallback decorator me caching për fallback results
    
    Args:
        default_value: Value për të kthyer në rast dështimi
        fallback_func: Function për të ekzekutuar në rast dështimi
        cache_key: Key për caching (optional)
        cache_ttl: Cache TTL në seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback triggered for {func.__name__}: {str(e)}")
                
                # Try cache first
                if cache_key:
                    try:
                        import redis
                        redis_client = redis.Redis(
                            host=os.getenv('REDIS_HOST', 'smartgrid-redis'),
                            port=int(os.getenv('REDIS_PORT', 6379)),
                            decode_responses=True
                        )
                        cached = redis_client.get(f"fallback:{cache_key}")
                        if cached:
                            logger.info(f"Using cached fallback for {func.__name__}")
                            return json.loads(cached)
                    except Exception:
                        pass
                
                # Execute fallback
                if fallback_func:
                    result = fallback_func(*args, **kwargs)
                    
                    # Cache result
                    if cache_key and result:
                        try:
                            redis_client.setex(
                                f"fallback:{cache_key}",
                                cache_ttl,
                                json.dumps(result)
                            )
                        except Exception:
                            pass
                    
                    return result
                
                return default_value
        return wrapper
    return decorator

# Global circuit breakers për different services
service_circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}

def get_circuit_breaker(service_name: str) -> EnhancedCircuitBreaker:
    """Get or create circuit breaker për service"""
    if service_name not in service_circuit_breakers:
        service_circuit_breakers[service_name] = EnhancedCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=2
        )
    return service_circuit_breakers[service_name]

