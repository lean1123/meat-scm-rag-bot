# /app/services/message.py

from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.message import MessageCreate, MessageInDB
from typing import List
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException, status


class MessageService:
    def __init__(self,
                 message_repo: MessageRepository,
                 convo_repo: ConversationRepository
                 ):
        self.message_repo = message_repo
        self.convo_repo = convo_repo

    def get_messages_for_conversation(self, convo_id: ObjectId) -> List[MessageInDB]:
        return self.message_repo.get_by_conversation_id(convo_id)

    def create_message(self, convo_id: ObjectId, msg: MessageCreate) -> MessageInDB:
        conversation = self.convo_repo.get_by_id(convo_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        now = datetime.utcnow()
        new_message = self.message_repo.create(convo_id, msg, now)

        self.convo_repo.update_timestamp(convo_id, now)

        return new_message