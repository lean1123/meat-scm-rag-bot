from typing import Optional, Dict, Any

from pymongo.database import Database


class AssetRepository:
    """Repository cho collection assets."""

    def __init__(self, db: Database):
        self._collection = db["assets"]

    def find_by_asset_and_facility(self, asset_id: str, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            asset = self._collection.find_one({"assetID": asset_id, "history.details.facilityID": facility_id})
            if asset is None:
                return None
            # convert to plain dict so callers can modify/format fields safely
            return dict(asset)
        except Exception as e:
            print(f"AssetRepository.find_by_asset_and_facility error: {e}")
            return None
