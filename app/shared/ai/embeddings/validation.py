import math


def validate_embeddings(chunks, vectors):

    if not chunks or not vectors:
        raise ValueError("Empty chunks or embeddings")

    if len(chunks) != len(vectors):
        raise ValueError("Mismatch between chunks and embeddings")

    first_dim = len(vectors[0])

    if first_dim == 0:
        raise ValueError("Empty embedding vector")

    for i, v in enumerate(vectors):

        if not isinstance(v, list):
            raise ValueError(f"Embedding at index {i} is not a list")

        if len(v) != first_dim:
            raise ValueError(f"Inconsistent embedding dimension at index {i}")

        for val in v:
            if not isinstance(val, (int, float)):
                raise ValueError(f"Non-numeric value at index {i}")

            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Invalid numeric value at index {i}")

    return True