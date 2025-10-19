import atexit
import os

from dotenv import load_dotenv
from fastapi import HTTPException, status
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print("MongoDB connection successful.")
    except (ConnectionFailure, AttributeError) as e:
        print(f"Could not connect to MongoDB: {e}")
        client = None
else:
    print("MONGO_URI not set")

if client is not None:
    db: Database = client["farm_db"]
else:
    db = None

# Đảm bảo đóng kết nối khi server dừng (chỉ đăng ký khi client tồn tại)
if client is not None:
    atexit.register(lambda: client.close())


def get_db() -> Database:
    """FastAPI dependency: trả về đối tượng Database hoặc raise HTTPException nếu không có kết nối.

    Tránh trả trực tiếp `db` vào Depends(...) vì đối tượng pymongo Database không cho phép
    kiểm tra truthiness và sẽ ném NotImplementedError khi FastAPI inspect dependency.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB not available")
    return db
