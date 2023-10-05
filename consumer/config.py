from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL=os.getenv("MONGODB_URL")

conn = MongoClient(MONGODB_URL)

# MongoDB setup
client = conn
db = client["user_db"]  # db name
users_collection = db["users"]
shipments_collection = db["Users_shipment"]
device_collection = db["device_data"]

