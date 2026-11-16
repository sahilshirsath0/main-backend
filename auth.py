from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from pymongo import MongoClient
import datetime
import secrets
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from config import MONGO_URI

auth_bp = Blueprint("auth", __name__)

client = MongoClient(MONGO_URI)
DB_NAME = "sample_mflix"
db = client[DB_NAME]
users = db["users"]

bcrypt = Bcrypt()
jwt_manager = JWTManager()

GOOGLE_CLIENT_ID = "YOUR_EXISTING_GOOGLE_CLIENT_ID"


@auth_bp.route("/users/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    email = data.get("email", "").strip().lower()
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "Username, email and password are required"}), 400

    if users.find_one({"email": email}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    users.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
        "last_active": datetime.datetime.utcnow().isoformat()
    })

    return jsonify({"message": "Signup successful!"}), 201


@auth_bp.route("/users/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    email = data["email"].strip().lower()
    password = data["password"]
    user = users.find_one({"email": email})

    if (
        not user
        or not user.get("password")
        or not bcrypt.check_password_hash(user["password"], password)
    ):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(
        identity=email,
        expires_delta=datetime.timedelta(days=1)
    )

    users.update_one(
        {"email": email},
        {"$set": {"last_active": datetime.datetime.utcnow().isoformat()}}
    )

    return jsonify({
        "token": token,
        "username": user.get("username", user.get("name", "Unknown User"))
    }), 200


@auth_bp.route("/users/google-login", methods=["POST"])
def google_login():
    data = request.get_json(silent=True) or {}
    google_token = data.get("token")

    if not google_token:
        return jsonify({"message": "Google token is required"}), 400

    try:
        google_info = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = google_info["email"].strip().lower()
        name = google_info.get("name", "Google User")

        user = users.find_one({"email": email})

        if not user:
            users.insert_one({
                "username": name,
                "email": email,
                "password": None,
                "last_active": datetime.datetime.utcnow().isoformat()
            })

        token = create_access_token(
            identity=email,
            expires_delta=datetime.timedelta(days=1)
        )

        return jsonify({
            "token": token,
            "username": name,
            "email": email
        }), 200

    except ValueError:
        return jsonify({"message": "Invalid Google token"}), 400


@auth_bp.route("/users/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = users.find_one({"email": email})

    if not user or not user.get("password"):
        return jsonify({"message": "User not found or password reset unavailable"}), 404

    reset_code = str(secrets.randbelow(900000) + 100000)
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_code": reset_code,
                "reset_code_expires": expiry
            }
        }
    )

    return jsonify({
        "message": "Demo reset code generated",
        "reset_code": reset_code,
        "expires_in_minutes": 10
    }), 200


@auth_bp.route("/users/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    reset_code = data.get("reset_code", "").strip()
    new_password = data.get("password", "")

    if not email or not reset_code or not new_password:
        return jsonify({
            "message": "Email, reset code and new password are required"
        }), 400

    user = users.find_one({
        "email": email,
        "reset_code": reset_code,
        "reset_code_expires": {"$gt": datetime.datetime.utcnow()}
    })

    if not user:
        return jsonify({"message": "Invalid or expired reset code"}), 400

    hashed_password = bcrypt.generate_password_hash(
        new_password
    ).decode("utf-8")

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hashed_password},
            "$unset": {
                "reset_code": "",
                "reset_code_expires": ""
            }
        }
    )

    return jsonify({"message": "Password reset successful"}), 200
