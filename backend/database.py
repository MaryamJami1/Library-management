from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)  # Connect to MongoDB
db = client["myLibraryDB"]  # Database Name
books_collection = db["books"]
users_collection = db["users"]  # ✅ New Users Collection
