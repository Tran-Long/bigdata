#!/bin/bash

# Define the master URL
: "${SPARK_MASTER:?Error: SPARK_MASTER is not set. Please set it before running the script.}"

TOTAL_CORE_PER_SPARK_TASK="${TOTAL_CORE_PER_SPARK_TASK:-4}"
MEM_PER_SPARK_TASK="${MEM_PER_SPARK_TASK:-4G}"
CORE_PER_SPARK_TASK="${CORE_PER_SPARK_TASK:-2}"


# Loop through all Python files in the /opt/spark-apps directory
scripts=(./jobs/*.py)
num_scripts=${#scripts[@]}

spark-submit \
  --master "$SPARK_MASTER" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --total-executor-cores "$TOTAL_CORE_PER_SPARK_TASK" \
  --executor-cores "$CORE_PER_SPARK_TASK" \
  --executor-memory "$MEM_PER_SPARK_TASK" \
  ./jobs/init.py

for i in "${!scripts[@]}"; do
  script="${scripts[$i]}"
  # Skip if the script is init.py
  if [[ "$script" == *"init.py"* ]]; then
    continue
  fi 
  echo "Submitting $script to Spark master at $SPARK_MASTER"
  spark-submit \
    --master "$SPARK_MASTER" \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    --total-executor-cores "$TOTAL_CORE_PER_SPARK_TASK" \
    --executor-cores "$CORE_PER_SPARK_TASK" \
    --executor-memory "$MEM_PER_SPARK_TASK" \
    "$script" &
done

# Wait for all background jobs to finish
# wait
