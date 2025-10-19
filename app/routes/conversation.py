from fastapi import APIRouter, Depends, status
from pymongo.database import Database

from app.configurations.mongo_config import get_db
from app.models.conversation import ConversationCreate, ConversationInDB
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService

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
