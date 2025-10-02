import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/voyagerai")
db_name = os.getenv("MONGO_DB", "voyagerai")

client = MongoClient(mongo_uri)
db = client[db_name]
1

print(f"Connected to MongoDB: {db_name}")
