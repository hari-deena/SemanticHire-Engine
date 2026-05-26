import logging
from typing import List

from app.shared.ai.vector_db.chroma_client import get_collection

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def validate_store_input(vectors, metadatas, ids):

    if not vectors or not metadatas or not ids:
        raise ValueError("Vectors, metadata, or ids cannot be empty")

    if not (len(vectors) == len(metadatas) == len(ids)):
        raise ValueError("Mismatch between vectors, metadata, and ids")


def store_vectors(
    vectors: List[List[float]],
    metadatas: List[dict],
    ids: List[str],
    documents: List[str] = None
):

    validate_store_input(vectors, metadatas, ids)

    collection = get_collection()
    total = len(vectors)

    logger.info(
        "vector_store_started",
        extra={"count": total}
    )

    try:
        for i in range(0, total, BATCH_SIZE):

            batch_vectors = vectors[i:i + BATCH_SIZE]
            batch_meta = metadatas[i:i + BATCH_SIZE]
            batch_ids = ids[i:i + BATCH_SIZE]
            documents=documents[i:i+BATCH_SIZE]

            # 🔥 Use UPSERT (important for production)
            collection.upsert(
                ids=batch_ids,
                embeddings=batch_vectors,
                metadatas=batch_meta,
                documents=documents
            )

        logger.info(
            "vector_store_completed",
            extra={"stored": total}
        )

    except Exception as e:
        logger.exception(
            "vector_store_failed",
            extra={"error": str(e)}
        )
        raise