from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Callable, Optional
from app.common.patterns.retry import ExponentialBackoff
import asyncio
import inspect


class CircuitBreakerStatus(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5  # Number of failures to open the circuit
    # Time in seconds to attempt to close the circuit again
    reset_timeout: timedelta = timedelta(minutes=1)
    # Time in seconds to wait before retrying a failed operation
    retry_timeout: timedelta = timedelta(seconds=10)


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        # Possible states: CLOSED, OPEN, HALF-OPEN
        self.state = CircuitBreakerStatus.CLOSED
        self.last_failure_time = None

    def has_passed_reset_time(self) -> bool:
        return datetime.now() - self.last_failure_time > self.config.reset_timeout

    def can_retry(self) -> bool:
        if self.state == CircuitBreakerStatus.CLOSED:
            return True

        if self.state == CircuitBreakerStatus.OPEN and self.has_passed_reset_time():
            self.state = CircuitBreakerStatus.HALF_OPEN
            return True

        return True

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerStatus.OPEN

    def record_success(self):
        if self.state == CircuitBreakerStatus.HALF_OPEN:
            self.state = CircuitBreakerStatus.CLOSED

        self.failure_count = 0
        self.last_failure_time = None


async def retry_with_circuit_breaker(
    operation: callable,
    circuit_breaker: CircuitBreaker,
    backoff: ExponentialBackoff
):
    while True:
        if not circuit_breaker.can_retry():
            raise Exception("Circuit breaker is open")

        try:
            result = await operation()
            circuit_breaker.record_success()
            return result
        except Exception as e:
            circuit_breaker.record_failure()
            delay = backoff.next_delay()
            if delay is None:
                raise e
            await asyncio.sleep(delay)


# Instância global do circuit breaker (compartilhada entre rotas)
_default_circuit_breaker = CircuitBreaker(CircuitBreakerConfig())


def with_retry_and_circuit_breaker(
    circuit_breaker: Optional[CircuitBreaker] = None,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    max_attempts: int = 3,
    jitter: bool = True,
):
    """
    Decorator que aplica retry com exponential backoff e circuit breaker.

    Uso:
        @app.get("/rota")
        @with_retry_and_circuit_breaker()
        async def minha_rota():
            ...

        @app.post("/outra-rota")
        @with_retry_and_circuit_breaker(max_attempts=5, initial_delay=0.5)
        async def outra_rota():
            ...
    """
    cb = circuit_breaker or _default_circuit_breaker

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(
                initial_delay=initial_delay,
                max_delay=max_delay,
                max_attemps=max_attempts,
                jitter=jitter,
            )

            async def operation():
                return await func(*args, **kwargs)

            return await retry_with_circuit_breaker(operation, cb, backoff)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(
                initial_delay=initial_delay,
                max_delay=max_delay,
                max_attemps=max_attempts,
                jitter=jitter,
            )

            async def operation():
                return func(*args, **kwargs)

            return asyncio.run(retry_with_circuit_breaker(operation, cb, backoff))

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
