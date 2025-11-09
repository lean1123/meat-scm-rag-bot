from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.asset_service import get_asset_service, AssetService
from app.services.auth_service import User
from app.services.auth_service import get_current_user
from app.services.farm_weaviate_service import search_knowledge_base
from app.services.gemini_service import detect_intent, generate_answer, generate_short_conversation_title, \
    handle_get_feed_info, handle_get_medication_info, handle_suggest_feed, handle_suggest_medication, \
    handle_general_chat
from app.services.get_asset_http_service import get_asset_trace
from app.services.message_service import MessageService
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.memory_weaviate_service import WeaviateChatMemoryService
from app.configurations.weaviate_config import get_weaviate_client
from app.configurations.mongo_config import get_db
from app.models.message import MessageCreate
from typing import Optional


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    conversation_title: Optional[str] = "New Chat"


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    conversation_title: str
    user_message_id: str
    bot_message_id: str


router = APIRouter()


def get_message_service():
    db = get_db()
    message_repo = MessageRepository(db)
    convo_repo = ConversationRepository(db)

    # Only create memory service if weaviate client is initialized
    memory_client = get_weaviate_client()
    memory_service = None
    if memory_client is not None:
        try:
            memory_service = WeaviateChatMemoryService()
        except Exception as e:
            # If memory service fails to initialize, log and continue without memory
            print(f"Warning: failed to init memory service: {e}")
            memory_service = None

    return MessageService(message_repo, convo_repo, memory_service)


# Support both /chat and /chat/{conversation_id}
@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
@router.post("/chat/{conversation_id}", response_model=ChatResponse, tags=["Chat"])
async def handle_chat(request: ChatRequest,
                      conversation_id: Optional[str] = None,
                      current_user: User = Depends(get_current_user),
                      asset_service: AssetService = Depends(get_asset_service),
                      message_service: MessageService = Depends(get_message_service)):
    try:
        user_facility_id = current_user.facilityID
        print(f"handle_chat called by user: {current_user.email}, facilityID: {user_facility_id}")

        if conversation_id and request.conversation_id and conversation_id != request.conversation_id:
            print(f"Note: conversation_id provided in both path ({conversation_id}) and body ({request.conversation_id}); using path value.")

        use_conversation_id = conversation_id or request.conversation_id

        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        # Lưu tin nhắn của user trước
        user_message = MessageCreate(
            content=request.question,
            sender_type="user",
            sender_id=current_user.email
        )

        conversation_title_renew = generate_short_conversation_title(request.question) \
            if request.conversation_title == "New Chat" or request.conversation_title is None \
            else request.conversation_title

        saved_user_message = message_service.save_new_message(
            msg=user_message,
            email=current_user.email,
            facility_id=user_facility_id,
            conversation_id=use_conversation_id,
            conversation_title=conversation_title_renew,
        )
        conversation_id_str = str(saved_user_message.conversation_id)

        conversation_memories = []
        try:
            # Ensure memory_service is initialized lazily if possible
            if hasattr(message_service, '_ensure_memory_service'):
                message_service._ensure_memory_service()

            mem_service = getattr(message_service, 'memory_service', None)
            if mem_service is not None:
                try:
                    conversation_memories = mem_service.get_memories_by_email_and_conversation(
                        current_user.email, conversation_id_str, limit=5
                    )
                    print(f"Loaded {len(conversation_memories)} conversation memories for {current_user.email}/{conversation_id_str}")
                except Exception as e:
                    print(f"Warning: unable to fetch conversation memories: {e}")
            else:
                print("Memory service not available; skipping conversation memory fetch.")
        except Exception as e:
            print(f"Warning while initializing memory service: {e}")

        # Convert memory objects to strings (prefer 'content' field)
        memory_texts = []
        for m in conversation_memories:
            try:
                if isinstance(m, dict):
                    content = m.get('content') or m.get('text') or str(m)
                else:
                    content = str(m)
                memory_texts.append(content)
            except Exception:
                memory_texts.append(str(m))

        print("Calling detect_intent...")
        intent_data = detect_intent(request.question, memories=memory_texts)
        print(f"Intent data received: {intent_data}")

        intent = intent_data.get("intent", "unknown")
        entities = intent_data.get("entities", {})

        answer = ""
        used_generate = False

        if intent == "get_feed_info":
            answer = handle_get_feed_info(entities)
        elif intent == "get_medication_info":
            answer = handle_get_medication_info(entities)
        elif intent == "suggest_feed":
            answer = handle_suggest_feed(request.question, user_facility_id)
        elif intent == "suggest_medication":
            answer = handle_suggest_medication(request.question, user_facility_id)
        else:  # Unknown intent
            answer, used_generate = handle_general_chat(request.question, memory_texts)

        # --- Enhance the answer using Gemini + memories ---
        if not used_generate:
            try:
                generated = generate_answer(request.question, memories=memory_texts, assistant_context=answer)
                if generated and isinstance(generated, str) and generated.strip():
                    answer = generated.strip()
            except Exception as e:
                print(f"Warning: Gemini generate_answer failed: {e}")

        # Lưu phản hồi của bot
        bot_message = MessageCreate(
            content=answer,
            sender_type="bot",
            sender_id=None
        )

        saved_bot_message = message_service.save_new_message(
            msg=bot_message,
            email=current_user.email,
            facility_id=user_facility_id,
            conversation_id=conversation_id_str,
            conversation_title=request.conversation_title or "New Chat"
        )

        print(f"Final answer: {answer}")
        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id_str,
            conversation_title=conversation_title_renew,
            user_message_id=str(saved_user_message.id),
            bot_message_id=str(saved_bot_message.id)
        )

    except Exception as e:
        print(f"ERROR in handle_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
