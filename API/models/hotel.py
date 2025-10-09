from pydantic import BaseModel

class Hotel(BaseModel):
    id: int | None = None
    name: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    rating: float
    price_range: str
    source: str
