from pymongo.database import Database
from app.models.message import MessageCreate, MessageInDB
from datetime import datetime
from bson import ObjectId
from typing import List, Any

MESSAGE_COLLECTION = "messages"


def _sanitize_doc(d: Any) -> Any:
    """Recursively convert ObjectId instances to strings in a document or value."""
    if isinstance(d, ObjectId):
        return str(d)
    if isinstance(d, dict):
        return {k: _sanitize_doc(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_sanitize_doc(x) for x in d]
    return d


class MessageRepository:
    def __init__(self, db: Database):
        self.collection = db[MESSAGE_COLLECTION]

    def create(self, convo_id: ObjectId, msg: MessageCreate, timestamp: datetime) -> MessageInDB:
        msg_doc = msg.model_dump()
        msg_doc["conversation_id"] = convo_id
        msg_doc["timestamp"] = timestamp

        result = self.collection.insert_one(msg_doc)
        created_msg = self.collection.find_one({"_id": result.inserted_id})
        if created_msg:
            created_msg = _sanitize_doc(dict(created_msg))
            return MessageInDB(**created_msg)
        raise ValueError("Failed to create message")

    def get_by_conversation_id(self, convo_id: ObjectId) -> List[MessageInDB]:
        cursor = self.collection.find(
            {"conversation_id": convo_id}
        ).sort("timestamp", 1)

        messages = list(cursor)

        result: List[MessageInDB] = []
        for msg in messages:
            msg = _sanitize_doc(dict(msg))
            result.append(MessageInDB(**msg))

        return result
