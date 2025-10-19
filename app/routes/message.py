# /app/controllers/message.py

from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.configurations.mongo_config import get_db
from app.models.message import MessageCreate, MessageInDB
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.message_service import MessageService

router = APIRouter()


# --- Dependency Injection (DI) ---
def get_convo_repo(db_client: Database = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db_client)


def get_message_repo(db_client: Database = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db_client)


def get_message_service(
        msg_repo: MessageRepository = Depends(get_message_repo),
        convo_repo: ConversationRepository = Depends(get_convo_repo)
) -> MessageService:
    return MessageService(message_repo=msg_repo, convo_repo=convo_repo)


def validate_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="ID không hợp lệ.")


@router.post(
    "/conversations/{conversation_id}/messages/",
    response_model=MessageInDB,
    status_code=status.HTTP_201_CREATED
)
def create_message_endpoint(
        conversation_id: str,
        message: MessageCreate,
        service: MessageService = Depends(get_message_service)
):
    oid = validate_object_id(conversation_id)
    return service.create_message(oid, message)


@router.get(
    "/conversations/{conversation_id}/messages/",
    response_model=List[MessageInDB]
)
def get_messages_endpoint(
        conversation_id: str,
        service: MessageService = Depends(get_message_service)
):
    oid = validate_object_id(conversation_id)
    return service.get_messages_for_conversation(oid)
