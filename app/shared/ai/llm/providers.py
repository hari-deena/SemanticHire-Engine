# app/services/llm/providers.py

import logging
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:

    @staticmethod
    def primary():
        logger.info("Using PRIMARY LLM")

        return ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0,
            max_retries=1,
            timeout=30,
        )

    @staticmethod
    def fallback():
        logger.warning("Switching to FALLBACK LLM")

        return ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.FALLBACK_GROQ_MODEL,
            temperature=0,
            max_retries=1,
            timeout=60,
        )