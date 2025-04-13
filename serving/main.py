from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv("./serve.env")
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB = os.getenv("MONGODB_DB")
MOVIES_COLLECTION = os.getenv("MOVIES_COLLECTION")
SPEEDLAYER_COLLECTION = os.getenv("SPEEDLAYER_COLLECTION")
BATCHLAYER_COLLECTION = os.getenv("BATCHLAYER_COLLECTION")
USER_COLLECTION = os.getenv("USER_COLLECTION")
assert MONGODB_URL is not None and MONGODB_DB is not None and MOVIES_COLLECTION is not None, "MONGODB_URL, MONGODB_DB, MOVIES_COLLECTION không được để trống"
assert SPEEDLAYER_COLLECTION is not None and BATCHLAYER_COLLECTION is not None, "SPEEDLAYER_COLLECTION, BATCHLAYER_COLLECTION không được để trống"

app = FastAPI(title="Movie Recommendation API with MongoDB")

# ---------- MongoDB setup ----------
mongo_client = MongoClient(MONGODB_URL)
mongo_db = mongo_client[MONGODB_DB]

# Collection chứa dữ liệu đánh giá từ các layer:
batch_collection = mongo_db[BATCHLAYER_COLLECTION]
speed_collection = mongo_db[SPEEDLAYER_COLLECTION]
user_profiles_collection = mongo_db[USER_COLLECTION]

# Collection lưu thông tin metadata phim (movie_id, title, genre)
movie_metadata_collection = mongo_db["movies"]

# ---------- Utility: Lấy thông tin phim từ movie_metadata ----------
def get_movie_info(movie_id: int):
    """
    Query MongoDB để lấy thông tin phim từ collection movie_metadata.
    Giả sử field "genre" được lưu dưới dạng danh sách (array) trực tiếp.
    Nếu genre được lưu dưới dạng chuỗi, bạn có thể chỉnh sửa lại logic tách chuỗi.
    """
    movie = movie_metadata_collection.find_one({"movie_id": movie_id})
    if movie:
        return {
            "title": movie.get("title"),
            "genre": movie.get("genre")  # giả sử đây là list, nếu là chuỗi, cần split bằng dấu phẩy
        }
    return None

# ---------- Utility functions ----------
def normalize_score(score: float, min_val: float, max_val: float) -> float:
    if max_val - min_val == 0:
        return 10.0
    return ((score - min_val) / (max_val - min_val)) * 10.0

def genre_similarity(movie_genres: List[str], user_genres: List[str]) -> float:
    if not movie_genres:
        return 0.0
    return sum(1 for g in movie_genres if g in user_genres) / len(movie_genres)

def calculate_final_score(rating: float, average_rating: float, similarity: float, alpha: float = 0.7) -> float:
    # Giả sử:
    # rating từ batch layer có phạm vi [5, 9]
    # average_rating từ speed layer có phạm vi [3, 10]
    min_batch, max_batch = 5, 9
    min_speed, max_speed = 3, 10

    batch_norm = normalize_score(rating, min_batch, max_batch)
    speed_norm = normalize_score(average_rating, min_speed, max_speed)
    merge_score = alpha * batch_norm + (1 - alpha) * speed_norm
    final_score = merge_score * (1 + similarity)
    return final_score

def infer_user_preferences(user_id: int) -> List[str]:
    """
    Infer preferred genres của user dựa vào dữ liệu từ batch_scores và metadata phim từ movie_metadata.
    """
    batch_doc = batch_collection.find_one({"user_id": user_id})
    if not batch_doc:
        return []
    genre_count = {}
    for rec in batch_doc.get("recommendations", []):
        movie_id = rec.get("movie_id")
        if not movie_id:
            continue
        movie_info = get_movie_info(movie_id)
        if not movie_info:
            continue
        for genre in movie_info["genre"]:
            genre_count[genre] = genre_count.get(genre, 0) + 1
    sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)
    return [genre for genre, count in sorted_genres[:2]]



