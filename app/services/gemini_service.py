import os
import google.generativeai as genai
import json
import traceback
from dotenv import load_dotenv
from typing import List, Optional

from app.services.farm_weaviate_service import search_knowledge_base
from app.services.get_asset_http_service import get_asset_trace

load_dotenv()

# Read API key but don't raise on import; allow lazy initialization
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print(f"Successfully loaded GEMINI_API_KEY starting with: {GEMINI_API_KEY[:4]}...")
    except Exception:
        print("Warning: failed to configure genai with provided GEMINI_API_KEY")
else:
    print("Warning: GEMINI_API_KEY not found in environment; Gemini calls will be disabled until key is provided.")

# Lazy model holder
_MODEL = None

def get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if not GEMINI_API_KEY:
        return None
    try:
        _MODEL = genai.GenerativeModel('gemini-2.5-flash')
        print("Gemini model initialized lazily.")
        return _MODEL
    except Exception:
        traceback.print_exc()
        return None


def detect_intent(user_question: str, memories: Optional[List[str]] = None) -> dict:
    """
    Phân tích ý định từ `user_question` và trả về JSON với key "intent" và "entities".
    Nếu `memories` được cung cấp, chèn chúng vào prompt như một khối tham khảo mà không thay đ��i định dạng
    hoặc mục đích của prompt (vẫn yêu cầu trả về JSON với key "intent").
    """

    # Build memories block (kept concise so model vẫn trả JSON giữ nguyên format)
    memories_block = ""
    if memories:
        try:
            mb_lines = [f"- {m}" for m in memories if m]
            if mb_lines:
                memories_block = "Các đoạn ghi nhớ liên quan (memories):\n" + "\n".join(mb_lines) + "\n\n"
        except Exception:
            memories_block = ""

    prompt = f"""
    Bạn là một trợ lý AI chuyên phân tích ý định của người dùng cho một chatbot quản lý trang trại chăn nuôi.
    Nhiệm vụ của bạn là đọc câu hỏi của người dùng và phân loại nó vào một trong các ý định (intent) sau đây,
    đồng thời trích xuất các thông tin quan trọng (entities) như mã đàn (batch_id), (species) là loại vật nuôi 
    mà người dùng hỏi ví dụ (tôi muốn hỏi thông tin về đàn heo 001? - species là heo).

    Các intent có thể có:
    - get_feed_info: Hỏi về thông tin thức ăn của một đàn cụ thể. (Ví dụ: "Đàn H001 đang ăn gì?", "Thức ăn của đàn B012?")
    - get_medication_info: Hỏi về thông tin thuốc men, lịch tiêm của một đàn cụ thể. (Ví dụ: "Đàn H001 đã tiêm vắc-xin gì?", "Lịch tiêm phòng của đàn G003?")
    - suggest_feed: Cần gợi ý, tư vấn loại thức ăn phù hợp với độ tuổi hoặc giai đoạn. (Ví dụ: "Heo 35 ngày tuổi nên ăn gì?", "Gà con mới nở cho ăn cám nào?")
    - suggest_medication: Cần gợi ý, tư vấn về thuốc hoặc lịch tiêm phòng. (Ví dụ: "Heo con mới nhập chuồng cần tiêm gì?", "Bò bị ho nên dùng thuốc nào?")
    - unknown: Các câu hỏi không liên quan, câu chào hỏi, hoặc không xác định được. (Ví dụ: "Chào bạn", "Thời tiết hôm nay thế nào?", "Cho xem hình ảnh")

    Yêu cầu đầu ra:
    - Trả về kết quả dưới dạng một chuỗi JSON hợp lệ.
    - JSON object phải có key "intent".
    - Nếu câu hỏi chứa mã đàn (ví dụ: H001, B012), hãy trích xuất nó vào key "entities" với key con là "batch_id". Nếu không có, entities là một object rỗng.

    """

    # Insert memories before the user question (do not change expected JSON output format)
    if memories_block:
        prompt = prompt + "\n" + memories_block

    prompt = prompt + f"\nDưới đây là câu hỏi của người dùng:\n\"{user_question}\"\n\nHãy phân tích và trả về kết quả dưới dạng JSON."

    raw_text = None
    try:
        model_obj = get_model()
        if model_obj is None:
            print("Gemini model not available; returning unknown intent.")
            return {"intent": "unknown", "entities": {}, "error": "Gemini model not initialized"}

        response = model_obj.generate_content(prompt)

        raw_text = getattr(response, 'text', None) or str(response)
        print("==== GEMINI RAW RESPONSE ====")
        print(raw_text)
        print("=============================")

        cleaned_response_text = raw_text.strip().replace("```json", "").replace("```", "").strip()

        result = json.loads(cleaned_response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Model response was: {raw_text if raw_text is not None else '<<no response>>'}")
        return {"intent": "unknown", "entities": {}, "error": "Failed to decode JSON from model response"}
    except Exception as e:
        print(f"An error occurred in detect_intent: {e}")
        traceback.print_exc()
        return {"intent": "unknown", "entities": {}, "error": str(e)}


def generate_answer(user_question: str, memories: Optional[List[str]] = None, assistant_context: Optional[str] = None) -> str:
    """Generate a helpful conversational answer using Gemini, incorporating conversation memories if provided.

    This function treats `memories` as contextual snippets to help Gemini respond better. It does not change
    the intent-detection prompt format used elsewhere; it's intended to produce a natural-language reply.
    """

    # Build memories block (short, readable list)
    memories_block = ""
    if memories:
        try:
            # truncate each memory to a safe length to avoid overly long prompts
            MAX_MEM_CHARS = 800
            mb_lines = []
            for m in memories:
                if not m:
                    continue
                text = str(m)
                if len(text) > MAX_MEM_CHARS:
                    text = text[:MAX_MEM_CHARS].rstrip() + "..."
                mb_lines.append(f"- {text}")
            if mb_lines:
                memories_block = "Các đoạn ghi nhớ liên quan (memories):\n" + "\n".join(mb_lines)
        except Exception:
            memories_block = ""

    # Optionally include previous assistant context
    context_block = ""
    if assistant_context:
        ctx = str(assistant_context).strip()
        if ctx:
            context_block = f"Gợi ý trước đó từ hệ thống: {ctx}"

    # Compose final prompt for a conversational answer
    prompt_parts = [
        "Bạn là một trợ lý AI cho hệ thống quản lý trang trại chăn nuôi. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, ngắn gọn "
        "và dựa trên dữ liệu có sẵn. Nếu không có dữ liệu tồn tại thì không suy đoán mà hãy nói rõ rằng bạn không có thông tin đó. VD: "
        "'Tôi xin lỗi', 'tôi không có thông tin về điều đó tại thời điểm này.'"
    ]

    if memories_block:
        prompt_parts.append(memories_block)

    if context_block:
        prompt_parts.append(context_block)

    prompt_parts.append(f"Người dùng hỏi: \"{user_question}\"\nHãy trả lời bằng tiếng Việt, trực tiếp, cụ thể và nếu cần đề xuất bước tiếp theo.")

    final_prompt = "\n\n".join(prompt_parts)

    raw_text = None
    try:
        model_obj = get_model()
        if model_obj is None:
            print("Gemini model not available; cannot generate answer.")
            return "Xin lỗi, hiện tại không thể tạo câu trả lời tự động. Vui lòng thử lại sau."

        response = model_obj.generate_content(final_prompt)
        raw_text = getattr(response, 'text', None) or str(response)
        # Clean code fences and return text
        cleaned = raw_text.strip().replace("```", "").strip()
        return cleaned
    except Exception as e:
        print(f"Error generating answer from Gemini: {e}")
        traceback.print_exc()
        return "Xin lỗi, hiện tại không thể tạo câu trả lời tự động. Vui lòng thử lại sau."

def generate_short_conversation_title(user_question: str) -> str:
    """Generate a short conversation title based on the user's initial question."""

    prompt = f"""
    Bạn là một trợ lý AI giúp tạo tiêu đề ngắn gọn cho cuộc trò chuyện dựa trên câu hỏi của người dùng.
    Hãy tạo một tiêu đề súc tích, rõ ràng, không quá 6 từ, phản ánh nội dung chính của câu hỏi sau:

    Câu hỏi của người dùng: "{user_question}"

    Yêu cầu đầu ra:
    - Trả về chỉ tiêu đề dưới dạng một chuỗi văn bản ngắn.
    - Tiêu đề không được vượt quá 6 từ.
    - Không thêm bất kỳ giải thích hoặc định dạng nào khác.
    """

    raw_text = None
    try:
        model_obj = get_model()
        if model_obj is None:
            print("Gemini model not available; cannot generate title.")
            return "Cuộc trò chuyện mới"

        response = model_obj.generate_content(prompt)
        raw_text = getattr(response, 'text', None) or str(response)
        cleaned = raw_text.strip().replace("```", "").strip()

        # Truncate to 6 words if necessary
        words = cleaned.split()
        if len(words) > 6:
            cleaned = " ".join(words[:6])

        return cleaned
    except Exception as e:
        print(f"Error generating conversation title from Gemini: {e}")
        traceback.print_exc()
        return "Cuộc trò chuyện mới"

def handle_get_feed_info(entities: dict) -> str:
    """
    Xử lý intent lấy thông tin thức ăn của đàn.
    """
    asset_id = entities.get("batch_id")
    if not asset_id:
        return "Bạn muốn hỏi về đàn nào ạ? Vui lòng cung cấp mã đàn (ví dụ: ASSET_HEO_001)."

    try:
        asset = get_asset_trace(asset_id)
    except Exception as e:
        print(f"Error fetching asset trace for {asset_id}: {e}")
        return f"Không thể lấy thông tin cho đàn {asset_id}: {str(e)}"

    full_history = asset.get("fullHistory", []) or asset.get("history", [])
    latest_details = {}
    if full_history:
        latest = full_history[-1]
        latest_details = latest.get("details", {}) if isinstance(latest, dict) else {}

    if not latest_details:
        return f"Không tìm thấy thông tin nuôi/feeds cho đàn {asset_id}."

    feeds = latest_details.get("feeds") or latest_details.get("feed") or []
    if isinstance(feeds, list) and feeds:
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
            return f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(parts)
        else:
            return f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(str(x) for x in feeds)
    else:
        feed_simple = latest_details.get("feed") or asset.get("feed") or asset.get("feeds")
        if feed_simple:
            return f"Đàn {asset_id} hiện dùng các loại thức ăn: " + ", ".join(str(x) for x in feed_simple)
        else:
            return f"Không tìm thấy thông tin thức ăn cho đàn {asset_id}."

def handle_get_medication_info(entities: dict) -> str:
    """
    Xử lý intent lấy thông tin thuốc/vắc-xin của đàn.
    """
    asset_id = entities.get("batch_id")
    if not asset_id:
        return "Bạn muốn hỏi về lịch tiêm của đàn nào ạ? Vui lòng cung cấp mã đàn."

    try:
        asset = get_asset_trace(asset_id)
    except Exception as e:
        print(f"Error fetching asset trace for {asset_id}: {e}")
        return f"Không thể lấy thông tin cho đàn {asset_id}: {str(e)}"

    full_history = asset.get("fullHistory", []) or asset.get("history", [])
    latest_details = {}
    if full_history:
        latest = full_history[-1]
        latest_details = latest.get("details", {}) if isinstance(latest, dict) else {}

    meds = []
    if latest_details:
        meds_field = latest_details.get("medications") or latest_details.get("medication")
        if isinstance(meds_field, list) and meds_field:
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
        return f"Thông tin thuốc/vắc-xin cho đàn {asset_id}: " + ", ".join(meds)
    else:
        top_meds = asset.get("medications") or asset.get("medication")
        if top_meds:
            return f"Thông tin thuốc/vắc-xin cho đàn {asset_id}: " + ", ".join(str(x) for x in top_meds)
        else:
            return f"Không tìm thấy thông tin thuốc/vắc-xin cho đàn {asset_id}."

def handle_suggest_feed(question: str, facility_id: str) -> str:
    """
    Xử lý intent gợi ý thức ăn từ cơ sở tri thức.
    """
    knowledge = search_knowledge_base(question, facility_id)
    if knowledge:
        return (
            f"Với vật nuôi giai đoạn '{knowledge['stage']}' từ ({knowledge['min_age_days']} - {knowledge['max_age_days']}), "
            f"bạn nên dùng '{knowledge['recommended_feed']}' "
            f"với liều lượng {knowledge['feed_dosage']}. "
            f"Lưu ý: {knowledge['notes']}"
        )
    else:
        return "Xin lỗi, tôi chưa tìm thấy hướng dẫn dinh dưỡng phù hợp trong cơ sở tri thức."

def handle_suggest_medication(question: str, facility_id: str) -> str:
    """
    Xử lý intent gợi ý thuốc/vắc-xin từ cơ sở tri thức.
    """
    knowledge = search_knowledge_base(question, facility_id)
    if knowledge:
        return (
            f"Với vật nuôi giai đoạn '{knowledge['stage']}' từ ({knowledge['min_age_days']} - {knowledge['max_age_days']}), "
            f"quy trình khuyến nghị có nhắc đến: '{knowledge['medication']}'. "
            f"Lưu ý thêm: {knowledge['notes']}. Bạn nên tham khảo ý kiến của bác sĩ thú y để có liều lượng chính xác."
        )
    else:
        return "Xin lỗi, tôi chưa tìm thấy hướng dẫn về thuốc/vắc-xin phù hợp trong cơ sở tri thức."


def handle_general_chat(question: str, memories: list) -> tuple[str, bool]:
    """
    Xử lý các câu hỏi chung (unknown intent) bằng cách gọi đến Gemini.
    Trả về câu trả lời và một cờ báo hiệu đã sử dụng generate_answer hay chưa.
    """
    try:
        generated_general = generate_answer(question, memories=memories)
        if generated_general and isinstance(generated_general, str) and generated_general.strip():
            return generated_general.strip(), True
    except Exception as e:
        print(f"Warning: generate_answer for general chat failed: {e}")

    fallback_answer = "Xin lỗi, tôi chưa được huấn luyện để trả lời câu hỏi này. Bạn có thể hỏi về thông tin đàn, thức ăn hoặc thuốc men nhé."
    return fallback_answer, False
