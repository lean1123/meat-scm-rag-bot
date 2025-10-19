from typing import Optional, Dict, Any

from fastapi import Depends
from pymongo.database import Database

from app.configurations.mongo_config import get_db
from app.repositories.user_repository import UserRepository


def get_user_repo(db: Database = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


class UserService:
    """Service cho user: chỉ lấy dữ liệu (get by id/email/username)."""

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def _format_user(self, user: dict) -> Dict[str, Any]:
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

    def _find_user(self, filter: dict) -> Optional[Dict[str, Any]]:
        try:
            user = self._repo.find_by_email(filter.get("email"), filter.get("facilityID")) if filter.get(
                "email") else None
            # if searching by _id, repo method will handle it
            if not user and filter.get("_id"):
                user = self._repo.find_by_id(filter.get("_id"), filter.get("facilityID"))

            if user:
                return self._format_user(user)
            return None
        except Exception as e:
            print(f"UserService._find_user error: {e}")
            return None

    def get_user_by_id(self, user_id: str, farm_id: str) -> Optional[Dict[str, Any]]:
        return self._find_user({"_id": user_id, "facilityID": farm_id})

    def get_user_by_username(self, username: str, farm_id: str) -> Optional[Dict[str, Any]]:
        return self._find_user({"email": username, "facilityID": farm_id})

    def get_user_by_email(self, email: str, farm_id: str) -> Optional[Dict[str, Any]]:
        return self._find_user({"email": email, "facilityID": farm_id})


def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(repo)
