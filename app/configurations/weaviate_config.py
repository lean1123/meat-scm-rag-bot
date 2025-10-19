import os
import weaviate
from dotenv import load_dotenv

load_dotenv()
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT"))

client = None

try:
    client = weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT
    )
    if client.is_live():
        print("Weaviate connection successful.")
    else:
        print("Weaviate connection failed: Server is not live.")
        client = None

except Exception as e:
    print(f"Could not connect to Weaviate: {e}")
    client = None

def get_weaviate_client():
    return client