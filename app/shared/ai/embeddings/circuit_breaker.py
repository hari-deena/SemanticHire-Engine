import time


class CircuitBreaker:
    """
    Simple circuit breaker to prevent repeated failures
    """

    def __init__(self, failure_threshold=5, recovery_time=30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED | OPEN

    def allow_request(self) -> bool:
        """
        Check if requests are allowed
        """

        if self.state == "OPEN":
            # Check if recovery time passed
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "CLOSED"
                self.failure_count = 0
                return True

            return False

        return True

    def record_success(self):
        """
        Reset on success
        """
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """
        Record failure and open circuit if threshold reached
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"