FROM jupyter/pyspark-notebook:spark-3.5.0

USER root
WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x ./submit_jobs.sh ./run.sh


# EXPOSE 8888

# CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
