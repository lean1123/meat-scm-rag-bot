import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from typing import Optional, Dict, Any

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
else:
    db = None

def get_user_by_id(user_id: str, farm_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin user từ database theo user_id và farm_id
    """
    if not db:
        print("ERROR: database connection is not available.")
        return None

    try:
        collection = db["users"]

        user = collection.find_one({
            "_id": user_id,
            "facilityID": farm_id
        })

        if user:
            return {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "name": user.get("name"),
                "role": user.get("role"),
                "facilityID": user.get("facilityID"),
                "status": user.get("status"),
                "fabricEnrollmentID": user.get("fabricEnrollmentID"),
                "is_active": user.get("status") == "active"
            }

        return None

    except Exception as e:
        print(f"Error in get_user_by_id: {e}")
        return None

def get_user_by_username(username: str, farm_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin user từ database theo username và farm_id
    """
    if not db:
        print("ERROR: database connection is not available.")
        return None

    try:
        collection = db["users"]

        user = collection.find_one({
            "email": username,
            "facilityID": farm_id
        })

        if user:
            return {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "name": user.get("name"),
                "role": user.get("role"),
                "facilityID": user.get("facilityID"),
                "status": user.get("status"),
                "fabricEnrollmentID": user.get("fabricEnrollmentID"),
                "is_active": user.get("status") == "active"
            }

        return None

    except Exception as e:
        print(f"Error in get_user_by_username: {e}")
        return None
