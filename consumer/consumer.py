from kafka import KafkaConsumer
import json
from pymongo import MongoClient
import os
from config import db, device_collection  
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

conn = MongoClient(MONGODB_URL)

bootstrap_servers =os.getenv("bootstrap_servers")  

topic_name=os.getenv("topic_name")

consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),  
    api_version=(0, 11, 5)
)

for message in consumer:
    try:
        for data_dict in message.value:
            if isinstance(data_dict, dict):
                device_collection.insert_one(data_dict)
                print("Inserted:", data_dict)
            else:
                print("Invalid data format:", data_dict)
    except Exception as e:
        print("Error during insertion:", e)
