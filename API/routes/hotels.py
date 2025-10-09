from fastapi import APIRouter, HTTPException
from typing import List
from models.hotel import Hotel
from database import get_hotels_db   # use mock DB list

router = APIRouter(
    prefix="/hotels",
    tags=["Hotels"]
)

@router.get("/", response_model=List[Hotel])
def get_hotels():
    return get_hotels_db()

@router.get("/{hotel_id}", response_model=Hotel)
def get_hotel(hotel_id: int):
    db = get_hotels_db()
    for hotel in db:
        if hotel["id"] == hotel_id:
            return hotel
    raise HTTPException(status_code=404, detail="Hotel not found")

@router.post("/", response_model=Hotel)
def add_hotel(hotel: Hotel):
    db = get_hotels_db()
    hotel.id = len(db) + 1
    db.append(hotel.dict())
    return hotel

@router.put("/{hotel_id}", response_model=Hotel)
def update_hotel(hotel_id: int, updated_hotel: Hotel):
    db = get_hotels_db()
    for i, hotel in enumerate(db):
        if hotel["id"] == hotel_id:
            updated_hotel.id = hotel_id
            db[i] = updated_hotel.dict()
            return updated_hotel
    raise HTTPException(status_code=404, detail="Hotel not found")

@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int):
    db = get_hotels_db()
    for i, hotel in enumerate(db):
        if hotel["id"] == hotel_id:
            db.pop(i)
            return {"message": f"Hotel with id {hotel_id} deleted"}
    raise HTTPException(status_code=404, detail="Hotel not found")
