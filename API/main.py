from fastapi import FastAPI
from routes import hotels,places

app = FastAPI()

# Register routers
app.include_router(hotels.router)
app.include_router(places.router)


@app.get("/")
def root():
    return {"message": "VoyagerAI API is running!"}
