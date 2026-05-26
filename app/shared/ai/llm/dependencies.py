# app/services/llm/dependencies.py

from functools import lru_cache
from .executor import LLMExecutor


@lru_cache(maxsize=1)
def get_llm_executor():
    return LLMExecutor()