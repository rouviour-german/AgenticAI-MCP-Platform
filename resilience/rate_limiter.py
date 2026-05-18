import asyncio
import time
from typing import Callable, Any

class RateLimitExceeded(Exception):
    pass

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min((1.0 - self.tokens) / self.refill_rate, remaining)
                await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
