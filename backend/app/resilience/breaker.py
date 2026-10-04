import time
from typing import Literal


class CircuitBreakerOpenError(Exception):
    def __init__(self, service_name: str, reset_timeout: float) -> None:
        super().__init__(f"Circuit breaker for service '{service_name}' is OPEN. Retry in {reset_timeout:.1f}s.")
        self.service_name = service_name
        self.reset_timeout = reset_timeout


class CircuitBreaker:
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_time_seconds: float = 30.0,
    ) -> None:
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state: Literal["CLOSED", "OPEN", "HALF_OPEN"] = "CLOSED"

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def check_state(self) -> None:
        now = time.monotonic()
        if self.state == "OPEN":
            if now - self.last_failure_time >= self.recovery_time_seconds:
                self.state = "HALF_OPEN"
            else:
                remaining = self.recovery_time_seconds - (now - self.last_failure_time)
                raise CircuitBreakerOpenError(self.service_name, remaining)
