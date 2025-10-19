from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import ConversationCreate, ConversationInDB


class ConversationService:
    def __init__(self, repo: ConversationRepository):
        self.repo = repo

    def create_conversation(self, convo: ConversationCreate) -> ConversationInDB:
        return self.repo.create(convo)