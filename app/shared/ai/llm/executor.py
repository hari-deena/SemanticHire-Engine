# # app/services/llm/executor.py

import time
import logging
from ..llm.providers import LLMProvider
from ..llm.circuit_breaker import CircuitBreaker
from ..llm.monitor import LLMMonitor

logger = logging.getLogger(__name__)


# app/services/llm/executor.py
class LLMExecutor:

    def __init__(self):
        self.primary = LLMProvider.primary()
        self.fallback = LLMProvider.fallback()
        self.circuit_breaker = CircuitBreaker()

    def execute(self, chain, payload):

        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit open → fallback")
            raise RuntimeError("Circuit open")

        try:
            return chain.invoke(payload)

        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"LLM failed: {str(e)}")
            raise