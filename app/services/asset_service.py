from typing import Optional, Dict, Any, List
from app.configurations.mongo_config import db

collection_name = "assets"


def _get_collection():
    if not db:
        print("ERROR: Database connection is not available.")
        return None
    return db[collection_name]


def _find_asset(filter: dict) -> Optional[Dict[str, Any]]:
    collection = _get_collection()
    if not collection:
        return None

    try:
        asset = collection.find_one(filter)
        if asset:
            asset["_id"] = str(asset["_id"])
            return asset
        return None
    except Exception as e:
        print(f"Error querying MongoDB: {e}")
        return None


def get_asset_info_by_id(asset_id: str, facility_id: str) -> Optional[Dict[str, Any]]:
    return _find_asset({"assetID": asset_id, "history.details.facilityID": facility_id})


def _get_latest_history_field(asset_id: str, facility_id: str, field: str) -> Optional[List[Dict[str, Any]]]:
    asset_data = get_asset_info_by_id(asset_id, facility_id)
    if not asset_data or not asset_data.get("history"):
        return None

    latest_history = asset_data["history"][-1]
    return latest_history.get("details", {}).get(field)


def get_current_feeds(asset_id: str, facility_id: str) -> Optional[List[Dict[str, Any]]]:
    return _get_latest_history_field(asset_id, facility_id, "feeds")


def get_current_medications(asset_id: str, facility_id: str) -> Optional[List[Dict[str, Any]]]:
    return _get_latest_history_field(asset_id, facility_id, "medications")
