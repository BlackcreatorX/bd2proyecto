from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db.chromadb_client import get_chroma_client
from api.db.mongodb import get_mongo_client
from api.models.game import HealthResponse
from api.routers import games, vector


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_mongo_client().server_info()
    get_chroma_client().heartbeat()
    yield


app = FastAPI(
    title="Steam Games API",
    description="MongoDB for structured data, ChromaDB for semantic search.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(vector.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    mongo_status = "ok"
    chroma_status = "ok"

    try:
        get_mongo_client().admin.command("ping")
    except Exception as exc:
        mongo_status = f"error: {exc}"

    try:
        get_chroma_client().heartbeat()
    except Exception as exc:
        chroma_status = f"error: {exc}"

    return HealthResponse(mongodb=mongo_status, chromadb=chroma_status)
