from pymongo.database import Database
from app.models.message import MessageCreate, MessageInDB
from datetime import datetime
from bson import ObjectId
from typing import List

MESSAGE_COLLECTION = "messages"


class MessageRepository:
    def __init__(self, db: Database):
        self.collection = db[MESSAGE_COLLECTION]

    def create(self, convo_id: ObjectId, msg: MessageCreate, timestamp: datetime) -> MessageInDB:
        msg_doc = msg.model_dump()
        msg_doc["conversation_id"] = convo_id
        msg_doc["timestamp"] = timestamp

        result = self.collection.insert_one(msg_doc)
        created_msg = self.collection.find_one({"_id": result.inserted_id})
        return MessageInDB(**created_msg)

    def get_by_conversation_id(self, convo_id: ObjectId) -> List[MessageInDB]:
        cursor = self.collection.find(
            {"conversation_id": convo_id}
        ).sort("timestamp", 1)

        messages = list(cursor)

        return [MessageInDB(**msg) for msg in messages]