#!/bin/bash

LOCK_FILE="/tmp/train_batch.lock"

if [ -f "$LOCK_FILE" ]; then
    echo "[`date`] 🚫 Đã có job khác đang chạy. Bỏ qua." >> /app/logs/cron_debug.log
    exit 0
fi

touch "$LOCK_FILE"
echo "[`date`] ✅ Bắt đầu training" >> /app/logs/cron_debug.log
# (2) Xuất biến môi trường nếu cần (ví dụ, conda hoặc venv)
export PYSPARK_PYTHON=/opt/conda/bin/python
export PYSPARK_DRIVER_PYTHON=/opt/conda/bin/python

# (3) Optional: thêm path pip packages nếu cần
# export PYTHONPATH="$PYTHONPATH:/opt/conda/lib/python3.11/dist-packages"

/usr/local/spark/bin/spark-submit   --master spark://spark-master:7077   --total-executor-cores 4   --executor-memory 2G   --executor-cores 2   /app/batch_layer/batch_train.py >> /app/logs/batch_train.log 2>&1

echo "[`date`] ✅ Xong training" >> /app/logs/cron_debug.log
rm -f "$LOCK_FILE"