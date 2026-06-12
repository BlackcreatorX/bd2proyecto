import json
from pymongo import MongoClient

client = MongoClient(
    "mongodb://root:Admin123@localhost:27017",
    authSource="admin"
)

db = client["steam_db"]
col = db["juegos"]

count = col.count_documents({})

if count == 0:
    with open("apisteam/100_juegos_steam.json", encoding="utf-8") as f:
        games = json.load(f)

    col.insert_many(games)
    print(f"Inserted {len(games)} games")
else:
    print(f"Collection already has {count} games")