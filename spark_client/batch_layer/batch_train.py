from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pymongo import MongoClient
import sys
from pyspark.sql.functions import col, rand, row_number, floor, when
from pyspark.sql.window import Window
from pyspark.sql.functions import explode, col, min as spark_min, max as spark_max, struct, collect_list
from pymongo import MongoClient
from pyspark.sql import functions as F


# 1. Tạo SparkSession
spark = SparkSession.builder \
    .appName("MovieRecommenderBatch") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/movies.recommendations") \
    .getOrCreate()

# 2. Đọc dữ liệu từ HDFS
ratings = spark.read.csv("hdfs://namenode:9000//movies/movie-data/ratings.csv", header=True, inferSchema=True)
movies = spark.read.csv("hdfs://namenode:9000//movies/movie-data/movies.csv", header=True, inferSchema=True)

# Lấy 10% dữ liệu ngẫu nhiên
ratings = ratings.sample(fraction=0.01, seed=42)
# ratings = ratings.orderBy(F.rand()).limit(1000)

# Hiển thị một số dòng dữ liệu đã lấy mẫu
ratings.show(10)
# Lấy số lượng bản ghi trong DataFrame
ratings_count = ratings.count()

# In ra số lượng bản ghi
print(f"Total number of records in ratings: {ratings_count}")

# Thêm cột random để trộn dữ liệu
ratings = ratings.withColumn("rand", rand())

# Đánh số thứ tự mỗi dòng theo từng user
windowSpec = Window.partitionBy("userId").orderBy("rand")
ratings = ratings.withColumn("row_num", row_number().over(windowSpec))

# Đếm số lượng rating của mỗi user
user_counts = ratings.groupBy("userId").count().withColumnRenamed("count", "total")

# Tính train_limit = floor(0.8 * total), nhưng nếu chỉ có 1 rating thì train_limit = 1
user_counts = user_counts.withColumn(
    "train_limit",
    when(col("total") == 1, 1).otherwise(floor(col("total") * 0.8))
)

# Gộp lại với ratings
ratings = ratings.join(user_counts, on="userId", how="inner")

# Chia train/test
train_df = ratings.filter(col("row_num") <= col("train_limit")).drop("rand", "row_num", "total", "train_limit")
test_df  = ratings.filter((col("row_num") > col("train_limit")) & (col("total") > 1)).drop("rand", "row_num", "total", "train_limit")
print(f'tessssssss: {test_df.count()}')

# === 4. Huấn luyện mô hình ALS
als = ALS(
    userCol="userId",
    itemCol="movieId",
    ratingCol="rating",
    coldStartStrategy="drop",
    nonnegative=True,
    maxIter=10,
    regParam=0.1
)

model = als.fit(train_df)

# === 5. Dự đoán trên tập test
predictions = model.transform(test_df)
predictions_valid = predictions.filter(predictions.prediction.isNotNull())

# === 6. Đánh giá mô hình
evaluator = RegressionEvaluator(
    metricName="rmse",
    labelCol="rating",
    predictionCol="prediction"
)
if predictions.count() == 0:
    print("⚠️ Không có dòng nào trong predictions! Không thể đánh giá.")
    print(f"test df count: test_df.count()")
    sys.exit(1)
else:
    rmse = evaluator.evaluate(predictions)
    print(f"✅ RMSE: {rmse}")
    print(f"Root-mean-square error = {rmse:.4f}")

    # 1. Lấy top 5 gợi ý cho mỗi user
    recommendations = model.recommendForAllUsers(5)

    # 2. Explode để tách từng gợi ý ra thành hàng riêng
    exploded = recommendations.withColumn("rec", explode("recommendations")) \
        .select("userId", col("rec.movieId").alias("movieId"), col("rec.rating").alias("rating"))

    # 3. Tính min-max rating
    rating_stats = exploded.agg(
        spark_min("rating").alias("min_rating"),
        spark_max("rating").alias("max_rating")
    ).collect()

    min_rating = rating_stats[0]["min_rating"]
    max_rating = rating_stats[0]["max_rating"]
    # 4. Thêm cột scaled_rating
    scaled = exploded.withColumn(
        "scaled_rating",
        ((col("rating") - min_rating) / (max_rating - min_rating)) * 10
    )

    # 5. Gom lại thành recommendations array giống ban đầu
    repacked = scaled.select("userId", "movieId", "scaled_rating", "rating") \
        .withColumn("rec", struct(col("movieId"), col("rating"), col("scaled_rating"))) \
        .groupBy("userId") \
        .agg(collect_list("rec").alias("recommendations"))

    # 6. Chuyển sang Pandas để lưu vào MongoDB
    user_recs_pd = repacked.toPandas()

    # 7. Chuyển thành dict (giữ movie_id và rating đã được scale)
    def convert_recs(row):
        return {
            "user_id": int(row['userId']),
            "recommendations": [{"movie_id": int(r.movieId), "rating": round(float(r.scaled_rating), 3), "ori_rating": round(float(r.rating), 3)} for r in row['recommendations']]
        }

    records = [convert_recs(row) for _, row in user_recs_pd.iterrows()]

    # 8. Kết nối MongoDB và lưu
    client = MongoClient("mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=myReplicaSet")
    db = client["movies"]
    collection = db["user_recommendations"]

    collection.delete_many({})
    collection.insert_many(records)

    print("✅ Đã chuẩn hoá rating và lưu gợi ý xuống MongoDB!")

    spark.stop()