from pydantic import BaseModel

class Place(BaseModel):
    id: int | None = None
    name: str
    location: str
    description: str
