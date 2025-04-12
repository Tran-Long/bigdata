#!/bin/bash

# In nội dung crontab để kiểm tra
echo "=== Cron jobs in /etc/cron.d ==="
cat /etc/cron.d/batch-cron

# Đảm bảo quyền file cron đúng
chmod 0644 /etc/cron.d/batch-cron
touch /app/logs/batch_train.log

# Khởi động cron trong foreground và log
cron && tail -f /app/logs/batch_train.log
