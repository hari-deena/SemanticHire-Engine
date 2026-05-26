

# app/services/llm/monitor.py

import time
import logging

logger = logging.getLogger(__name__)


class LLMMonitor:

    @staticmethod
    def track(func):
        def wrapper(*args, **kwargs):
            start = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start

                logger.info(f"LLM success | {duration:.2f}s")
                return result

            except Exception as e:
                duration = time.time() - start

                logger.error(f"LLM failed | {duration:.2f}s | {str(e)}")
                raise

        return wrapper