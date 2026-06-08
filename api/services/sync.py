from typing import List

from pymongo.collection import Collection

from api.db.chromadb_client import get_chroma_collection
from api.models.game import SyncResponse
from api.services.game_utils import game_to_chroma_metadata, game_to_search_document

BATCH_SIZE = 100


def sync_mongo_to_chroma(
    games_collection: Collection,
    *,
    reset: bool = False,
) -> SyncResponse:
    """
    Index every MongoDB game document into ChromaDB.

    MongoDB remains the source of truth; ChromaDB stores embeddings plus
    lightweight metadata used to link search hits back to MongoDB documents.
    """
    chroma = get_chroma_collection()

    if reset:
        existing_ids = chroma.get(include=[])["ids"]
        if existing_ids:
            chroma.delete(ids=existing_ids)

    total_in_mongo = games_collection.count_documents({})
    synced = 0
    skipped = 0

    cursor = games_collection.find({})

    batch_ids: List[str] = []
    batch_documents: List[str] = []
    batch_metadatas: List[dict] = []

    def flush_batch() -> None:
        nonlocal synced
        if not batch_ids:
            return
        chroma.upsert(
            ids=batch_ids,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )
        synced += len(batch_ids)
        batch_ids.clear()
        batch_documents.clear()
        batch_metadatas.clear()

    for game in cursor:
        mongo_id = str(game["_id"])
        document = game_to_search_document(game)

        if not document:
            skipped += 1
            continue

        batch_ids.append(mongo_id)
        batch_documents.append(document)
        batch_metadatas.append(game_to_chroma_metadata(game))

        if len(batch_ids) >= BATCH_SIZE:
            flush_batch()

    flush_batch()

    return SyncResponse(
        synced=synced,
        skipped=skipped,
        total_in_mongo=total_in_mongo,
        total_in_chroma=chroma.count(),
    )


def index_game(games_collection: Collection, mongo_id: str) -> None:
    """Upsert a single MongoDB game into ChromaDB."""
    from bson import ObjectId

    game = games_collection.find_one({"_id": ObjectId(mongo_id)})
    if not game:
        return

    document = game_to_search_document(game)
    if not document:
        return

    chroma = get_chroma_collection()
    chroma.upsert(
        ids=[mongo_id],
        documents=[document],
        metadatas=[game_to_chroma_metadata(game)],
    )


def remove_game_from_chroma(mongo_id: str) -> None:
    chroma = get_chroma_collection()
    chroma.delete(ids=[mongo_id])
