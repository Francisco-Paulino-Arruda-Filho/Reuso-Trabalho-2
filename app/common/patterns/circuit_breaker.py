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
    # Time to attempt to close the circuit again (timedelta or seconds as int/float)
    reset_timeout: timedelta = timedelta(minutes=1)
    # Time to wait before retrying a failed operation (timedelta or seconds as int/float)
    retry_timeout: timedelta = timedelta(seconds=10)

    def __post_init__(self):
        # Normalize numeric timeouts to timedelta for convenience
        if isinstance(self.reset_timeout, (int, float)):
            self.reset_timeout = timedelta(seconds=self.reset_timeout)
        if isinstance(self.retry_timeout, (int, float)):
            self.retry_timeout = timedelta(seconds=self.retry_timeout)


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        # Possible states: CLOSED, OPEN, HALF-OPEN
        self.state = CircuitBreakerStatus.CLOSED
        self.error_messages = []
        self.last_failure_time = None

    def has_passed_reset_time(self) -> bool:
        if self.last_failure_time is None:
            return False
        return datetime.now() - self.last_failure_time > self.config.reset_timeout

    def can_retry(self) -> bool:
        if self.state == CircuitBreakerStatus.CLOSED:
            return True

        if self.state == CircuitBreakerStatus.OPEN:
            if self.has_passed_reset_time():
                self.state = CircuitBreakerStatus.HALF_OPEN
                return True
            return False

        if self.state == CircuitBreakerStatus.HALF_OPEN:
            return True

        return False

    def record_failure(self, error_message: str = None):
        self.failure_count += 1
        if error_message:
            self.error_messages.append(
                f"{datetime.now().isoformat()}: {error_message}")
        else:
            self.error_messages.append(
                f"Failure at {datetime.now().isoformat()}")
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerStatus.HALF_OPEN:
            self.state = CircuitBreakerStatus.OPEN
            return

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerStatus.OPEN

    def record_success(self):
        if self.state == CircuitBreakerStatus.HALF_OPEN:
            self.state = CircuitBreakerStatus.CLOSED

        self.failure_count = 0
        self.error_messages = []
        self.last_failure_time = None


async def retry_with_circuit_breaker(
    operation: callable,
    circuit_breaker: CircuitBreaker,
    backoff: ExponentialBackoff
):
    """Retry an operation using circuit breaker and exponential backoff."""

    while True:
        if not circuit_breaker.can_retry():
            raise Exception(
                f"Circuit breaker is open. \n Failures: {circuit_breaker.error_messages}")

        try:
            if inspect.iscoroutinefunction(operation):
                result = await operation()
            else:
                result = await asyncio.to_thread(operation)

            circuit_breaker.record_success()

            backoff.reset()

            return result
        except Exception as e:
            circuit_breaker.record_failure(error_message=str(e))
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
