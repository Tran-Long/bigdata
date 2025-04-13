import os
from pyspark.sql import SparkSession

SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")

def main():
    spark = SparkSession.builder \
        .appName("INIT") \
        .master(SPARK_MASTER) \
        .config("spark.cores.max", "1") \
        .config("spark.executor.memory", "1G") \
        .config("spark.executor.cores", "1") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()

    df = spark.read.parquet("/app/ratings.parquet")
    df.write.mode("overwrite").parquet("hdfs://namenode:9000/movies_recommendation/history_data")
    spark.stop()

if __name__ == "__main__":
    main()
