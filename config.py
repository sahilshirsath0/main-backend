
import os
from pymongo import MongoClient

# MongoDB URI from Render Environment Variables
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Establish MongoDB Connection
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

# Define Database and Collections
DB_NAME = "sample_mflix"

db = client[DB_NAME]
collection = db["images"]
shops_collection = db["shops"]


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_TYPE = "filesystem"
    MONGO_URI = MONGO_URI


class DevelopmentConfig(Config):
    """Development configuration class."""

    DEBUG = True
