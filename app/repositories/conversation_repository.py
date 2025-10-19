from pymongo.database import Database
from app.models.conversation import ConversationCreate, ConversationInDB
from datetime import datetime
from bson import ObjectId

CONVERSATION_COLLECTION = "conversations"


class ConversationRepository:
    def __init__(self, db: Database):
        self.collection = db[CONVERSATION_COLLECTION]

    def create(self, convo: ConversationCreate) -> ConversationInDB:
        now = datetime.utcnow()
        convo_doc = convo.model_dump()
        convo_doc["created_at"] = now
        convo_doc["updated_at"] = now

        result = self.collection.insert_one(convo_doc)
        created_convo = self.collection.find_one({"_id": result.inserted_id})
        return ConversationInDB(**created_convo)

    def get_by_id(self, convo_id: ObjectId) -> ConversationInDB | None:
        convo = self.collection.find_one({"_id": convo_id})
        if convo:
            return ConversationInDB(**convo)
        return None

    def update_timestamp(self, convo_id: ObjectId, timestamp: datetime):
        self.collection.update_one(
            {"_id": convo_id},
            {"$set": {"updated_at": timestamp}}
        )