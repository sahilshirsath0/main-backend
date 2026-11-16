from pymongo import MongoClient
import os
# MongoDB URI
MONGO_URI = os.environ.get("MONGO_URI")

# Establish Connection
client = MongoClient(MONGO_URI)

# Define Database and Collection
DB_NAME = "sample_mflix"
db = client[DB_NAME]
collection = db["images"]
shops_collection = db["shops"]



class DevelopmentConfig(Config):
    """Development configuration class."""
    DEBUG = True
    MONGO_URI = "mongodb://localhost:27017/sample_mflix"  # Default MongoDB URI for local development
