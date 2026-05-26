
# app/services/llm/circuit_breaker.py

import time


class CircuitBreaker:

    def __init__(self, failure_threshold=3, recovery_time=30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = None

    def can_execute(self):
        if self.failures < self.failure_threshold:
            return True

        if self.last_failure_time and (
            time.time() - self.last_failure_time > self.recovery_time
        ):
            self.reset()
            return True

        return False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

    def reset(self):
        self.failures = 0
        self.last_failure_time = None