import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, count
from pyspark.sql.types import StructType, IntegerType, LongType, FloatType, TimestampType
import pymongo

SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")


def write_to_mongo(batch_df, batch_id):
    """
    For each micro-batch, convert the aggregated DataFrame to a Pandas DataFrame and upsert the results
    into MongoDB database 'movies_recommendation' and collection 'top_movie_in_one_hours'.
    """
    # Convert Spark DataFrame to Pandas DataFrame
    records = batch_df.toPandas().to_dict(orient="records")
    
    client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=myReplicaSet")
    db = client["movies_recommendation"]
    collection = db["top_movie_in_one_hours"]
    
    # Upsert each record based on the composite key (window start, window end, and movie_id)
    for record in records:
        # Assume the window field is a dictionary with "start" and "end" (formatted as strings)
        window_start = record["window"]["start"]
        window_end = record["window"]["end"]
        movie_id = record["movie_id"]
        
        query = {
            "window.start": window_start,
            "window.end": window_end,
            "movie_id": movie_id
        }
        update = {
            "$set": record
        }
        collection.update_one(query, update, upsert=True)
    
    client.close()

def main():
    spark = SparkSession.builder \
        .appName("SpeedLayer") \
        .master(SPARK_MASTER) \
        .config("spark.cores.max", "4") \
        .config("spark.executor.memory", "6G") \
        .config("spark.executor.cores", "2") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    # Define the schema for incoming Kafka events.
    schema = StructType() \
        .add("user_id", IntegerType()) \
        .add("movie_id", IntegerType()) \
        .add("rating", FloatType()) \
        .add("timestamp", LongType())  # epoch milliseconds

    kafkaDF = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka1:19091,kafka2:29092") \
        .option("subscribe", "user_interactions") \
        .option("startingOffsets", "latest") \
        .load()

    eventsDF = kafkaDF.select(from_json(col("value").cast("string"), schema).alias("event")).select("event.*")
    eventsDF = eventsDF.withColumn("event_time", (col("timestamp") / 1000).cast(TimestampType()))
    # Group events into 1-hour windows with a slide interval of 15 minutes.
    aggregatedDF = eventsDF.groupBy(
        window(col("event_time"), "30 minutes", "30 seconds"),
        col("movie_id")
    ).agg(
        count("*").alias("event_count"),      # Count of events
        avg(col("rating")).alias("average_rating")  # Average rating
    )

    # Write each micro-batch into MongoDB using foreachBatch.
    query = aggregatedDF.writeStream \
        .outputMode("update") \
        .foreachBatch(write_to_mongo) \
        .option("checkpointLocation", "hdfs://namenode:9000/spark/movies_recommendation/mongo_checkpoints") \
        .start()

    query.awaitTermination()
    spark.stop()

if __name__ == "__main__":
    main()
