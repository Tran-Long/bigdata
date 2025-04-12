from pymongo import MongoClient
from datetime import datetime, timedelta
import random

# Kết nối đến MongoDB (chỉnh sửa connection string nếu cần)
client = MongoClient("mongodb://localhost:27017")
db = client["moviesdb"]

# Xóa dữ liệu cũ (nếu cần)
db.batch_scores.delete_many({})
db.speed_scores.delete_many({})

# Giả sử chúng ta có 2 user để thử (user_id = 1 và user_id = 2) và 10 movie_ids từ 1 đến 10.
user_ids = [3, 4]
movie_ids = list(range(1, 11))  # 1,2,...,10

# Seed dữ liệu vào batch_scores:
# Ví dụ: user 1 có các phim 1,2,3,4,5; user 2 có các phim 6,7,8,9,10.
batch_data = []
batch_data.append({
    "user_id": 1,
    "recommendations": [
        {"movie_id": m_id, "rating": round(random.uniform(5, 9), 1)}
        for m_id in movie_ids[:5]
    ]
})
batch_data.append({
    "user_id": 2,
    "recommendations": [
        {"movie_id": m_id, "rating": round(random.uniform(5, 9), 1)}
        for m_id in movie_ids[5:]
    ]
})

db.batch_scores.insert_many(batch_data)
print("✅ Seeded batch_scores successfully.")

# Seed dữ liệu vào speed_scores:
# Đảm bảo mỗi movie_id từ 1 đến 10 có một document với thời gian hiện tại trong mảng window.
now = datetime.utcnow()
# Để dữ liệu speed luôn "mới", ta chọn start time cách đây 10-30 phút, end time cách đây 0-5 phút.
speed_data = []
for m_id in movie_ids:
    start_time = now - timedelta(minutes=random.randint(10, 30))
    end_time = now - timedelta(minutes=random.randint(0, 5))
    speed_data.append({
        "movie_id": m_id,
        "window": [start_time, end_time],
        "average_rating": round(random.uniform(3, 10), 1),
        "event_count": random.randint(1, 10)
    })

db.speed_scores.insert_many(speed_data)
print("✅ Seeded speed_scores successfully.")
