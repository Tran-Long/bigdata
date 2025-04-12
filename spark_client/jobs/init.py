import os
from pyspark.sql import SparkSession

SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")

def main():
    spark = SparkSession.builder \
        .appName("SpeedLayer") \
        .master(SPARK_MASTER) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()
    
    spark.stop()

if __name__ == "__main__":
    main()
