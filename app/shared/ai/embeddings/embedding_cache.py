import redis
import json
import hashlib
from app.core.config import settings

# 🔥 Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=2,
    decode_responses=True
)


def _hash_text(text: str) -> str:
    """
    Generate unique hash for text
    """
    return hashlib.sha256(text.encode()).hexdigest()


def get_many(texts: list[str]) -> dict:
    """
    Bulk fetch cached embeddings
    """
    keys = [_hash_text(t) for t in texts]
    values = redis_client.mget(keys)

    result = {}

    for text, val in zip(texts, values):
        if val:
            result[text] = json.loads(val)

    return result


def set_many(texts: list[str], vectors: list[list[float]]):
    """
    Bulk store embeddings in Redis
    """
    pipe = redis_client.pipeline()

    for text, vector in zip(texts, vectors):
        key = _hash_text(text)

        pipe.setex(
            key,
            settings.EMBEDDING_CACHE_TTL,  # e.g. 86400 (1 day)
            json.dumps(vector)
        )

    pipe.execute()