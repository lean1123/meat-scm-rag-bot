from weaviate.classes.config import Property, DataType
from weaviate.collections.classes.config import Configure, Tokenization, InvertedIndexConfig, BM25Config, \
    StopwordsConfig

from app.configurations.weaviate_config import init_weaviate_client, close_weaviate_client

knowledge_data = [
    {
        "stage": "Tập ăn",
        "species": "Heo",
        "min_age_days": 25,
        "max_age_days": 45,
        "recommended_feed": "Green Feed tập ăn",
        "feed_dosage": "0.8 kg/con/ngày",
        "medication": "Tiêm vắc-xin E.coli",
        "notes": "Theo dõi tiêu hóa 2 ngày đầu sau tập ăn, đảm bảo cung cấp đủ nước sạch.",
        "facilityID": "farm-a"
    },
    {
        "stage": "Tăng trọng",
        "species": "Heo",
        "min_age_days": 46,
        "max_age_days": 90,
        "recommended_feed": "Cám CP 201",
        "feed_dosage": "2.5 kg/con/ngày",
        "medication": "Tẩy giun định kỳ",
        "notes": "Đảm bảo chuồng trại thoáng mát, mật độ nuôi phù hợp.",
        "facilityID": "farm-a"
    },
    {
        "stage": "Vỗ béo",
        "species": "Heo",
        "min_age_days": 91,
        "max_age_days": 150,
        "recommended_feed": "Cargill 803S",
        "feed_dosage": "3.5 kg/con/ngày",
        "medication": "Tiêm nhắc lại vắc-xin dịch tả",
        "notes": "Tăng cường rau xanh để cải thiện chất lượng thịt.",
        "facilityID": "farm-a"
    },
{
        "stage": "Úm gà",
        "species": "Gà",
        "min_age_days": 21,
        "max_age_days": 41,
        "recommended_feed": "Cargill 803S",
        "feed_dosage": "3.5 kg/con/ngày",
        "medication": "Tiêm nhắc lại vắc-xin dịch tả",
        "notes": "Tăng cường rau xanh để cải thiện chất lượng thịt.",
        "facilityID": "farm-b"
    }
]


class_name = "FarmingKnowledge"


def load_knowledge_to_weaviate():
    # initialize client via config
    client = init_weaviate_client()
    if client is None:
        print("Không thể kết nối tới Weaviate. Bỏ qua việc nạp dữ liệu.")
        return

    try:
        if client.collections.exists(class_name):
            print(f"Collection '{class_name}' đã tồn tại. Đang xóa...")
            client.collections.delete(class_name)
            print("Đã xóa collection cũ.")

        print(f"Đang tạo collection '{class_name}' với Gemini...")

        # client.collections.create(
        #     name=class_name,
        #     properties=[
        #         Property(name="content", data_type=DataType.TEXT),
        #         Property(name="stage", data_type=DataType.TEXT),
        #         Property(name="species", data_type=DataType.TEXT),
        #         Property(name="min_age_days", data_type=DataType.INT),
        #         Property(name="max_age_days", data_type=DataType.INT),
        #         Property(name="recommended_feed", data_type=DataType.TEXT),
        #         Property(name="feed_dosage", data_type=DataType.TEXT),
        #         Property(name="medication", data_type=DataType.TEXT),
        #         Property(name="notes", data_type=DataType.TEXT),
        #         Property(name="facilityID", data_type=DataType.TEXT)
        #     ],
        #     vectorizer_config=Configure.Vectorizer.text2vec_transformers()
        # )

        stopwords_cfg = StopwordsConfig(
            preset="en",
            additions=[],
            removals=[]
        )

        inverted_cfg = InvertedIndexConfig(
            bm25=BM25Config(k1=1.2, b=0.75),
            cleanup_interval_seconds=60,
            index_null_state=True,
            index_property_length=True,
            index_timestamps=True,
            stopwords=stopwords_cfg,
        )

        client.collections.create(
            name=class_name,
            properties=[
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="stage",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="species",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(name="min_age_days", data_type=DataType.INT, index_filterable=True),
                Property(name="max_age_days", data_type=DataType.INT, index_filterable=True),
                Property(
                    name="recommended_feed",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="feed_dosage",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="medication",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="notes",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.WORD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
                Property(
                    name="facilityID",
                    data_type=DataType.TEXT,
                    tokenization=Tokenization.FIELD,
                    index_filterable=True,
                    index_searchable=True,
                    inverted_index_config=inverted_cfg,
                ),
            ],
            vectorizer_config=Configure.Vectorizer.text2vec_transformers()
        )

        print(f"Collection '{class_name}' đã được tạo thành công với Gemini.")

        # --- Nạp dữ liệu vào Weaviate ---
        collection = client.collections.get(class_name)
        print("Đang tải dữ liệu kiến thức vào Weaviate...")

        for item in knowledge_data:
            content = (
                f"Thông tin chăn nuôi: Giai đoạn {item['stage']} của loài {item['species']} "
                f"từ {item['min_age_days']} đến {item['max_age_days']} ngày tuổi. "
                f"Thức ăn phù hợp là {item['recommended_feed']} với liều lượng {item['feed_dosage']}. "
                f"Thuốc cần dùng: {item['medication']}. "
                f"Ghi chú: {item['notes']}."
            )

            data_object = item.copy()
            data_object["content"] = content
            collection.data.insert(data_object)

        print("Dữ liệu đã được tải thành công!")

    except Exception as e:
        print(f"Lỗi khi tạo collection hoặc tải dữ liệu: {e}")


if __name__ == "__main__":
    try:
        load_knowledge_to_weaviate()
    finally:
        close_weaviate_client()
        print("Đã đóng kết nối.")
