import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, IntegerType, LongType

SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")

def main():
    # Initialize SparkSession with Kafka support
    spark = SparkSession.builder \
        .appName("SpeedLayerToHDFS") \
        .master(SPARK_MASTER) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()

    # Define the schema for incoming Kafka messages
    schema = StructType() \
        .add("user_id", IntegerType()) \
        .add("movie_id", IntegerType()) \
        .add("rating", IntegerType()) \
        .add("timestamp", LongType())  # expecting epoch milliseconds

    # Read streaming data from the Kafka topic 'user_events'
    kafkaDF = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka1:19091,kafka2:29092") \
        .option("subscribe", "user_events") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse the Kafka 'value' as JSON with the defined schema
    eventsDF = kafkaDF.select(from_json(col("value").cast("string"), schema).alias("event")).select("event.*")
    
    # Optionally, you could perform additional transformations, filtering, or windowed aggregations here.
    # For example, you can create a timestamp column if your Kafka messages include event time.
    
    # Write the micro-batch results into HDFS as Parquet files.
    # The output mode 'append' is used since data is streamed continuously.
    query = eventsDF.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", "hdfs://namenode:9000/spark/streaming-output") \
        .option("checkpointLocation", "hdfs://namenode:9000/spark/checkpoints") \
        .start()

    # Wait for the streaming query to finish
    query.awaitTermination()
    spark.stop()

if __name__ == "__main__":
    main()
