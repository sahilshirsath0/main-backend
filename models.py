# models.py
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(current_app.config['MONGO_URI'])
db = client.get_database()

# User Collection
users_collection = db.users

class User:
    def __init__(self, email, password, username=None):
        self.email = email
        self.password = password
        self.username = username

    def save(self):
        """Save the user to the database"""
        hashed_password = generate_password_hash(self.password)
        user_data = {
            "email": self.email,
            "password": hashed_password,
            "username": self.username
        }
        result = users_collection.insert_one(user_data)
        return result.inserted_id

    @classmethod
    def find_by_email(cls, email):
        """Find a user by email"""
        user_data = users_collection.find_one({"email": email})
        if user_data:
            return cls(user_data["email"], user_data["password"], user_data["username"])
        return None

    def verify_password(self, password):
        """Verify if the given password matches the hashed password"""
        return check_password_hash(self.password, password)
