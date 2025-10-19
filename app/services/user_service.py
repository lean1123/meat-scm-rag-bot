from typing import Optional, Dict, Any
from app.configurations.mongo_config import db

collection_name = "users"

def _format_user(user: dict) -> Dict[str, Any]:
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
        "facilityID": user.get("facilityID"),
        "status": user.get("status"),
        "fabricEnrollmentID": user.get("fabricEnrollmentID"),
        "is_active": user.get("status") == "active",
    }

def _find_user(filter: dict) -> Optional[Dict[str, Any]]:
    if not db:
        print("ERROR: Database connection is not available.")
        return None

    try:
        collection = db[collection_name]
        user = collection.find_one(filter)

        if user:
            return _format_user(user)

        return None

    except Exception as e:
        print(f"Error in _find_user: {e}")
        return None

def get_user_by_id(user_id: str, farm_id: str) -> Optional[Dict[str, Any]]:
    return _find_user({"_id": user_id, "facilityID": farm_id})


def get_user_by_username(username: str, farm_id: str) -> Optional[Dict[str, Any]]:
    return _find_user({"email": username, "facilityID": farm_id})


def get_user_by_email(email: str, farm_id: str) -> Optional[Dict[str, Any]]:
    return _find_user({"email": email, "facilityID": farm_id})
