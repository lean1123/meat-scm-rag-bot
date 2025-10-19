import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("MongoDB connection successful.")
except (ConnectionFailure, AttributeError) as e:
    print(f"Could not connect to MongoDB: {e}")
    client = None

if client:
    db = client["farm_db"]
    assets_collection = db["assets"]
else:
    db = None
    assets_collection = None
