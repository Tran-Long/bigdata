#!/bin/bash

LOCK_FILE="/tmp/train_batch.lock"

if [ -f "$LOCK_FILE" ]; then
    echo "[`date`] 🚫 Đã có job khác đang chạy. Bỏ qua." >> /app/logs/cron_debug.log
    exit 0
fi

# Check if logs directory exists, if not create it
if [ ! -d "/app/logs" ]; then
    mkdir -p /app/logs
fi
rm -rf /app/logs/*

touch "$LOCK_FILE"
echo "[`date`] ✅ Bắt đầu training" >> /app/logs/cron_debug.log

spark-submit \
     --master $SPARK_MASTER \
     --executor-memory 12G \
     --executor-cores 6 \
     /app/batch_layer/batch_train.py >> /app/logs/batch_train.log 2>&1

echo "[`date`] ✅ Xong training" >> /app/logs/cron_debug.log
rm -f "$LOCK_FILE"