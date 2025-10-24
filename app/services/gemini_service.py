import os
import google.generativeai as genai
import json
import traceback
from dotenv import load_dotenv
from typing import List, Optional

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
    đồng thời trích xuất các thông tin quan trọng (entities) như mã đàn (batch_id).

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
        "Bạn là một trợ lý AI cho hệ thống quản lý trang trại chăn nuôi. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, ngắn gọn và dựa trên dữ liệu có sẵn.",
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
