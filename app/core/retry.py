import random
from typing import Callable
import asyncio


class ExponentialBackoff:
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        max_attemps: int = 5,
        jitter: bool = True  # jitter: param
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_attemps = max_attemps
        self.jitter = jitter
        self.attempt = 0

    def reset(self):
        self.attempt = 0

    def next_delay(self):
        if self.attempt >= self.max_attemps:
            return None

        delay = min(self.initial_delay * (2 ** self.attempt), self.max_delay)

        if self.jitter:
            delay *= (0.5 * random.random())

        self.attempt += 1
        return delay


async def retry_operation(operation: Callable, backoff: ExponentialBackoff):
    last_exception = None

    while (delay := backoff.next_delay()) is not None:
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            await asyncio.sleep(delay)

    raise last_exception