# ---------- Endpoint: Recommendations ------------
@app.get("/api/user/{user_id}/recommendations")
def get_recommendations(user_id: int, top_n: int = Query(10, description="Số lượng phim gợi ý cần trả về")):
    # # Lấy thông tin user từ MongoDB (user_profiles); nếu không tồn tại, infer sở thích và tạo document mặc định.
    user_profile = user_profiles_collection.find_one({"user_id": user_id})
    if not user_profile:
        inferred = infer_user_preferences(user_id)
        user_profile = {"user_id": user_id, "preferred_genres": inferred}
        user_profiles_collection.insert_one(user_profile)

    alpha = 0.7
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    # Lấy dữ liệu từ batch_scores cho user
    batch_doc = batch_collection.find_one({"user_id": user_id})
    batch_data = {}
    if batch_doc:
        for rec in batch_doc.get("recommendations", []):
            movie_id = rec.get("movie_id")
            if not movie_id:
                continue
            batch_data[movie_id] = rec["rating"]
    # Lấy dữ liệu từ speed_scores, sử dụng "window.1" để lọc theo thời gian (end time ≥ one_hour_ago)
    speed_cursor = speed_collection.find({"window.1": {"$gte": one_hour_ago}})
    speed_data = {}
    for doc in speed_cursor:
        movie_id = doc.get("movie_id")
        if not movie_id:
            continue
        speed_data[movie_id] = doc["average_rating"]

    # print("DEBUG: User profile:", user_profile)
    # print("DEBUG: Batch data:", batch_data)
    # print("DEBUG: Speed data:", speed_data)

    recommendations = []
    for movie_id, rating in batch_data.items():
        if movie_id not in speed_data:
            movie_info = get_movie_info(movie_id)
            if not movie_info:
                continue
            recommendations.append({
                "movie_id": movie_id,
                "title": movie_info["title"],
                "genres": movie_info["genre"],
                "rating": rating,
                "average_rating": rating,
                "merge_score": rating,
                "similarity": 1,
                "final_score": rating
            })
            continue  # bỏ qua nếu không có dữ liệu speed gần đây
        avg_rating = speed_data[movie_id]
        movie_info = get_movie_info(movie_id)
        if not movie_info:
            continue
        sim = genre_similarity(movie_info["genre"], user_profile["preferred_genres"])
        final_score = calculate_final_score(rating, avg_rating, sim, alpha)
        merge_score = alpha * rating + (1 - alpha) * avg_rating
        recommendations.append({
            "movie_id": movie_id,
            "title": movie_info["title"],
            "genres": movie_info["genre"],
            "rating": rating,
            "average_rating": avg_rating,
            "merge_score": merge_score,
            "similarity": sim,
            "final_score": final_score
        })

    recommendations.sort(key=lambda x: x["final_score"], reverse=True)
    return {
        "user_id": user_id,
        "preferred_genres": user_profile["preferred_genres"],
        "recommendations": recommendations[:top_n]
    }


# ---------- Endpoint: Trending Movies ------------
@app.get("/api/trending/movies")
def get_trending_movies(top_n: int = Query(10, description="Số lượng phim trending cần trả về")):
    one_hour_ago = datetime.now() - timedelta(hours=1)

    # Tập hợp dữ liệu batch từ tất cả các user
    batch_docs = list(batch_collection.find())
    batch_data = {}
    for doc in batch_docs:
        for rec in doc.get("recommendations", []):
            movie_id = rec.get("movie_id")
            if not movie_id:
                continue
            # Nếu có nhiều rating cho cùng movie, chỉ lấy giá trị cuối cùng (hoặc bạn có thể tính trung bình)\n            batch_data[movie_id] = rec[\"rating\"]\n"
            batch_data[movie_id] = rec["rating"]

    speed_cursor = speed_collection.find({"window.1": {"$gte": one_hour_ago}})
    speed_data = {}
    for doc in speed_cursor:
        movie_id = doc.get("movie_id")
        if not movie_id:
            continue
        speed_data[movie_id] = doc["average_rating"]

    alpha = 0.7
    trending = []
    for movie_id, rating in batch_data.items():
        if movie_id not in speed_data:
            continue
        avg_rating = speed_data[movie_id]
        merge_score = alpha * rating + (1 - alpha) * avg_rating

        movie_info = get_movie_info(movie_id)
        if not movie_info:
            continue

        trending.append({
            "movie_id": movie_id,
            "title": movie_info["title"],
            "genres": movie_info["genre"],
            "merge_score": merge_score
        })

    trending.sort(key=lambda x: x["merge_score"], reverse=True)
    print("DEBUG: Trending Results:", trending[:top_n])
    return {"trending_movies": trending[:top_n]}

# ---------- Endpoint: Pure Speed Scores Only (Top N) ------------
@app.get("/api/speed_only")
def get_speed_only(
    top_n: int = Query(10, description="Số lượng phim cần trả về"),
    window_hours: int = Query(1, description="Window length in hours", ge=0)
):
    one_window_ago = datetime.now() - timedelta(hours=window_hours)

    speed_cursor = speed_collection.find({"window.1": {"$gte": one_window_ago}})
    selected = {}
    movies = []
    for doc in speed_cursor:
        movie_id = doc.get("movie_id")
        avg_rating = doc.get("average_rating")
        movie_info = get_movie_info(movie_id)
        if not movie_info:
            continue
        if movie_id not in selected:
            selected[movie_id] = {
                "movie_id": movie_id,
                "title": movie_info["title"],
                "genres": movie_info["genre"],
                "average_rating": []
            }
        selected[movie_id]["average_rating"].append(avg_rating)
    for movie_id in selected:
        selected[movie_id]["average_rating"] = sum(selected[movie_id]["average_rating"]) / len(selected[movie_id]["average_rating"]) * 2
        movies.append(selected[movie_id])
        
    movies.sort(key=lambda x: x["average_rating"], reverse=True)
    return {
        "speed_only": movies[:top_n],
        "window_hours": window_hours
    }

@app.get("/health")
def health_check():
    return {"status": "Working fine!"}

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Run the application ----------
if __name__ == "__main__":
    import uvicorn
    df = pd.read_csv('movies.csv')
    records = df.to_dict(orient='records')

    # Kết nối đến MongoDB
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]  # Đặt tên database của bạn
    metadata_collection = db[MOVIES_COLLECTION]  # Collection nơi lưu thông tin phim

    # Xóa dữ liệu cũ (nếu bạn muốn làm mới dữ liệu)
    metadata_collection.delete_many({})

    new_records = []
    for record in records:
        new_record = {
            "movie_id": record["movie_id"],
            "title": record["title"],
            "genre": record["genres"].split("|"),
        }
        new_records.append(new_record)
    # Chèn các record vào MongoDB
    result = metadata_collection.insert_many(new_records)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)