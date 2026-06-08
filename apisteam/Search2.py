#%%
from operator import mod
import re
import urllib.request
import urllib.parse
import json
import time
from attrs import field
from bson import ObjectId
from dotenv import load_dotenv
import os
from pymongo import MongoClient, collection, cursor
#############################################################################
#############################################################################
#############################################################################
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId

#%%
load_dotenv()
#%%
juegos = json.load(open("100_juegos_steam.json", "r", encoding="utf-8"))




#%%
#==========================
#ConectMongodb
#==========================
mongo_uri = "mongodb://root:Admin123@localhost:27017"
client = MongoClient(mongo_uri, authSource="admin")
#%%
client.server_info() 

#%%

db = client["steam_db"]
GamesCollection = db["juegos"]



#%%
GamesCollection.insert_many(juegos)

#%%
#==================================================
#Definición de la función para buscar una palabra en los juegos
#==================================================
def buscar_palabra(juegos, patron):

    try:
        coincidencias = []

        
        regex = re.compile(patron, re.IGNORECASE)

        
        for juego in juegos:

            
            texto = str(juego)

            
            if regex.search(texto):
                coincidencias.append(juego)

        
        if len(coincidencias) > 0:

            print(f"Se encontraron {len(coincidencias)} coincidencias:\n")

            for juego in coincidencias:

                print("Nombre:", juego.get("name"))
                print("Steam App ID:", juego.get("steam_appid"))

                
                if juego.get("developers"):
                    print("Developer:", ", ".join(juego.get("developers")))

                
                if juego.get("genres"):
                    generos = [g["description"] for g in juego["genres"]]
                    print("Géneros:", ", ".join(generos))

                print("-" * 50)

        else:
            print("No se encontraron coincidencias")

    
    except re.error as e:
        print("Expresión regular inválida:", e)

    
    except Exception as e:
        print("Ocurrió un error:", e)


#%%
#==================================================
#Función para buscar una palabra en los juegos
#==================================================

palabra=input("Ingrese la palabra a buscar: ")
buscar_palabra(juegos, palabra)
#%%
#+==================================================
#buscar_juegos_regex(GamesCollection, palabra)
#==================================================
def buscar_juegos_regex(collection, patron):

    try:

        # buscar en todos los campos usando $or
        games = collection.find({
            '$or': [

                {'name': {'$regex': patron, '$options': 'i'}},
                {'detailed_description': {'$regex': patron, '$options': 'i'}},
                {'about_the_game': {'$regex': patron, '$options': 'i'}},
                {'short_description': {'$regex': patron, '$options': 'i'}},
                {'supported_languages': {'$regex': patron, '$options': 'i'}},
                {'developers': {'$regex': patron, '$options': 'i'}},
                {'publishers': {'$regex': patron, '$options': 'i'}},
                {'genres.description': {'$regex': patron, '$options': 'i'}},
                {'categories.description': {'$regex': patron, '$options': 'i'}}

            ]
        })

        encontrados = False

        for game in games:

            encontrados = True

            print("Nombre:", game.get("name"))
            print("Steam App ID:", game.get("steam_appid"))

            if game.get("developers"):
                print("Developer:", ", ".join(game.get("developers")))

            print("-" * 50)

        if not encontrados:
            print("No se encontraron coincidencias")

    except Exception as e:
        print("Error:", e)
#%%
palabra=input("Buscar: ")

buscar_juegos_regex(juegos, palabra)

#%%
#clase de entrada y salida para la API




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
#%%

#####Endpoints
@router.get("/", response_model=List[GameOutput])
def get_games():

    games = collection.find()

    return [
        doc_to_game_output(game)
        for game in games
    ]
@router.get("/{game_id}", response_model=GameOutput)
def get_game(game_id: str):

    game = collection.find_one({
        "_id": ObjectId(game_id)
    })

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Game not found"
        )

    return doc_to_game_output(game)
@router.get("/search/", response_model=List[GameOutput])
def search_games(q: str):

    games = collection.find({
        "name": {
            "$regex": q,
            "$options": "i"
        }
    })

    return [
        doc_to_game_output(game)
        for game in games
    ]

@router.post("/", response_model=GameOutput)
def create_game(game: GameInput):

    game_dict = game.model_dump()

    result = collection.insert_one(game_dict)

    created_game = collection.find_one({
        "_id": result.inserted_id
    })

    return GameOutput(
        id=str(created_game["_id"]),
        updated_at="",
        **created_game
    )
@router.put("/{game_id}", response_model=GameOutput)
def update_game(game_id: str, game: GameInput):

    result = collection.update_one(
        {"_id": ObjectId(game_id)},
        {
            "$set": game.model_dump()
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Game not found"
        )

    updated_game = collection.find_one({
        "_id": ObjectId(game_id)
    })

    return GameOutput(
        id=str(updated_game["_id"]),
        updated_at="",
        **updated_game
    )


# DELETE
@router.delete("/{game_id}")
def delete_game(game_id: str):
    
    result = collection.delete_one({
        "_id": ObjectId(game_id)
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Game not found"
        )

    return {
        "message": "Game deleted"
    }


#%%
class GameOutput(GameInput):
   id: str
   updated_at: str
    
def doc_to_game_output(doc: dict) -> dict:
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

        pc_requirements=doc.get("pc_requirements"),
        mac_requirements=doc.get("mac_requirements"),
        linux_requirements=doc.get("linux_requirements"),

        developers=doc.get("developers"),
        publishers=doc.get("publishers"),

        price_overview=doc.get("price_overview"),

        packages=doc.get("packages"),

        package_groups=doc.get("package_groups"),

        platforms=doc.get("platforms"),

        metacritic=doc.get("metacritic"),

        categories=doc.get("categories"),
        genres=doc.get("genres"),

        screenshots=doc.get("screenshots"),

        recommendations=doc.get("recommendations"),

        release_date=doc.get("release_date"),

        support_info=doc.get("support_info"),

        background=doc.get("background"),
        background_raw=doc.get("background_raw"),

        content_descriptors=doc.get("content_descriptors"),

        ratings=doc.get("ratings")
    )



#%%



# =========================
# 1. OBTENER LISTA DE JUEGOS
# =========================

url = (
    "https://api.steampowered.com/IStoreService/GetAppList/v1/"
    f"?key={os.getenv('STEAMWORKS_API_KEY')}&include_games=true&max_results=100"
)

response = urllib.request.urlopen(url)

data = json.loads(response.read().decode("utf-8"))

apps = data["response"]["apps"]

print(f"Se encontraron {len(apps)} juegos")

# =========================
# 2. OBTENER DETALLES
# =========================

detalles_juegos = []

for i, juego in enumerate(apps):

    appid = juego["appid"]

    print(f"[{i+1}/100] Obteniendo detalles de {juego['name']}")

    try:

        details_url = (
            f"https://store.steampowered.com/api/appdetails?appids={appid}"
        )

        details_response = urllib.request.urlopen(details_url)

        details_data = json.loads(
            details_response.read().decode("utf-8")
        )

        # Extraer solo la data útil
        game_data = details_data[str(appid)]["data"]

        detalles_juegos.append(game_data)

        # Pequeña pausa para evitar rate limit
        time.sleep(0.2)

    except Exception as e:
        print(f"Error con {appid}: {e}")
#%%


# =========================
# 3. GUARDAR JSON
# =========================

with open("100_juegos_steam.json", "w", encoding="utf-8") as file:
    json.dump(
        detalles_juegos,
        file,
        indent=4,
        ensure_ascii=False
    )

print("Archivo creado: 100_juegos_steam.json")
#%%
