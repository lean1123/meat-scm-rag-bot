import weaviate
from weaviate.classes.config import Property, DataType, Configure

# --- Dữ liệu tri thức mẫu ---
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
        "min_age_days": 1,
        "max_age_days": 21,
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
    port=8081,
)
print("Connected to Weaviate.")

# --- Định nghĩa cấu trúc dữ liệu ---
class_name = "FarmingKnowledge"

# Xóa collection cũ nếu đã tồn tại
collections = client.collections.list_all()
if class_name in collections:
    client.collections.delete(class_name)
    print(f"Deleted existing collection: {class_name}")

# Tạo collection mới
client.collections.create(
    name=class_name,
    properties=[
        Property(name="content", data_type=DataType.TEXT),
        Property(name="stage", data_type=DataType.TEXT),
        Property(name="species", data_type=DataType.TEXT),
        Property(name="min_age_days", data_type=DataType.INT),
        Property(name="max_age_days", data_type=DataType.INT),
        Property(name="recommended_feed", data_type=DataType.TEXT),
        Property(name="feed_dosage", data_type=DataType.TEXT),
        Property(name="medication", data_type=DataType.TEXT),
        Property(name="notes", data_type=DataType.TEXT),
        Property(name="facilityID", data_type=DataType.TEXT),
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
)
print(f"Created new collection: {class_name}")

# --- Nạp dữ liệu vào Weaviate ---
collection = client.collections.get(class_name)
print("Loading knowledge data into Weaviate...")

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


    data_object = item.copy()
    data_object["content"] = content
    collection.data.insert(data_object)

print("Data loaded successfully!")

# Đóng kết nối
client.close()
print("Connection closed.")
