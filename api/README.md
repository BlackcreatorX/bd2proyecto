# Steam Games API — MongoDB + ChromaDB

This API connects your existing **MongoDB** Steam games database with **ChromaDB** for semantic (vector) search. MongoDB remains the source of truth; ChromaDB indexes searchable text and returns the most relevant games by meaning, not just exact keywords.

## Architecture

```mermaid
flowchart LR
    Client[Client / Browser]
    API[FastAPI api/]
    Mongo[(MongoDB\nsteam_db.juegos)]
    Chroma[(ChromaDB\nsteam_games)]

    Client --> API
    API -->|CRUD, regex search| Mongo
    API -->|sync + vector search| Chroma
    Chroma -->|mongo_id in metadata| Mongo
```

| Store | Role |
|-------|------|
| **MongoDB** | Full game documents (descriptions, prices, genres, etc.) |
| **ChromaDB** | Embeddings of name + descriptions + genres; lightweight metadata (`mongo_id`, `steam_appid`, `name`) |
| **Link** | Each ChromaDB vector uses the MongoDB `_id` as its ID, so search hits map back to the original document |

### What gets embedded?

For each game, ChromaDB indexes a text blob built from:

- `name`, `short_description`, `detailed_description`, `about_the_game`
- `developers`, `publishers`
- genre and category descriptions

ChromaDB generates embeddings automatically (default model: `all-MiniLM-L6-v2`).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for MongoDB + ChromaDB)
- [uv](https://docs.astral.sh/uv/) or Python 3.14+ with pip

## Quick start

### 1. Start databases

From the repo root:

```bash
docker compose up -d
```

This starts:

| Service | Port | Credentials |
|---------|------|-------------|
| MongoDB | `27017` | user `root`, password `Admin123` |
| ChromaDB | `8000` | no auth (local dev) |

Data persists in `./data` (MongoDB) and `./chroma_data` (ChromaDB).

### 2. Load games into MongoDB (if empty)

If you have not loaded data yet, use the notebook/script in `apisteam/Search2.py` or import the JSON directly:

```bash
uv run python -c "
import json
from pymongo import MongoClient

client = MongoClient('mongodb://root:Admin123@localhost:27017', authSource='admin')
db = client['steam_db']
col = db['juegos']
if col.count_documents({}) == 0:
    games = json.load(open('apisteam/100_juegos_steam.json', encoding='utf-8'))
    col.insert_many(games)
    print(f'Inserted {len(games)} games')
else:
    print(f'Collection already has {col.count_documents({})} games')
"
```

### 3. Install dependencies

```bash
uv sync
```

Copy environment variables (optional — defaults match docker-compose):

```bash
cp api/.env.example api/.env
```

### 4. Run the API

```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

Open interactive docs: [http://localhost:8080/docs](http://localhost:8080/docs)

### 5. Sync MongoDB → ChromaDB

Before semantic search works, index your MongoDB data into ChromaDB:

```bash
curl -X POST "http://localhost:8080/vector/sync"
```

To wipe and rebuild the vector index:

```bash
curl -X POST "http://localhost:8080/vector/sync?reset=true"
```

Response example:

```json
{
  "synced": 100,
  "skipped": 0,
  "total_in_mongo": 100,
  "total_in_chroma": 100
}
```

### 6. Semantic search

```bash
curl "http://localhost:8080/vector/search?q=team+based+shooter&limit=5"
```

Unlike regex search on `name`, this finds games by **meaning** — e.g. `"survival crafting open world"` can match Valheim-like titles even if those exact words are not in the title.

## API endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Ping MongoDB and ChromaDB |

### Games (MongoDB)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/games/` | List all games |
| `GET` | `/games/search?q=...` | Regex search on game name |
| `GET` | `/games/{id}` | Get one game by MongoDB `_id` |
| `POST` | `/games/` | Create game (also indexes in ChromaDB) |
| `PUT` | `/games/{id}` | Update game (re-indexes in ChromaDB) |
| `DELETE` | `/games/{id}` | Delete game (removes from ChromaDB too) |

### Vector search (ChromaDB)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/vector/sync` | Bulk sync MongoDB → ChromaDB |
| `GET` | `/vector/search?q=...` | Semantic search |

Query params for `/vector/search`:

- `q` — natural language query (required)
- `limit` — max results, 1–50 (default `10`)
- `hydrate` — attach full MongoDB document to each hit (default `true`)

## Project layout

```
api/
├── main.py              # FastAPI app entry point
├── config.py            # Environment variables
├── db/
│   ├── mongodb.py       # PyMongo client
│   └── chromadb_client.py
├── models/
│   └── game.py          # Pydantic schemas
├── routers/
│   ├── games.py         # CRUD + name search
│   └── vector.py        # Sync + semantic search
└── services/
    ├── sync.py          # MongoDB → ChromaDB indexing
    ├── search.py        # Vector query + MongoDB hydration
    └── game_utils.py    # Document helpers
```

## How the connection works (step by step)

1. **Write path** — When you create or update a game via `/games`, the document is saved in MongoDB and immediately upserted into ChromaDB (`services/sync.py` → `index_game`).

2. **Bulk sync** — `POST /vector/sync` reads every document from `steam_db.juegos`, builds a searchable text string per game, and upserts vectors into the `steam_games` ChromaDB collection. The MongoDB `_id` is used as the ChromaDB document ID.

3. **Search path** — `GET /vector/search` sends your query to ChromaDB, which returns the closest vectors by cosine similarity. Each result includes `mongo_id`; when `hydrate=true`, the API loads the full game from MongoDB and returns it in the `game` field.

4. **Delete path** — Deleting a game removes it from both stores.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://root:Admin123@localhost:27017` | MongoDB connection string |
| `MONGO_DB` | `steam_db` | Database name |
| `MONGO_COLLECTION` | `juegos` | Collection name |
| `CHROMA_HOST` | `localhost` | ChromaDB server host |
| `CHROMA_PORT` | `8000` | ChromaDB server port |
| `CHROMA_COLLECTION` | `steam_games` | ChromaDB collection name |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8080` | API bind port |

## Troubleshooting

**ChromaDB connection refused**

- Ensure `docker compose up -d` is running and port `8000` is free.
- Check: `curl http://localhost:8000/api/v2/heartbeat`

**MongoDB auth failed**

- Confirm credentials match `docker-compose.yml` (`root` / `Admin123`).
- Use `authSource=admin` (already set in `api/db/mongodb.py`).

**Semantic search returns nothing**

- Run `POST /vector/sync` first to populate ChromaDB.
- Verify MongoDB has data: `GET /games/`.

**Port conflict between ChromaDB and API**

- ChromaDB uses port `8000`; the FastAPI app uses `8080` by default so they do not clash.

## MongoDB vs ChromaDB — when to use which

| Use case | Store |
|----------|-------|
| Exact CRUD, filters, regex on fields | MongoDB |
| “Find games like…” / natural language | ChromaDB |
| Full structured response | MongoDB (via `hydrate=true`) |

You typically query ChromaDB for relevance, then read the full document from MongoDB — which is exactly what `/vector/search?hydrate=true` does.
