from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.message import MessageCreate, MessageInDB
from app.models.conversation import ConversationCreate
from app.services.memory_weaviate_service import WeaviateChatMemoryService
from app.configurations.weaviate_config import get_weaviate_client
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, UTC
from fastapi import HTTPException


class MessageService:
    def __init__(self,
                 message_repo: MessageRepository,
                 convo_repo: ConversationRepository,
                 memory_service: Optional[WeaviateChatMemoryService] = None
                 ):
        self.message_repo = message_repo
        self.convo_repo = convo_repo
        self.memory_service = memory_service

    def _ensure_memory_service(self):
        """Lazily initialize memory service if a global weaviate client exists."""
        if self.memory_service is not None:
            return
        client = get_weaviate_client()
        if client is None:
            return
        try:
            self.memory_service = WeaviateChatMemoryService()
        except Exception as e:
            print(f"Warning: failed to initialize memory service lazily: {e}")
            self.memory_service = None

    def get_messages_for_conversation(self, convo_id: ObjectId) -> List[MessageInDB]:
        return self.message_repo.get_by_conversation_id(convo_id)

    def create_message(self, convo_id: ObjectId, msg: MessageCreate) -> MessageInDB:
        conversation = self.convo_repo.get_by_id(convo_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        now = datetime.now(UTC)
        new_message = self.message_repo.create(convo_id, msg, now)

        self.convo_repo.update_timestamp(convo_id, now)

        return new_message

    def save_new_message(self,
                        msg: MessageCreate,
                        email: str,
                        facility_id: str,
                        conversation_id: Optional[str] = None,
                        conversation_title: str = "New Chat") -> MessageInDB:

        if conversation_id:
            try:
                convo_obj_id = ObjectId(conversation_id)
                conversation = self.convo_repo.get_by_id(convo_obj_id)
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        else:
            convo_create = ConversationCreate(
                email=email,
                facilityID=facility_id,
                title=conversation_title
            )
            conversation = self.convo_repo.create(convo_create)
            convo_obj_id = conversation.id

        now = datetime.now(UTC)
        new_message = self.message_repo.create(convo_obj_id, msg, now)

        self.convo_repo.update_timestamp(convo_obj_id, now)

        memory_json = {
            "content": msg.content,
            "memoryType": "FACT",
            "importanceScore": 0.5,
            "sourceMessageID": str(new_message.id),
            "createdAt": now.isoformat().replace("+00:00", "Z")
        }

        # Try to lazily initialize memory service, then save if available
        self._ensure_memory_service()
        if self.memory_service is not None:
            try:
                self.memory_service.save_memory(
                    email=email,
                    conversation_id=str(convo_obj_id),
                    memory_json=memory_json
                )
            except Exception as e:
                print(f"Lỗi khi lưu memory vào Weaviate: {e}")

        return new_message
