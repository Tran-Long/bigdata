from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["moviesdb"]
collection = db["movies"]  # hoặc db["movies"] nếu bạn dùng tên khác

# Duyệt tất cả các document và cập nhật genre thành dạng list
for doc in collection.find():
    genre_str = doc.get("genre")
    if isinstance(genre_str, str):
        genre_list = genre_str.split("|")
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"genre": genre_list}}
        )

print("✅ Hoàn tất cập nhật trường genre thành danh sách.")
