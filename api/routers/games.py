from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from api.db.mongodb import get_games_collection
from api.models.game import GameInput, GameOutput
from api.services.game_utils import doc_to_game_output, parse_object_id
from api.services.sync import index_game, remove_game_from_chroma

router = APIRouter(prefix="api/v1/games", tags=["games"])


@router.get("/", response_model=List[GameOutput])
def list_games() -> List[GameOutput]:
    collection = get_games_collection()
    return [doc_to_game_output(game) for game in collection.find()]


@router.get("/search", response_model=List[GameOutput])
def search_games_by_name(q: str = Query(..., min_length=1)) -> List[GameOutput]:
    collection = get_games_collection()
    games = collection.find({"name": {"$regex": q, "$options": "i"}})
    return [doc_to_game_output(game) for game in games]


@router.get("search/{game_id}", response_model=GameOutput)
def get_game(game_id: str) -> GameOutput:
    collection = get_games_collection()
    try:
        object_id = parse_object_id(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    game = collection.find_one({"_id": object_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return doc_to_game_output(game)


@router.post("/", response_model=GameOutput, status_code=201)
def create_game(game: GameInput) -> GameOutput:
    collection = get_games_collection()
    result = collection.insert_one(game.model_dump())
    created_game = collection.find_one({"_id": result.inserted_id})
    mongo_id = str(result.inserted_id)
    index_game(collection, mongo_id)
    return doc_to_game_output(created_game)


@router.put("/{game_id}", response_model=GameOutput)
def update_game(game_id: str, game: GameInput) -> GameOutput:
    collection = get_games_collection()
    try:
        object_id = parse_object_id(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = collection.update_one(
        {"_id": object_id},
        {"$set": game.model_dump()},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")

    updated_game = collection.find_one({"_id": object_id})
    index_game(collection, game_id)
    return doc_to_game_output(updated_game)


@router.delete("/{game_id}")
def delete_game(game_id: str) -> dict:
    collection = get_games_collection()
    try:
        object_id = parse_object_id(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")

    remove_game_from_chroma(game_id)
    return {"message": "Game deleted"}
