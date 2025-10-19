from weaviate.classes.query import Filter
from app.configurations.weaviate_config import client


# check weaviate client connection
if client is None:
    print("Weaviate client is not connected. Please check the configuration.")


def extract_age_days(query: str) -> int | None:
    import re
    match = re.search(r"(\d+)\s*ngày", query)
    return int(match.group(1)) if match else None

def search_knowledge_base(query: str, farm_id: str) -> dict | None:
    if not client:
        print("ERROR: Weaviate client is not available.")
        return None

    try:
        knowledge_collection = client.collections.get("FarmingKnowledge")
        age_days = extract_age_days(query)

        filters  = Filter.by_property("facilityID").equal(farm_id)

        if age_days is not None:
            filters = filters & Filter.by_property("min_age_days").less_or_equal(age_days)
            filters = filters & Filter.by_property("max_age_days").greater_or_equal(age_days)

        result_farm = knowledge_collection.query.near_text(
            query=query,
            filters=filters,
            limit=1
        )

        if result_farm.objects:
            print(f"Found specific knowledge for farm: {farm_id}")
            return result_farm.objects[0].properties

    except Exception as e:
        print(f"Error searching farm-specific knowledge: {e}")

    try:
        knowledge_collection = client.collections.get("FarmingKnowledge")

        global_filter = Filter.by_property("facilityID").equal("global")

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