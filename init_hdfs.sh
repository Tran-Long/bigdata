#!/bin/bash

# Wait for HDFS to exit safe mode
hdfs dfsadmin -safemode wait

# Create target directory in HDFS if it doesn't exist
hdfs dfs -mkdir -p /movies_recommendation/history_data

# Upload the Parquet file to HDFS
hdfs dfs -put -f /app/ratings.parquet /movies_recommendation/history_data

echo "Parquet file uploaded to HDFS successfully."