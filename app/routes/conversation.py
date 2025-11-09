from bson import ObjectId
from fastapi import APIRouter, Depends, status, Query, HTTPException
from typing import List
from pymongo.database import Database

from app.configurations.mongo_config import get_db
from app.models.conversation import ConversationCreate, ConversationInDB
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService
from app.services.auth_service import get_current_user, User

router = APIRouter()


def get_convo_repo(db_client: Database = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db_client)


def get_convo_service(repo: ConversationRepository = Depends(get_convo_repo)) -> ConversationService:
    return ConversationService(repo)


@router.post(
    "/conversations/",
    response_model=ConversationInDB,
    status_code=status.HTTP_201_CREATED
)
def create_conversation_endpoint(
        conversation: ConversationCreate,
        service: ConversationService = Depends(get_convo_service)
):
    return service.create_conversation(conversation)


@router.get(
    "/conversations/",
    response_model=List[ConversationInDB],
    status_code=status.HTTP_200_OK,
)
def list_conversations_endpoint(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="Max number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    service: ConversationService = Depends(get_convo_service)
):
    """Lấy danh sách conversation của user đang xác thực (email và facilityID lấy từ token)."""
    # Lấy thông tin từ token
    email = current_user.email
    facilityID = current_user.facilityID

    return service.list_conversations_for_user(email=email, facilityID=facilityID, limit=limit, offset=offset)

@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation_endpoint(
        conversation_id: str,
        service: ConversationService = Depends(get_convo_service)
):
    try:
        obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    success = service.delete_conversation(obj_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")