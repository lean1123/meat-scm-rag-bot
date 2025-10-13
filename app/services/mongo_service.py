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
    batches_collection = db["batches"]
else:
    db = None
    batches_collection = None

def get_batch_info_by_id(batch_id: str, farm_id: str) -> dict | None:
    if not batches_collection:
        print("ERROR: batches_collection is not available.")
        return None

    try:
        query = {"batch_id": batch_id, "facilityID": farm_id}
        batch_data = batches_collection.find_one(query)

        if batch_data:
            batch_data["_id"] = str(batch_data["_id"])

        return batch_data

    except Exception as e:
        print(f"An error occurred while querying MongoDB: {e}")
        return None