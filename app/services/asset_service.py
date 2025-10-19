from typing import Optional, Dict, Any, List

from fastapi import Depends
from pymongo.database import Database

from app.configurations.mongo_config import get_db
from app.repositories.asset_repository import AssetRepository


def get_asset_repo(db: Database = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


class AssetService:
    """Service cho assets, sử dụng AssetRepository."""

    def __init__(self, repo: AssetRepository):
        self._repo = repo

    def _format_asset(self, asset: dict) -> Dict[str, Any]:
        # đảm bảo asset là dict thuần (repository trả dict nhưng defensive cast để tránh Mapping immutability)
        if asset is None:
            return asset
        asset = dict(asset)
        if asset.get("_id") is not None:
            asset["_id"] = str(asset["_id"])
        return asset

    def get_asset_info_by_id(self, asset_id: str, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            asset = self._repo.find_by_asset_and_facility(asset_id, facility_id)
            if asset:
                return self._format_asset(asset)
            return None
        except Exception as e:
            print(f"AssetService.get_asset_info_by_id error: {e}")
            return None

    def _get_latest_history_field(self, asset_id: str, facility_id: str, field: str) -> Optional[List[Dict[str, Any]]]:
        asset_data = self.get_asset_info_by_id(asset_id, facility_id)
        if not asset_data or not asset_data.get("history"):
            return None

        latest_history = asset_data["history"][-1]
        return latest_history.get("details", {}).get(field)

    def get_current_feeds(self, asset_id: str, facility_id: str) -> Optional[List[Dict[str, Any]]]:
        return self._get_latest_history_field(asset_id, facility_id, "feeds")

    def get_current_medications(self, asset_id: str, facility_id: str) -> Optional[List[Dict[str, Any]]]:
        return self._get_latest_history_field(asset_id, facility_id, "medications")


def get_asset_service(repo: AssetRepository = Depends(get_asset_repo)) -> AssetService:
    return AssetService(repo)

# Lưu ý: các hàm/ phương thức chỉ đọc dữ liệu (read-only)
