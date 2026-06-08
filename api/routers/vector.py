from typing import List

from fastapi import APIRouter, Query

from api.db.mongodb import get_games_collection
from api.models.game import SemanticSearchResult, SyncResponse
from api.services.search import semantic_search
from api.services.sync import sync_mongo_to_chroma

router = APIRouter(prefix="/vector", tags=["vector-search"])


@router.post("/sync", response_model=SyncResponse)
def sync_games(reset: bool = Query(False, description="Delete existing vectors before re-indexing")) -> SyncResponse:
    """Read all games from MongoDB and upsert them into ChromaDB."""
    return sync_mongo_to_chroma(get_games_collection(), reset=reset)


@router.get("/search", response_model=List[SemanticSearchResult])
def vector_search(
    q: str = Query(..., min_length=1, description="Natural-language search query"),
    limit: int = Query(10, ge=1, le=50),
    hydrate: bool = Query(True, description="Attach full MongoDB documents to each hit"),
) -> List[SemanticSearchResult]:
    """
    Semantic search powered by ChromaDB.

    Example: `q=open world survival crafting` finds games by meaning, not just keyword match.
    """
    collection = get_games_collection() if hydrate else None
    return semantic_search(q, limit=limit, hydrate=hydrate, games_collection=collection)
