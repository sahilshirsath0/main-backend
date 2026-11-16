from flask import Blueprint, request, jsonify
from config import MONGO_URI  # Ensure MONGO_URI is correctly set in config.py
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["sample_mflix"]  # Replace with your actual database name
users_collection = db["users"]  # Collection name for users

users_routes = Blueprint("users_routes", __name__)

# 🔹 Get all users
@users_routes.route("/users", methods=["GET"])
def get_users():
    try:
        page = int(request.args.get("page", 1))  # Default page 1
        per_page = 10  # Load 10 users per request for infinite scrolling

        # Apply skip and limit to paginate users
        users = list(users_collection.find({}, {"_id": 0})
                     .skip((page - 1) * per_page)
                     .limit(per_page))

        return jsonify({
            "users": users,
            "has_more": len(users) == per_page  # If less than 10, no more pages
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 Add or Login a User (Automatically Adds if Not Exists)
@users_routes.route("/users/login", methods=["POST"])
def login_user():
    data = request.json

    if "email" not in data:
        return jsonify({"error": "Email is required"}), 400

    email = data["email"]
    user = users_collection.find_one({"email": email})

    if user:
        # Update last active timestamp
        users_collection.update_one(
            {"email": email},
            {"$set": {"last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M")}}
        )
        return jsonify({
            "message": "Login successful",
            "username": user["username"],
            "last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        }), 200
    else:
        # Create a new user
        if "username" not in data:
            return jsonify({"error": "Username is required for first-time login"}), 400

        new_user = {
            "username": data["username"],
            "email": email,
            "last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "date_logged_in": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        }
        users_collection.insert_one(new_user)

        return jsonify({
            "message": "New user added successfully",
            "username": new_user["username"],
            "last_active": new_user["last_active"]
        }), 201

# 🔹 Delete a user
@users_routes.route("/users/delete", methods=["POST"])
def delete_users():
    try:
        data = request.get_json()
        emails_to_delete = data.get("emails", [])

        if not emails_to_delete:
            return jsonify({"error": "No emails provided"}), 400

        users_collection.delete_many({"email": {"$in": emails_to_delete}})
        return jsonify({"message": "Users deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

