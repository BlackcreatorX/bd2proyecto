from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection

from api.config import MONGO_COLLECTION, MONGO_DB, MONGO_URI


@lru_cache
def get_mongo_client() -> MongoClient:
    return MongoClient(MONGO_URI, authSource="admin")


def get_games_collection() -> Collection:
    return get_mongo_client()[MONGO_DB][MONGO_COLLECTION]
