"""
Resilience Patterns për Analytics Service
"""
from data_processing_service.resilience import (
    CircuitBreaker, CircuitBreakerOpenError, retry_with_backoff, fallback
)
import logging

logger = logging.getLogger(__name__)

# Circuit breakers për analytics operations
ml_model_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60,
    success_threshold=1
)

cache_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    success_threshold=2
)

