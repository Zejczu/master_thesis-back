from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection URI
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the environment variables.")

# Create a MongoDB client
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# Access the DB
db = client['MasterThesis']
