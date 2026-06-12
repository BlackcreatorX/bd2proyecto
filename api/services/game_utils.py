from typing import Any, Dict, List, Optional

from bson import ObjectId

from api.models.game import GameOutput

from typing import Any, Dict, List, Optional

from bson import ObjectId

from api.models.game import GameOutput


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []
def doc_to_game_output(doc: dict) -> GameOutput:
    return GameOutput(
        id=str(doc["_id"]),
        updated_at=doc.get("updated_at", ""),
        type=doc.get("type"),
        name=doc.get("name"),
        steam_appid=doc.get("steam_appid"),
        required_age=doc.get("required_age"),
        is_free=doc.get("is_free"),
        detailed_description=doc.get("detailed_description"),
        about_the_game=doc.get("about_the_game"),
        short_description=doc.get("short_description"),
        supported_languages=doc.get("supported_languages"),
        header_image=doc.get("header_image"),
        capsule_image=doc.get("capsule_image"),
        capsule_imagev5=doc.get("capsule_imagev5"),
        website=doc.get("website"),

        pc_requirements=safe_dict(doc.get("pc_requirements")),
        mac_requirements=safe_dict(doc.get("mac_requirements")),
        linux_requirements=safe_dict(doc.get("linux_requirements")),

        developers=safe_list(doc.get("developers")),
        publishers=safe_list(doc.get("publishers")),

        price_overview=safe_dict(doc.get("price_overview")),

        packages=safe_list(doc.get("packages")),
        package_groups=safe_list(doc.get("package_groups")),

        platforms=safe_dict(doc.get("platforms")),
        metacritic=safe_dict(doc.get("metacritic")),

        categories=safe_list(doc.get("categories")),
        genres=safe_list(doc.get("genres")),
        screenshots=safe_list(doc.get("screenshots")),

        recommendations=safe_dict(doc.get("recommendations")),
        release_date=safe_dict(doc.get("release_date")),
        support_info=safe_dict(doc.get("support_info")),

        background=doc.get("background"),
        background_raw=doc.get("background_raw"),

        content_descriptors=safe_dict(doc.get("content_descriptors")),
        ratings=safe_dict(doc.get("ratings")),
    )


def game_to_search_document(game: dict) -> str:
    """Build the text blob that ChromaDB will embed for semantic search."""
    parts: List[str] = [
        game.get("name", ""),
        game.get("short_description", ""),
        game.get("detailed_description", ""),
        game.get("about_the_game", ""),
    ]

    developers = game.get("developers") or []
    if developers:
        parts.append(", ".join(developers))

    publishers = game.get("publishers") or []
    if publishers:
        parts.append(", ".join(publishers))

    genres = game.get("genres") or []
    if genres:
        parts.append(", ".join(g.get("description", "") for g in genres))

    categories = game.get("categories") or []
    if categories:
        parts.append(", ".join(c.get("description", "") for c in categories))

    return " ".join(part.strip() for part in parts if part and part.strip())


def game_to_chroma_metadata(game: dict) -> Dict[str, Any]:
    return {
        "mongo_id": str(game["_id"]),
        "steam_appid": game.get("steam_appid"),
        "name": game.get("name", ""),
        "short_description": (game.get("short_description") or "")[:500],
    }


def parse_object_id(game_id: str) -> ObjectId:
    try:
        return ObjectId(game_id)
    except Exception as exc:
        raise ValueError(f"Invalid game id: {game_id}") from exc
