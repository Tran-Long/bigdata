import pandas as pd
from pymongo import MongoClient

# Đọc file CSV, thay 'movies.csv' bằng đường dẫn file của bạn
df = pd.read_csv('movies.csv')

# Kiểm tra cấu trúc DataFrame (các cột)
print("Columns in CSV:", df.columns.tolist())

# Nếu cần, bạn có thể thực hiện một số xử lý. Ví dụ:
# - Đảm bảo rằng movie_id là kiểu số (int)
# - Nếu genre dưới dạng chuỗi, bạn có thể giữ nguyên hoặc chuyển thành list tuỳ vào cách bạn muốn lưu.
# Ở đây, chúng ta lưu genre dưới dạng chuỗi, bạn có thể thay đổi nếu mong muốn.
records = df.to_dict(orient='records')

# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["moviesdb"]  # Đặt tên database của bạn
metadata_collection = db["movies"]  # Collection nơi lưu thông tin phim

# Xóa dữ liệu cũ (nếu bạn muốn làm mới dữ liệu)
metadata_collection.delete_many({})

# Chèn các record vào MongoDB
result = metadata_collection.insert_many(records)

print(f"✅ Đã seed {len(result.inserted_ids)} movie records vào MongoDB.")
