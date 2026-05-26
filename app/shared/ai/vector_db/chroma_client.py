# # import chromadb

# # client = chromadb.HttpClient(
# #     host="localhost",
# #     port=8000
# # )

# # collection = client.get_or_create_collection(name="resumes")


# # def store_vectors(vectors, metadatas, ids):

# #     if not vectors:
# #         raise ValueError("No vectors to store")

# #     collection.add(
# #         ids=ids,
# #         embeddings=vectors,
# #         metadatas=metadatas
# #     )
    
    
# # def search_similar(query_vector, top_k=5):
# #     return collection.query(
# #         query_embeddings=[query_vector],
# #         n_results=top_k
# #     )
    
# import chromadb
# from app.core.config import settings

# _client = None
# _collection = None


# def get_client():
#     global _client

#     if _client is None:
#         _client = chromadb.HttpClient(
#             host=settings.CHROMA_HOST,
#             port=settings.CHROMA_PORT
#         )

#     return _client


# def get_collection():
#     global _collection

#     if _collection is None:
#         client = get_client()

#         _collection = client.get_or_create_collection(
#             name=settings.CHROMA_COLLECTION_NAME
#         )

#     return _collection
    
    
# app/shared/ai/vector_db/chroma_client.py

# import chromadb
# from chromadb.config import Settings

# _client = None
# _collection = None


# def get_client():
#     global _client

#     if _client is None:
#         _client = chromadb.Client(
#             Settings(
#                 persist_directory="./chroma_db" , # local storage
#                 is_persistent=True   # ✅ important
#             )
#         )

#     return _client


# def get_collection():
#     global _collection

#     if _collection is None:
#         client = get_client()

#         _collection = client.get_or_create_collection(
#             name="resumes",
#             embedding_function=None   # ✅ CRITICAL FIX
#         )

#     return _collection



import chromadb

_client = None
_collection = None


def get_client():
    global _client

    if _client is None:
        _client = chromadb.HttpClient(
            host="localhost",
            port=8001
        )

    return _client


def get_collection():
    global _collection

    if _collection is None:
        client = get_client()

        _collection = client.get_or_create_collection(
            name="resumes",
            embedding_function=None
        )

    return _collection