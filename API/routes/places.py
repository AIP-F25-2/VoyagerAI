from fastapi import APIRouter, HTTPException
from typing import List
from models.place import Place
from database import get_places_db   # use mock DB list

router = APIRouter(
    prefix="/places",
    tags=["Places"]
)

@router.get("/", response_model=List[Place])
def get_places():
    return get_places_db()

@router.get("/{place_id}", response_model=Place)
def get_place(place_id: int):
    db = get_places_db()
    for place in db:
        if place["id"] == place_id:
            return place
    raise HTTPException(status_code=404, detail="Place not found")

@router.post("/", response_model=Place)
def add_place(place: Place):
    db = get_places_db()
    place.id = len(db) + 1
    db.append(place.dict())
    return place

@router.put("/{place_id}", response_model=Place)
def update_place(place_id: int, updated_place: Place):
    db = get_places_db()
    for i, place in enumerate(db):
        if place["id"] == place_id:
            updated_place.id = place_id
            db[i] = updated_place.dict()
            return updated_place
    raise HTTPException(status_code=404, detail="Place not found")

@router.delete("/{place_id}")
def delete_place(place_id: int):
    db = get_places_db()
    for i, place in enumerate(db):
        if place["id"] == place_id:
            db.pop(i)
            return {"message": f"Place with id {place_id} deleted"}
    raise HTTPException(status_code=404, detail="Place not found")
