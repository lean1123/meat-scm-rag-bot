import os
import weaviate
from dotenv import load_dotenv

load_dotenv()
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", 8081))
WEAVIATE_GOOGLE_KEY = os.getenv("GEMINI_API_KEY")

_client = None


def init_weaviate_client(host: str = None, port: int = None, google_key: str | None = None):
    """Initialize the global Weaviate client. Safe to call multiple times."""
    global _client
    if _client is not None:
        return _client

    host = host or WEAVIATE_HOST
    port = port or WEAVIATE_PORT
    google_key = google_key or WEAVIATE_GOOGLE_KEY

    try:
        headers = None
        if google_key:
            headers = {"X-Google-Generative-AI-Key": google_key}

        _client = weaviate.connect_to_local(host=host, port=port, headers=headers)
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
    """Return the global client (may be None if not initialized)."""
    return _client


def close_weaviate_client():
    """Close the global client if exists."""
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
