import os
import google.generativeai as genai
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("FATAL ERROR: GEMINI_API_KEY not found in .env file.")
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
else:
    print(f"Successfully loaded GEMINI_API_KEY starting with: {GEMINI_API_KEY[:4]}...")

genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel('gemini-2.5-pro')
    print("Gemini model 'gemini-pro' initialized successfully.")
except Exception as e:
    print("FATAL ERROR: Failed to initialize Gemini model.")
    traceback.print_exc()
    raise e

def detect_intent(user_question: str) -> dict:
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

    Dưới đây là câu hỏi của người dùng:
    "{user_question}"

    Hãy phân tích và trả về kết quả dưới dạng JSON.
    """

    try:
        response = model.generate_content(prompt)

        print("==== GEMINI RAW RESPONSE ====")
        print(response.text)
        print("=============================")

        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        result = json.loads(cleaned_response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Model response was: {response.text}")
        return {"intent": "unknown", "entities": {}, "error": "Failed to decode JSON from model response"}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"intent": "unknown", "entities": {}, "error": str(e)}