#!/bin/bash

# Define the master URL
: "${SPARK_MASTER:?Error: SPARK_MASTER is not set. Please set it before running the script.}"
# Assign the environment variable to SPARK_MASTER_URL
SPARK_MASTER_URL="$SPARK_MASTER"

TOTAL_CORE_PER_SPARK_TASK="${TOTAL_CORE_PER_SPARK_TASK:-4}"
MEM_PER_SPARK_TASK="${MEM_PER_SPARK_TASK:-4G}"
CORE_PER_SPARK_TASK="${CORE_PER_SPARK_TASK:-2}"


# Loop through all Python files in the /opt/spark-apps directory
scripts=(./jobs/*.py)
num_scripts=${#scripts[@]}

for i in "${!scripts[@]}"; do
  script="${scripts[$i]}"
  echo "Submitting $script to Spark master at $SPARK_MASTER_URL"
  spark-submit \
    --master "$SPARK_MASTER_URL" \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    --total-executor-cores "$TOTAL_CORE_PER_SPARK_TASK" \
    --executor-cores "$CORE_PER_SPARK_TASK" \
    --executor-memory "$MEM_PER_SPARK_TASK" \
    "$script" &
  
  # Sleep only if this is not the last script
  if [ $i -lt $((num_scripts - 1)) ]; then
    sleep 60
  fi
done

# Wait for all background jobs to finish
# wait
