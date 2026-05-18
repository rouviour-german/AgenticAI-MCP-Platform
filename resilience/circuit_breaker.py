import time
from enum import Enum

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, half_open_max: int = 1):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time: float | None = None
        self.half_open_count = 0
        self.half_open_max = half_open_max

    def check(self) -> None:
        if self.state == CircuitState.CLOSED:
            return
        if self.state == CircuitState.OPEN:
            if self._should_try_recovery():
                self.state = CircuitState.HALF_OPEN
                self.half_open_count = 0
                return
            raise CircuitOpenError("Circuit is OPEN — server is down")
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_count < self.half_open_max:
                self.half_open_count += 1
                return
            raise CircuitOpenError("Circuit is HALF_OPEN — waiting for test result")

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_try_recovery(self) -> bool:
        if self.last_failure_time is None:
            return True
        return (time.monotonic() - self.last_failure_time) > self.recovery_timeout
