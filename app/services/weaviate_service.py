import os
import weaviate
from weaviate.classes.query import Filter
from dotenv import load_dotenv

load_dotenv()
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8080"))

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

def search_knowledge_base(query: str, farm_id: str) -> dict | None:
    if not client:
        print("ERROR: Weaviate client is not available.")
        return None

    try:
        knowledge_collection = client.collections.get("FarmingKnowledge")

        farm_filter = Filter.by_property("facilityID").equal(farm_id)

        result_farm = knowledge_collection.query.near_text(
            query=query,
            filters=farm_filter,
            limit=1
        )

        if result_farm.objects:
            print(f"Found specific knowledge for farm: {farm_id}")
            return result_farm.objects[0].properties

    except Exception as e:
        print(f"Error searching farm-specific knowledge: {e}")

    try:
        knowledge_collection = client.collections.get("FarmingKnowledge")

        global_filter = Filter.by_property("farm_id").equal("global")

        result_global = knowledge_collection.query.near_text(
            query=query,
            filters=global_filter,
            limit=1
        )

        if result_global.objects:
            print("Found global knowledge.")
            return result_global.objects[0].properties

    except Exception as e:
        print(f"Error searching global knowledge: {e}")

    return None