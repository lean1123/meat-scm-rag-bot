import os
import weaviate
from dotenv import load_dotenv

load_dotenv()
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", 8081))

# Biến client toàn cục
_client = None


def init_weaviate_client(host: str = None, port: int = None):
    """
    Khởi tạo client Weaviate toàn cục. An toàn để gọi nhiều lần.
    Phiên bản này không còn xử lý API key của Google.
    """
    global _client
    if _client is not None:
        # Client đã được khởi tạo, trả về ngay lập tức
        return _client

    # Sử dụng giá trị mặc định nếu không được cung cấp
    host = host or WEAVIATE_HOST
    port = port or WEAVIATE_PORT

    try:
        # Kết nối tới Weaviate không cần headers chứa API key
        _client = weaviate.connect_to_local(host=host, port=port)

        if _client.is_live():
            print("Weaviate connection successful.")
            return _client
        else:
            print("Weaviate connection failed: Server is not live.")
            _client = None

    except Exception as e:
        print(f"Could not connect to Weaviate: {e}")
        _client = None

    return _client


def get_weaviate_client():
    """
    Trả về client toàn cục (có thể là None nếu chưa được khởi tạo).
    """
    return _client


def close_weaviate_client():
    """
    Đóng client toàn cục nếu nó tồn tại.
    """
    global _client
    try:
        if _client is not None and hasattr(_client, "close"):
            try:
                _client.close()
                print("Weaviate client closed.")
            except Exception as e:
                print(f"Error closing Weaviate client: {e}")
    finally:
        _client = None