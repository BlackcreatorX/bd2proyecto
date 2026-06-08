from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from api.config import CHROMA_COLLECTION, CHROMA_HOST, CHROMA_PORT


@lru_cache
def get_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


def get_chroma_collection() -> Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
