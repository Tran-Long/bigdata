FROM python:3.8.10

WORKDIR /app

COPY . /app

RUN apt update
RUN apt install -y openjdk-11-jdk

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x ./submit_jobs.sh ./run.sh


# EXPOSE 8888

# CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
