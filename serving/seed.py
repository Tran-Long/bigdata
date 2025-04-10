from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["movie_recommendation"]

# Dữ liệu
batch_scores = [
    {"movie_id": 1, "title": "Action Thriller", "genre": ["Action", "Thriller"], "score": 8.0},
    {"movie_id": 2, "title": "Drama Romance", "genre": ["Drama", "Romance"], "score": 7.0},
    {"movie_id": 3, "title": "Comedy Fun", "genre": ["Comedy", "Action"], "score": 6.5},
    {"movie_id": 4, "title": "Sci-Fi Adventure", "genre": ["Sci-Fi", "Adventure"], "score": 9.0},
    {"movie_id": 5, "title": "Horror Night", "genre": ["Horror"], "score": 7.5}
]

speed_scores = [
    {"movie_id": 1, "score": 7.5},
    {"movie_id": 2, "score": 8.0},
    {"movie_id": 3, "score": 7.0},
    {"movie_id": 4, "score": 8.5},
    {"movie_id": 5, "score": 7.2}
]

user_profiles = [
    {"user_id": 1, "preferred_genres": ["Action", "Comedy"]},
    {"user_id": 2, "preferred_genres": ["Drama", "Romance"]},
    {"user_id": 3, "preferred_genres": ["Sci-Fi", "Adventure"]}
]

# Xóa dữ liệu cũ nếu có
db.batch_scores.delete_many({})
db.speed_scores.delete_many({})
db.user_profiles.delete_many({})

# Insert mới
db.batch_scores.insert_many(batch_scores)
db.speed_scores.insert_many(speed_scores)
db.user_profiles.insert_many(user_profiles)

print("✅ Seed dữ liệu thành công vào MongoDB!")