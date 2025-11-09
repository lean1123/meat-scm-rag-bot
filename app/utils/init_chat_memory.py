import os

import weaviate
from dotenv import load_dotenv
from weaviate.classes.config import Property, DataType
from weaviate.collections.classes.config import Configure

from app.configurations.weaviate_config import (
    init_weaviate_client,
    close_weaviate_client,
)


memory_properties = [
    Property(
        name="email",
        data_type=DataType.TEXT,
        skip_vectorization=True,
    ),
    Property(
        name="memoryType",
        data_type=DataType.TEXT,  # (FACT, PREFERENCE, SUMMARY)
        skip_vectorization=True,
    ),
    Property(
        name="createdAt",
        data_type=DataType.DATE,
        skip_vectorization=True,
    ),
    Property(
        name="importanceScore",
        data_type=DataType.NUMBER,
        skip_vectorization=True,
    ),
    Property(
        name="content",
        data_type=DataType.TEXT,
        skip_vectorization=False,  # Đây là trường chính để vector hóa
    ),
    # conversationID được tách ra ngoài để dễ filter
    Property(
        name="conversationID",
        data_type=DataType.TEXT,
        skip_vectorization=True,
    ),

    # metadata vẫn giữ lại để chứa các thông tin phụ như sourceMessageID
    Property(
        name="metadata",
        data_type=DataType.OBJECT,
        skip_vectorization=True,
        nested_properties=[
            Property(name="sourceMessageID", data_type=DataType.TEXT),
        ],
    ),
]

collection_name = "ChatMemory"


def init_chat_memory_collection():
    client = init_weaviate_client()
    if client is None:
        print("Không thể kết nối tới Weaviate. Bỏ qua việc tạo collection.")
        return

    try:
        if client.collections.exists(collection_name):
            print(f"Collection '{collection_name}' đã tồn tại. Đang xóa...")
            client.collections.delete(collection_name)
            print("Đã xóa collection cũ.")

        print(f"Đang tạo collection '{collection_name}' với Gemini...")

        client.collections.create(
            name=collection_name,
            properties=memory_properties,
            vectorizer_config=Configure.Vectorizer.text2vec_transformers()
        )

        print(f"Collection '{collection_name}' đã được tạo thành công với Gemini.")

    except Exception as e:
        print(f"Lỗi khi tạo collection: {e}")


if __name__ == "__main__":
    try:
        init_chat_memory_collection()
    finally:
        close_weaviate_client()
        print("Đã đóng kết nối.")
