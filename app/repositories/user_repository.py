from typing import Optional, Dict, Any

from pymongo.database import Database


class UserRepository:

    def __init__(self, db: Database):
        self._collection = db["users"]

    def find_by_id(self, user_id: str, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            user = self._collection.find_one({"_id": user_id, "facilityID": facility_id})
            return user
        except Exception as e:
            print(f"UserRepository.find_by_id error: {e}")
            return None

    def find_by_email(self, email: str, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            user = self._collection.find_one({"email": email, "facilityID": facility_id})
            return user
        except Exception as e:
            print(f"UserRepository.find_by_email error: {e}")
            return None

    def find_by_username(self, username: str, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            user = self._collection.find_one({"email": username, "facilityID": facility_id})
            return user
        except Exception as e:
            print(f"UserRepository.find_by_username error: {e}")
            return None
