FROM python:3.8.10

WORKDIR /app

COPY . /app

RUN apt update
RUN apt install -y openjdk-11-jdk
# Cài đặt cron
RUN apt-get update && apt-get install -y cron

RUN pip install --no-cache-dir -r requirements.txt



# Copy file crontab và script cron
COPY crontab.txt /etc/cron.d/batch-cron

# Đảm bảo script chạy được
RUN chmod +x /app/batch_layer/batch_train.sh

# Cấp quyền cho file cron và đăng ký nó
RUN chmod 0644 /etc/cron.d/batch-cron && \
    crontab /etc/cron.d/batch-cron

# # Đảm bảo file cron kết thúc bằng dòng trống
# RUN echo "" >> /etc/cron.d/batch-cron

# # Lệnh khởi động cron và giữ container sống
# CMD service cron start && tail -f /app/logs/batch_train.log

RUN chmod +x  ./start.sh

RUN chmod +x ./submit_jobs.sh ./run.sh



 

# EXPOSE 8888

# CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

