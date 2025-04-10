FROM jupyter/pyspark-notebook:spark-3.5.0

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# EXPOSE 8888

# CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
