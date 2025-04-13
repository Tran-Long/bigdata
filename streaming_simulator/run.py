import copy
import json
import time
from kafka import KafkaProducer
import pandas as pd
from tqdm import tqdm
import random
import datetime

producer = KafkaProducer(bootstrap_servers=['localhost:9091', 'localhost:9092'])
df = pd.read_csv("streaming_ratings.csv")
data = df.to_dict(orient='records')
random.seed(42)
random.shuffle(data)
i = 0
while True:
    # time.sleep(1)
    data_to_send = copy.deepcopy(data[i%len(data)])
    current_datetime = datetime.datetime.now()
    # Transform datetime to timestamp in long format
    timestamp = int(current_datetime.timestamp() * 1000)
    data_to_send["timestamp"] = timestamp
    producer.send('user_interactions', json.dumps(data_to_send).encode('utf-8'))
    i += 1
    if i % 50 == 0:
        print(f"Sent {i} messages")
        time.sleep(5)
        break
    producer.flush()
producer.close()