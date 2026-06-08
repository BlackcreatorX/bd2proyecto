from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class GameInput(BaseModel):
    type: str = Field(..., description="Tipo de contenido")
    name: str = Field(..., min_length=1, max_length=200)
    steam_appid: int = Field(..., ge=0)
    required_age: int = Field(..., ge=0)
    is_free: bool
    detailed_description: str
    about_the_game: str
    short_description: str
    supported_languages: str
    header_image: HttpUrl
    capsule_image: HttpUrl
    capsule_imagev5: HttpUrl
    website: Optional[HttpUrl] = None
    pc_requirements: Optional[Dict[str, Any]] = None
    mac_requirements: Optional[Dict[str, Any]] = None
    linux_requirements: Optional[Dict[str, Any]] = None
    developers: List[str]
    publishers: List[str]
    price_overview: Optional[Dict[str, Any]] = None
    packages: List[int]
    package_groups: List[Dict[str, Any]]
    platforms: Dict[str, bool]
    metacritic: Optional[Dict[str, Any]] = None
    categories: List[Dict[str, Any]]
    genres: List[Dict[str, Any]]
    screenshots: List[Dict[str, Any]]
    recommendations: Dict[str, int]
    release_date: Dict[str, Any]
    support_info: Dict[str, Optional[str]]
    background: HttpUrl
    background_raw: HttpUrl
    content_descriptors: Dict[str, Any]
    ratings: Dict[str, Dict[str, Any]]


class GameOutput(GameInput):
    id: str
    updated_at: str = ""


class SemanticSearchResult(BaseModel):
    mongo_id: str
    steam_appid: Optional[int] = None
    name: str
    short_description: str = ""
    score: float
    game: Optional[GameOutput] = None


class SyncResponse(BaseModel):
    synced: int
    skipped: int
    total_in_mongo: int
    total_in_chroma: int


class HealthResponse(BaseModel):
    mongodb: str
    chromadb: str
