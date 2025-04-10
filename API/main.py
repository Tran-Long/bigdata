from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

app = FastAPI(title="Movie Recommendation")

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["movie_recommendation"]

# -----------------------------
# Các model dữ liệu
# -----------------------------
class Movie(BaseModel):
    movie_id: int
    title: str
    genre: List[str]
    score_batch: float
    score_speed: float

class UserProfile(BaseModel):
    user_id: int
    preferred_genres: List[str]

# -----------------------------
# Hàm chuẩn hóa với min-max normalization
# -----------------------------
def normalize_score(score: float, min_val: float, max_val: float) -> float:
    if max_val - min_val == 0:
        return 10
    return ((score - min_val) / (max_val - min_val)) * 10

# -----------------------------
# Hàm tính similarity
# -----------------------------
def genre_similarity(movie_genres: List[str], user_preferred: List[str]) -> float:
    if not movie_genres:
        return 0.0
    match_count = sum(1 for genre in movie_genres if genre in user_preferred)
    return match_count / len(movie_genres)

# -----------------------------
# Tính điểm cuối cùng
# -----------------------------
def calculate_final_score(score_batch: float, score_speed: float, similarity: float, alpha: float = 0.7) -> float:
    min_batch, max_batch = 5, 9
    min_speed, max_speed = 3, 10

    batch_norm = normalize_score(score_batch, min_batch, max_batch)
    speed_norm = normalize_score(score_speed, min_speed, max_speed)

    merge_score = alpha * batch_norm + (1 - alpha) * speed_norm
    final_score = merge_score * (1 + similarity)
    return final_score

# -----------------------------
# API: Gợi ý phim
# -----------------------------
@app.get("/api/user/{user_id}/recommendations")
def get_recommendations(user_id: int, top_n: int = Query(10)):
    user_profile = db.user_profiles.find_one({"user_id": user_id})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    batch_data = list(db.batch_scores.find())
    speed_data = {doc["movie_id"]: doc["score"] for doc in db.speed_scores.find()}

    alpha = 0.7
    recommendations = []

    for movie in batch_data:
        movie_id = movie["movie_id"]
        speed_score = speed_data.get(movie_id)
        if speed_score is None:
            continue

        similarity = genre_similarity(movie["genre"], user_profile["preferred_genres"])
        final_score = calculate_final_score(movie["score"], speed_score, similarity, alpha)
        merge_score_raw = alpha * movie["score"] + (1 - alpha) * speed_score

        recommendations.append({
            "movie_id": movie_id,
            "title": movie["title"],
            "genres": movie["genre"],
            "batch_score": movie["score"],
            "speed_score": speed_score,
            "final_score": final_score,
            "merge_score": merge_score_raw,
            "similarity": similarity
        })

    recommendations = sorted(recommendations, key=lambda x: x["final_score"], reverse=True)
    return {
        "user_id": user_id,
        "preferred_genres": user_profile["preferred_genres"],
        "recommendations": recommendations[:top_n]
    }

# -----------------------------
# API: Trending phim
# -----------------------------
@app.get("/api/trending/movies")
def get_trending_movies(top_n: int = Query(10)):
    batch_data = list(db.batch_scores.find())
    speed_data = {doc["movie_id"]: doc["score"] for doc in db.speed_scores.find()}

    alpha = 0.7
    trending = []

    for movie in batch_data:
        movie_id = movie["movie_id"]
        speed_score = speed_data.get(movie_id)
        if speed_score is None:
            continue

        merge_score = alpha * movie["score"] + (1 - alpha) * speed_score
        trending.append({
            "movie_id": movie_id,
            "title": movie["title"],
            "genres": movie["genre"],
            "merge_score": merge_score
        })

    trending = sorted(trending, key=lambda x: x["merge_score"], reverse=True)
    return {"trending_movies": trending[:top_n]}

# -----------------------------
# Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Chạy local nếu cần
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)