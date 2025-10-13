from app.services.mongo_service import get_batch_info_by_id
from app.services.weaviate_service import search_knowledge_base
from app import auth
from app.auth import User
from app.services.gemini_service import detect_intent
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def handle_chat(request: ChatRequest, current_user: User = Depends(auth.get_current_user)):
    try:
        user_farm_id = current_user.farm_id
        question = request.question.lower()

        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        print("Calling detect_intent...")
        intent_data = detect_intent(request.question)
        print(f"Intent data received: {intent_data}")

        intent = intent_data.get("intent", "unknown")
        entities = intent_data.get("entities", {})

        answer = ""

        if intent == "get_feed_info":
            batch_id = entities.get("batch_id")
            if not batch_id:
                answer = "Bạn muốn hỏi về đàn nào ạ? Vui lòng cung cấp mã đàn (ví dụ: H001)."
            else:
                batch_data = get_batch_info_by_id(batch_id, user_farm_id)
                if batch_data and "current_feed" in batch_data:
                    feed_info = batch_data["current_feed"]
                    answer = (f"Đàn {batch_id} hiện đang sử dụng '{feed_info.get('name')}' "
                              f"với liều lượng {feed_info.get('dosage_kg_per_day')} kg/con/ngày "
                              f"cho giai đoạn '{feed_info.get('stage')}'.")
                else:
                    answer = f"Không tìm thấy thông tin thức ăn cho đàn {batch_id}. Vui lòng kiểm tra lại mã đàn."

        elif intent == "get_medication_info":
            batch_id = entities.get("batch_id")
            if not batch_id:
                answer = "Bạn muốn hỏi về lịch tiêm của đàn nào ạ? Vui lòng cung cấp mã đàn."
            else:
                batch_data = get_batch_info_by_id(batch_id, user_farm_id)
                if batch_data and "next_vaccination_schedule" in batch_data:
                    next_vax = batch_data["next_vaccination_schedule"]
                    answer = (f"Theo lịch, đàn {batch_id} cần tiêm nhắc lại vắc-xin "
                              f"'{next_vax.get('name')}' vào ngày {next_vax.get('date')}.")
                else:
                    answer = f"Không tìm thấy thông tin lịch tiêm phòng cho đàn {batch_id}."
        elif intent == "suggest_feed":
            knowledge = search_knowledge_base(request.question, user_farm_id)
            if knowledge:
                answer = (f"Với vật nuôi giai đoạn '{knowledge['stage']}' ({knowledge['age_range']}), "
                          f"bạn nên dùng '{knowledge['recommended_feed']}' "
                          f"với liều lượng {knowledge['feed_dosage']}. "
                          f"Lưu ý: {knowledge['notes']}")
            else:
                answer = "Xin lỗi, tôi chưa tìm thấy hướng dẫn dinh dưỡng phù hợp trong cơ sở tri thức."

        elif intent == "suggest_medication":
            knowledge = search_knowledge_base(request.question, user_farm_id)
            if knowledge:
                answer = (f"Đối với vật nuôi giai đoạn '{knowledge['stage']}' ({knowledge['age_range']}), "
                          f"quy trình khuyến nghị có nhắc đến: '{knowledge['medication']}'. "
                          f"Lưu ý thêm: {knowledge['notes']}. Bạn nên tham khảo ý kiến của bác sĩ thú y để có liều lượng chính xác.")
            else:
                answer = "Xin lỗi, tôi chưa tìm thấy hướng dẫn về thuốc/vắc-xin phù hợp trong cơ sở tri thức."
        else:
            answer = "Xin lỗi, tôi chưa được huấn luyện để trả lời câu hỏi này. Bạn có thể hỏi về thông tin đàn, thức ăn hoặc thuốc men nhé."

        print(f"Final answer: {answer}")
        return ChatResponse(answer=answer)

    except Exception as e:
        print(f"ERROR in handle_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
