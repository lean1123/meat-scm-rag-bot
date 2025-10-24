from pymongo.database import Database
from app.models.conversation import ConversationCreate, ConversationInDB
from datetime import datetime, timezone
from bson import ObjectId

CONVERSATION_COLLECTION = "conversations"


class ConversationRepository:
    def __init__(self, db: Database):
        self.collection = db[CONVERSATION_COLLECTION]

    def create(self, convo: ConversationCreate) -> ConversationInDB:
        now = datetime.now(timezone.utc)
        convo_doc = convo.model_dump()
        convo_doc["created_at"] = now
        convo_doc["updated_at"] = now

        result = self.collection.insert_one(convo_doc)
        created_convo = self.collection.find_one({"_id": result.inserted_id})
        # Ensure we have a mutable dict and _id is a string for Pydantic validation
        if created_convo:
            created_convo = dict(created_convo)
            if "_id" in created_convo:
                created_convo["_id"] = str(created_convo["_id"])
            return ConversationInDB(**created_convo)
        # Shouldn't normally happen, but raise a ValueError to signal failure
        raise ValueError("Failed to create conversation")

    def get_by_id(self, convo_id: ObjectId) -> ConversationInDB | None:
        convo = self.collection.find_one({"_id": convo_id})
        if convo:
            # Convert to dict so we can mutate and convert ObjectId to string
            convo = dict(convo)
            if "_id" in convo:
                convo["_id"] = str(convo["_id"])
            return ConversationInDB(**convo)
        return None

    def update_timestamp(self, convo_id: ObjectId, timestamp: datetime):
        self.collection.update_one(
            {"_id": convo_id},
            {"$set": {"updated_at": timestamp}}
        )