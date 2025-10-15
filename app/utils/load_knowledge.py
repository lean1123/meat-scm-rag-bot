# load_knowledge.py (Weaviate client v4)
import weaviate
from weaviate.classes.config import Property, DataType, Configure

# --- Dữ liệu tri thức mẫu ---
knowledge_data = [
    {
        "stage": "Tập ăn",
        "species": "Heo",
        "age_range": "25-45 ngày tuổi",
        "recommended_feed": "Green Feed tập ăn",
        "feed_dosage": "0.8 kg/con/ngày",
        "medication": "Tiêm vắc-xin E.coli",
        "notes": "Theo dõi tiêu hóa 2 ngày đầu sau tập ăn, đảm bảo cung cấp đủ nước sạch.",
        "facilityID": "farm-a"
    },
    {
        "stage": "Tăng trọng",
        "species": "Heo",
        "age_range": "46-90 ngày tuổi",
        "recommended_feed": "Cám CP 201",
        "feed_dosage": "2.5 kg/con/ngày",
        "medication": "Tẩy giun định kỳ",
        "notes": "Đảm bảo chuồng trại thoáng mát, mật độ nuôi phù hợp.",
        "facilityID": "farm-a"
    },
    {
        "stage": "Vỗ béo",
        "species": "Heo",
        "age_range": "91-150 ngày tuổi",
        "recommended_feed": "Cargill 803S",
        "feed_dosage": "3.5 kg/con/ngày",
        "medication": "Tiêm nhắc lại vắc-xin dịch tả",
        "notes": "Tăng cường rau xanh để cải thiện chất lượng thịt.",
        "facilityID": "farm-a"
    },
    {
        "stage": "Úm gà",
        "species": "Gà",
        "age_range": "1-21 ngày tuổi",
        "recommended_feed": "De Heus 111S",
        "feed_dosage": "20-50 g/con/ngày",
        "medication": "Vắc-xin Newcastle (lần 1), Gumboro",
        "notes": "Luôn giữ nhiệt độ chuồng úm ở 30-32°C, che chắn gió lùa.",
        "facilityID": "farm-b"
    }
]

# --- Kết nối tới Weaviate ---
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
)
print("✅ Connected to Weaviate.")

# --- Định nghĩa cấu trúc dữ liệu ---
class_name = "FarmingKnowledge"

# Xóa collection cũ nếu đã tồn tại
collections = client.collections.list_all()
if class_name in collections:
    client.collections.delete(class_name)
    print(f"🗑️ Deleted existing collection: {class_name}")

# Tạo collection mới
client.collections.create(
    name=class_name,
    properties=[
        Property(name="content", data_type=DataType.TEXT),
        Property(name="stage", data_type=DataType.TEXT),
        Property(name="species", data_type=DataType.TEXT),
        Property(name="age_range", data_type=DataType.TEXT),
        Property(name="recommended_feed", data_type=DataType.TEXT),
        Property(name="feed_dosage", data_type=DataType.TEXT),
        Property(name="medication", data_type=DataType.TEXT),
        Property(name="notes", data_type=DataType.TEXT),
        Property(name="facilityID", data_type=DataType.TEXT),
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
)
print(f"✅ Created new collection: {class_name}")

# --- Nạp dữ liệu vào Weaviate ---
collection = client.collections.get(class_name)
print("📦 Loading knowledge data into Weaviate...")

for item in knowledge_data:
    # Tạo content để vector hóa
    content = (
        f"Giai đoạn: {item['stage']}. "
        f"Loài: {item['species']}. "
        f"Độ tuổi: {item['age_range']}. "
        f"Thức ăn: {item['recommended_feed']}. "
        f"Thuốc: {item['medication']}."
    )

    data_object = item.copy()
    data_object["content"] = content
    collection.data.insert(data_object)

print("🎉 Data loaded successfully!")

# Đóng kết nối
client.close()
print("🔒 Connection closed.")
