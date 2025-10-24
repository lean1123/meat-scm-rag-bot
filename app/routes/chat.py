from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.asset_service import get_asset_service, AssetService
from app.services.auth_service import User
from app.services.auth_service import get_current_user
from app.services.farm_weaviate_service import search_knowledge_base
from app.services.gemini_service import detect_intent, generate_answer
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

        # If conversation_id provided both in path and body, prefer path and log
        if conversation_id and request.conversation_id and conversation_id != request.conversation_id:
            print(f"Note: conversation_id provided in both path ({conversation_id}) and body ({request.conversation_id}); using path value.")

        # Determine which conversation_id to use: path param takes precedence
        use_conversation_id = conversation_id or request.conversation_id

        question = request.question or ""
        question = question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        # Lưu tin nhắn của user trước
        user_message = MessageCreate(
            content=request.question,
            sender_type="user",
            sender_id=current_user.email
        )

        saved_user_message = message_service.save_new_message(
            msg=user_message,
            email=current_user.email,
            facility_id=user_facility_id,
            conversation_id=use_conversation_id,
            conversation_title=request.conversation_title or "New Chat"
        )

        conversation_id_str = str(saved_user_message.conversation_id)

        # --- Retrieve up to 5 conversation memories to provide context to the chatbot ---
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

        # if intent == "get_feed_info":
        #     asset_id = entities.get("batch_id")
        #     if not asset_id:
        #         answer = "Bạn muốn hỏi về đàn nào ạ? Vui lòng cung cấp mã đàn (ví dụ: ASSET_HEO_001)."
        #     else:
        #         feeds = asset_service.get_current_feeds(asset_id, user_facility_id)
        #         if feeds:
        #             current_feed = feeds[0] if feeds else None
        #             if current_feed:
        #                 answer = (f"Đàn {asset_id} hiện đang sử dụng '{current_feed.get('name')}' "
        #                           f"với liều lượng {current_feed.get('dosageKg')} kg/con/ngày "
        #                           f"từ ngày {current_feed.get('startDate')} đến {current_feed.get('endDate')}. "
        #                           f"Ghi chú: {current_feed.get('notes', 'Không có ghi chú đặc biệt')}.")
        #             else:
        #                 answer = f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}."
        #         else:
        #             answer = f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}. Vui lòng kiểm tra lại mã đàn."
        #
        # elif intent == "get_medication_info":
        #     asset_id = entities.get("batch_id")
        #     if not asset_id:
        #         answer = "Bạn muốn hỏi về lịch tiêm của đàn nào ạ? Vui lòng cung cấp mã đàn."
        #     else:
        #         medications = asset_service.get_current_medications(asset_id, user_facility_id)
        #         if medications:
        #             next_medication = None
        #             for med in medications:
        #                 if med.get('nextDueDate'):
        #                     next_medication = med
        #                     break
        #
        #             if next_medication:
        #                 answer = (f"Theo lịch, đàn {asset_id} cần tiêm nhắc lại "
        #                           f"'{next_medication.get('name')}' vào ngày {next_medication.get('nextDueDate')} "
        #                           f"với liều lượng {next_medication.get('dose')}.")
        #             else:
        #                 latest_med = medications[-1] if medications else None
        #                 if latest_med:
        #                     answer = (f"Đàn {asset_id} đã được tiêm '{latest_med.get('name')}' "
        #                               f"vào ngày {latest_med.get('dateApplied')} với liều lượng {latest_med.get('dose')}.")
        #                 else:
        #                     answer = f"Không tìm thấy thông tin về thuốc/vaccine cho đàn {asset_id}."
        #         else:
        #             answer = f"Không tìm thấy thông tin lịch tiêm phòng cho đàn {asset_id}."

        if intent == "get_feed_info":
            asset_id = entities.get("batch_id")
            if not asset_id:
                answer = "Bạn muốn hỏi về đàn nào ạ? Vui lòng cung cấp mã đàn (ví dụ: ASSET_HEO_001)."
            else:
                try:
                    asset = get_asset_trace(asset_id)
                except Exception as e:
                    print(f"Error fetching asset trace for {asset_id}: {e}")
                    answer = f"Không thể lấy thông tin cho đàn {asset_id}: {str(e)}"
                else:
                    # Try to extract feeds from the latest history details
                    full_history = asset.get("fullHistory", []) or asset.get("history", [])
                    latest_details = None
                    if full_history:
                        latest = full_history[-1]
                        latest_details = latest.get("details", {}) if isinstance(latest, dict) else {}

                    if not latest_details:
                        answer = f"Không tìm thấy thông tin nuôi/feeds cho đàn {asset_id}."
                    else:
                        feeds = latest_details.get("feeds") or latest_details.get("feed") or []
                        # feeds can be list of dicts or list of strings
                        if isinstance(feeds, list) and feeds:
                            # If items are dicts with name/dosage/startDate/endDate
                            if all(isinstance(f, dict) for f in feeds):
                                parts = []
                                for f in feeds:
                                    name = f.get("name") or f.get("feedName") or "(không tên)"
                                    dosage = f.get("dosageKg")
                                    start = f.get("startDate")
                                    end = f.get("endDate")
                                    note = f.get("notes")
                                    seg = f"{name}"
                                    if dosage is not None:
                                        seg += f" — liều {dosage} kg/con/ngày"
                                    if start or end:
                                        seg += f" (từ {start or '??'} đến {end or '??'})"
                                    if note:
                                        seg += f"; Ghi chú: {note}"
                                    parts.append(seg)
                                answer = f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(parts)
                            else:
                                # list of strings
                                answer = f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(str(x) for x in feeds)
                        else:
                            # Fallback to 'feed' simple list or top-level fields
                            feed_simple = latest_details.get("feed") or asset.get("feed") or asset.get("feeds")
                            if feed_simple:
                                answer = f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(str(x) for x in feed_simple)
                            else:
                                answer = f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}."

        elif intent == "get_medication_info":
            asset_id = entities.get("batch_id")
            if not asset_id:
                answer = "Bạn muốn hỏi về lịch tiêm của đàn nào ạ? Vui lòng cung cấp mã đàn."
            else:
                try:
                    asset = get_asset_trace(asset_id)
                except Exception as e:
                    print(f"Error fetching asset trace for {asset_id}: {e}")
                    answer = f"Không thể lấy thông tin cho đàn {asset_id}: {str(e)}"
                else:
                    full_history = asset.get("fullHistory", []) or asset.get("history", [])
                    latest_details = None
                    if full_history:
                        latest = full_history[-1]
                        latest_details = latest.get("details", {}) if isinstance(latest, dict) else {}

                    meds = []
                    if latest_details:
                        meds_field = latest_details.get("medications") or latest_details.get("medication")
                        if isinstance(meds_field, list) and meds_field:
                            # items may be strings or dicts
                            if all(isinstance(m, dict) for m in meds_field):
                                for m in meds_field:
                                    name = m.get("name") or m.get("medicationName") or "(không tên)"
                                    dose = m.get("dose")
                                    date_applied = m.get("dateApplied") or m.get("appliedDate")
                                    next_due = m.get("nextDueDate")
                                    seg = name
                                    if dose:
                                        seg += f" — liều: {dose}"
                                    if date_applied:
                                        seg += f"; đã áp dụng: {date_applied}"
                                    if next_due:
                                        seg += f"; hạn tiếp theo: {next_due}"
                                    meds.append(seg)
                            else:
                                meds = [str(x) for x in meds_field]

                    if meds:
                        answer = f"Thông tin thuốc/vắc-xin cho đàn {asset_id}: " + ", ".join(meds)
                    else:
                        # fallback: maybe medication info in asset top-level
                        top_meds = asset.get("medications") or asset.get("medication")
                        if top_meds:
                            answer = f"Thông tin thuốc/vắc-xin cho đàn {asset_id}: " + ", ".join(str(x) for x in top_meds)
                        else:
                            answer = f"Không tìm thấy thông tin thuốc/vắc-xin cho đàn {asset_id}."
        elif intent == "suggest_feed":
            knowledge = search_knowledge_base(request.question, user_facility_id)
            if knowledge:
                answer = (
                    f"Với vật nuôi giai đoạn '{knowledge['stage']}' từ ({knowledge['min_age_days']} - {knowledge['max_age_days']}), "
                    f"bạn nên dùng '{knowledge['recommended_feed']}' "
                    f"với liều lượng {knowledge['feed_dosage']}. "
                    f"Lưu ý: {knowledge['notes']}")
            else:
                answer = "Xin lỗi, tôi chưa tìm thấy hướng dẫn dinh dưỡng phù hợp trong cơ sở tri thức."

        elif intent == "suggest_medication":
            knowledge = search_knowledge_base(request.question, user_facility_id)
            if knowledge:
                answer = (f"Với vật nuôi giai đoạn '{knowledge['stage']}' từ ({knowledge['min_age_days']} - {knowledge['max_age_days']}), "
                          f"quy trình khuyến nghị có nhắc đến: '{knowledge['medication']}'. "
                          f"Lưu ý thêm: {knowledge['notes']}. Bạn nên tham khảo ý kiến của bác sĩ thú y để có liều lượng chính xác.")
            else:
                answer = "Xin lỗi, tôi chưa tìm thấy hướng dẫn về thuốc/vắc-xin phù hợp trong cơ sở tri thức."
        else:
            # Unknown intent -> treat as general chat: use Gemini with memories to produce an open response
            answer = ""
            used_generate = False
            try:
                generated_general = generate_answer(request.question, memories=memory_texts)
                if generated_general and isinstance(generated_general, str) and generated_general.strip():
                    answer = generated_general.strip()
                    used_generate = True
                else:
                    answer = "Xin lỗi, tôi chưa được huấn luyện để trả lời câu hỏi này. Bạn có thể hỏi về thông tin đàn, thức ăn hoặc thuốc men nhé."
            except Exception as e:
                print(f"Warning: generate_answer for general chat failed: {e}")
                answer = "Xin lỗi, tôi chưa được huấn luyện để trả lời câu hỏi này. Bạn có thể hỏi về thông tin đàn, thức ăn hoặc thuốc men nhé."

        # --- Enhance the answer using Gemini + memories ---
        try:
            # If we already generated an answer for unknown-intent using Gemini, skip extra enhancement.
            if not ("used_generate" in locals() and used_generate):
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
            user_message_id=str(saved_user_message.id),
            bot_message_id=str(saved_bot_message.id)
        )

    except Exception as e:
        print(f"ERROR in handle_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
