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

def get_asset_info_by_id(asset_id: str, facility_id: str) -> dict | None:
    """
    Lấy thông tin đàn vật nuôi theo assetID và facilityID
    """
    if not assets_collection:
        print("ERROR: assets_collection is not available.")
        return None

    try:
        query = {"assetID": asset_id, "history.details.facilityID": facility_id}
        asset_data = assets_collection.find_one(query)

        if asset_data:
            # Chuyển đổi _id thành string và tạo dict mới
            result = dict(asset_data)
            result["_id"] = str(result["_id"])
            return result

        return None

    except Exception as e:
        print(f"An error occurred while querying MongoDB: {e}")
        return None

def get_current_feeds(asset_id: str, facility_id: str) -> list | None:
    """
    Lấy thông tin thức ăn hiện tại của đàn vật nuôi
    """
    asset_data = get_asset_info_by_id(asset_id, facility_id)
    if not asset_data or not asset_data.get("history"):
        return None

    # Lấy thông tin feeds từ history item gần nhất
    latest_history = asset_data["history"][-1] if asset_data["history"] else None
    if latest_history and latest_history.get("details", {}).get("feeds"):
        return latest_history["details"]["feeds"]

    return None

def get_current_medications(asset_id: str, facility_id: str) -> list | None:
    """
    Lấy thông tin thuốc/vaccine hiện tại của đàn vật nuôi
    """
    asset_data = get_asset_info_by_id(asset_id, facility_id)
    if not asset_data or not asset_data.get("history"):
        return None

    # Lấy thông tin medications từ history item gần nhất
    latest_history = asset_data["history"][-1] if asset_data["history"] else None
    if latest_history and latest_history.get("details", {}).get("medications"):
        return latest_history["details"]["medications"]

    return None
