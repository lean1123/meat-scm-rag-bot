from datetime import datetime, UTC
from typing import Any

from weaviate.classes.query import Filter, Sort

from app.configurations.weaviate_config import get_weaviate_client, close_weaviate_client

COLLECTION_NAME = "ChatMemory"


class WeaviateChatMemoryService:
    def __init__(self):
        self.client = get_weaviate_client()
        if self.client is None:
            raise Exception(
                "Weaviate client is not initialized. Call init_weaviate_client at application startup."
            )
        print("Đã kết nối Weaviate (service).")
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        if not self.client.collections.exists(COLLECTION_NAME):
            raise Exception(
                f"Collection '{COLLECTION_NAME}' không tồn tại. Vui lòng chạy file khởi tạo collection trước."
            )
        return self.client.collections.get(COLLECTION_NAME)

    def save_memory(self, email: str, conversation_id: str, memory_json: dict):
        created_at = memory_json.get(
            "createdAt", datetime.now(UTC).isoformat().replace("+00:00", "Z")
        )

        data = {
            "email": email,
            "conversationID": conversation_id,
            "memoryType": memory_json.get("memoryType", "FACT"),
            "createdAt": created_at,
            "importanceScore": memory_json.get("importanceScore", 0.0),
            "content": memory_json.get("content", ""),
            "metadata": {
                "sourceMessageID": memory_json.get("sourceMessageID", ""),
            },
        }

        try:
            self.collection.data.insert(properties=data)
            print(f"Đã lưu memory cho {email} ({conversation_id})")
        except Exception as e:
            print(f"Lỗi khi lưu memory: {e}")

    def get_memories_by_email(self, email: str, limit: int = 10) -> list[dict]:
        try:
            filter_expr = Filter.by_property("email").equal(email)
            result = self.collection.query.fetch_objects(
                filters=filter_expr,
                limit=limit,
            )
            return [obj.properties for obj in result.objects]
        except Exception as e:
            print(f"Lỗi khi truy vấn theo email: {e}")
            return []

    def get_memories_by_email_and_conversation(
            self, email: str, conversation_id: str, limit: int = 10
    ) -> list[dict]:
        try:
            filters = (
                    Filter.by_property("email").equal(email)
                    & Filter.by_property("conversationID").equal(conversation_id)
            )
            sort = Sort.by_property("createdAt", ascending=False)
            result = self.collection.query.fetch_objects(
                filters=filters,
                limit=limit,
                sort=sort,
            )
            return [obj.properties for obj in result.objects]
        except Exception as e:
            print(f"Lỗi khi truy vấn theo email + conversation: {e}")
            return []

    def delete_memories_by_conversation(self, email: str, conversation_id: str):
        try:
            filter_expr = (
                Filter.by_property("email").equal(email)
                & Filter.by_property("conversationID").equal(conversation_id)
            )
            result = self.collection.data.delete_many(where=filter_expr)
            print(f"Đã xoá {result['matches']} memory trong {conversation_id}")
        except Exception as e:
            print(f"Lỗi khi xoá memory: {e}")

    def close(self):
        # delegate to central close function
        close_weaviate_client()
        print("Đã đóng kết nối Weaviate (service).")
