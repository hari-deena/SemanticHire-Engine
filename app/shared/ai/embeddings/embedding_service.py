# import logging
# from langchain_openai import OpenAIEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings

# from app.core.config import settings
# from app.shared.ai.embeddings.embedding_cache import get_many, set_many
# from app.shared.ai.embeddings.circuit_breaker import CircuitBreaker

# logger = logging.getLogger(__name__)


# class EmbeddingService:

#     def __init__(self):

#         self.primary = None
#         self.fallback = None
#         self.breaker = CircuitBreaker()

#         self._init_models()

#     # 🔥 MISSING METHOD (THIS IS YOUR BUG)
#     def _init_models(self):

#         # OpenAI (primary)
#         try:
#             logger.info("init_openai_embeddings")

#             self.primary = OpenAIEmbeddings(
#                 model=settings.EMBEDDING_MODEL,
#                 api_key=settings.OPENAI_API_KEY,
#                 request_timeout=settings.EMBEDDING_TIMEOUT,
#                 max_retries=2
#             )

#         except Exception as e:
#             logger.warning(f"openai_init_failed: {e}")

#         # HuggingFace (fallback)
#         try:
#             logger.info("init_hf_embeddings")

#             self.fallback = HuggingFaceEmbeddings(
#                 model_name=settings.EMBEDDING_MODEL_HF,
#                 model_kwargs={"device": "cpu"},
#                 encode_kwargs={"normalize_embeddings": True}
#             )

#         except Exception as e:
#             logger.critical(f"hf_init_failed: {e}")

#         if not self.primary and not self.fallback:
#             raise RuntimeError("No embedding providers available")

#     # 🔥 MAIN LOGIC
#     def embed(self, texts):

#         if not texts:
#             return []

#         # 🔥 CACHE
#         cache_hits = get_many(texts)
#         uncached = [t for t in texts if t not in cache_hits]

#         results = {}
#         results.update(cache_hits)

#         # 🔥 CIRCUIT BREAKER
#         if not self.breaker.allow_request():
#             raise RuntimeError("Embedding service temporarily disabled")

#         try:
#             if self.primary and uncached:
#                 logger.info("using_openai_embeddings")

#                 vectors = self.primary.embed_documents(uncached)

#                 set_many(uncached, vectors)

#                 for t, v in zip(uncached, vectors):
#                     results[t] = v

#                 self.breaker.record_success()

#         except Exception as e:
#             logger.warning(f"openai_failed_switching_to_hf: {e}")
#             self.breaker.record_failure()

#             if self.fallback:
#                 logger.info("using_huggingface_embeddings")

#                 vectors = self.fallback.embed_documents(uncached)

#                 set_many(uncached, vectors)

#                 for t, v in zip(uncached, vectors):
#                     results[t] = v
#             else:
#                 raise RuntimeError("No embedding provider available")

#         return [results[t] for t in texts]


# # 🔥 SINGLE INSTANCE (Celery-safe)
# _embedding_service = EmbeddingService()


# def generate_embeddings(texts):
#     return _embedding_service.embed(texts)



# app/shared/ai/embeddings/embedding_service.py

import logging
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings
from app.shared.ai.embeddings.embedding_cache import get_many, set_many

logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(self):

        try:
            logger.info("init_hf_embeddings")

            self.model = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_HF,
                model_kwargs={"device": "cpu"},  # change to cuda if GPU
                encode_kwargs={"normalize_embeddings": True}
            )

        except Exception as e:
            logger.critical(f"hf_init_failed: {e}")
            raise RuntimeError("Embedding model failed to initialize")

    def embed(self, texts):

        if not texts:
            return []

        # 🔥 CACHE
        cache_hits = get_many(texts)
        uncached = [t for t in texts if t not in cache_hits]

        results = {}
        results.update(cache_hits)

        if uncached:
            logger.info(f"encoding_{len(uncached)}_texts")

            vectors = self.model.embed_documents(uncached)

            set_many(uncached, vectors)

            for t, v in zip(uncached, vectors):
                results[t] = v

        return [results[t] for t in texts]


# ✅ SINGLETON
_embedding_service = EmbeddingService()


def generate_embeddings(texts):
    return _embedding_service.embed(texts)