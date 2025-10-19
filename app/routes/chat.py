from app.services.asset_service import get_asset_info_by_id, get_current_feeds, get_current_medications
from app.services.farm_weaviate_service import search_knowledge_base
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
        user_facility_id = current_user.facilityID
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
            asset_id = entities.get("batch_id")  # Giữ tên entity để tương thích với AI model
            if not asset_id:
                answer = "Bạn muốn hỏi về đàn nào ạ? Vui lòng cung cấp mã đàn (ví dụ: ASSET_HEO_001)."
            else:
                feeds = get_current_feeds(asset_id, user_facility_id)
                if feeds:
                    current_feed = feeds[0] if feeds else None
                    if current_feed:
                        answer = (f"Đàn {asset_id} hiện đang sử dụng '{current_feed.get('name')}' "
                                f"với liều lượng {current_feed.get('dosageKg')} kg/con/ngày "
                                f"từ ngày {current_feed.get('startDate')} đến {current_feed.get('endDate')}. "
                                f"Ghi chú: {current_feed.get('notes', 'Không có ghi chú đặc biệt')}.")
                    else:
                        answer = f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}."
                else:
                    answer = f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}. Vui lòng kiểm tra lại mã đàn."

        elif intent == "get_medication_info":
            asset_id = entities.get("batch_id")  # Giữ tên entity để tương thích với AI model
            if not asset_id:
                answer = "Bạn muốn hỏi về lịch tiêm của đàn nào ạ? Vui lòng cung cấp mã đàn."
            else:
                medications = get_current_medications(asset_id, user_facility_id)
                if medications:
                    # Tìm vaccine có nextDueDate gần nhất
                    next_medication = None
                    for med in medications:
                        if med.get('nextDueDate'):
                            next_medication = med
                            break

                    if next_medication:
                        answer = (f"Theo lịch, đàn {asset_id} cần tiêm nhắc lại "
                                f"'{next_medication.get('name')}' vào ngày {next_medication.get('nextDueDate')} "
                                f"với liều lượng {next_medication.get('dose')}.")
                    else:
                        # Hiển thị thông tin vaccine đã tiêm gần nhất
                        latest_med = medications[-1] if medications else None
                        if latest_med:
                            answer = (f"Đàn {asset_id} đã được tiêm '{latest_med.get('name')}' "
                                    f"vào ngày {latest_med.get('dateApplied')} với liều lượng {latest_med.get('dose')}.")
                        else:
                            answer = f"Không tìm thấy thông tin về thuốc/vaccine cho đàn {asset_id}."
                else:
                    answer = f"Không tìm thấy thông tin lịch tiêm phòng cho đàn {asset_id}."
        elif intent == "suggest_feed":
            knowledge = search_knowledge_base(request.question, user_facility_id)
            if knowledge:
                answer = (f"Với vật nuôi giai đoạn '{knowledge['stage']}' từ ({knowledge['min_age_days']} - {knowledge['max_age_days']}), "
                          f"bạn nên dùng '{knowledge['recommended_feed']}' "
                          f"với liều lượng {knowledge['feed_dosage']}. "
                          f"Lưu ý: {knowledge['notes']}")
            else:
                answer = "Xin lỗi, tôi chưa tìm thấy hướng dẫn dinh dưỡng phù hợp trong cơ sở tri thức."

        elif intent == "suggest_medication":
            knowledge = search_knowledge_base(request.question, user_facility_id)
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
