from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import ConversationCreate, ConversationInDB
from bson import ObjectId
from datetime import datetime, timezone


class ConversationService:
    def __init__(self, repo: ConversationRepository):
        self.repo = repo

    def create_conversation(self, convo: ConversationCreate) -> ConversationInDB:
        return self.repo.create(convo)

    def list_conversations_for_user(self, email: str, facilityID: str | None = None, limit: int = 50, offset: int = 0) -> list[ConversationInDB]:
        """Return list of conversations for a user (optionally filtered by facilityID) with pagination."""
        return self.repo.list_by_user(email=email, facilityID=facilityID, limit=limit, offset=offset)

    def update_title(self, convo_id: str, new_title: str) -> bool:
        try:
            obj_id = ObjectId(convo_id)
        except Exception:
            return False

        convo = self.repo.get_by_id(obj_id)
        if convo is None:
            return False

        self.repo.collection.update_one(
            {"_id": obj_id},
            {"$set": {"title": new_title, "updated_at": datetime.now(timezone.utc)}}
        )
        return True

    def delete_conversation(self, convo_id: ObjectId) -> bool:
        result = self.repo.collection.delete_one({"_id": convo_id})
        return result.deleted_count > 0