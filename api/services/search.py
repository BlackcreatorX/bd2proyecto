from typing import List, Optional

from bson import ObjectId
from pymongo.collection import Collection

from api.db.chromadb_client import get_chroma_collection
from api.models.game import GameOutput, SemanticSearchResult
from api.services.game_utils import doc_to_game_output


def semantic_search(
    query: str,
    *,
    limit: int = 10,
    hydrate: bool = True,
    games_collection: Optional[Collection] = None,
) -> List[SemanticSearchResult]:
    """
    Run a vector search in ChromaDB and optionally load full documents from MongoDB.
    """
    chroma = get_chroma_collection()
    results = chroma.query(
        query_texts=[query],
        n_results=limit,
        include=["metadatas", "distances", "documents"],
    )

    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    hits: List[SemanticSearchResult] = []

    for mongo_id, metadata, distance in zip(ids, metadatas, distances):
        score = 1.0 - distance if distance is not None else 0.0
        game: Optional[GameOutput] = None

        if hydrate and games_collection is not None:
            doc = games_collection.find_one({"_id": ObjectId(mongo_id)})
            if doc:
                game = doc_to_game_output(doc)

        hits.append(
            SemanticSearchResult(
                mongo_id=mongo_id,
                steam_appid=metadata.get("steam_appid"),
                name=metadata.get("name", ""),
                short_description=metadata.get("short_description", ""),
                score=round(score, 4),
                game=game,
            )
        )

    return hits
