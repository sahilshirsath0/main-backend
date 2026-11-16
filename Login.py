from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token
from config import MONGO_URI
from pymongo import MongoClient
import datetime
import jwt  # PyJWT for token handling
import os
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token  # Google OAuth

app = Flask(__name__)

# ================================
#    CONFIGURATION & SETUP
# ================================

# MongoDB Connection
client = MongoClient(MONGO_URI)
DB_NAME = "sample_mflix"  # Ensure this is your   # Collection inside farmDB

db = client[DB_NAME]
users = db["users"]

# JWT Authentication Setup
JWT_SECRET = "f90219bf3d19946da006dcfd21873ebc7ebec3015a829de6d63658286b639008"  # Replace with a secure key
app.config["JWT_SECRET_KEY"] = JWT_SECRET

# Email Setup (SMTP Gmail Configuration)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "gslv3126@gmail.com"  # Change this
app.config["MAIL_PASSWORD"] = "doum jrkn tmdw hwty"  # Change this

# Google OAuth Client ID
GOOGLE_CLIENT_ID = "564836411990-f4mmim1rievspf4sssh2kvfomn0ge3c3.apps.googleusercontent.com"

# Secret for Password Reset Token
RESET_SECRET = "6b2d98285d9c9c9277f8f04e92125a9b90e6fcc0ef2647936ba5c65488e9b557"

bcrypt = Bcrypt(app)
jwt_manager = JWTManager(app)
mail = Mail(app)

# ================================
#        USER AUTH ROUTES
# ================================

# **USER SIGNUP**
@app.route("/users/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username, email, password = data.get("name"), data.get("email"), data.get("password")

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


# **USER LOGIN**
@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    user = users.find_one({"email": email})

    if not user or not user.get("password") or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=email, expires_delta=datetime.timedelta(days=1))
    users.update_one({"email": email}, {"$set": {"last_active": datetime.datetime.utcnow().isoformat()}})
    return jsonify({"token": token, "username": user["name"]})


# ================================
#        GOOGLE LOGIN
# ================================
@app.route("/users/google-login", methods=["POST"])
def google_login():
    data = request.get_json()
    google_token = data.get("token")

    try:
        google_info = id_token.verify_oauth2_token(google_token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = google_info["email"]
        name = google_info.get("name", "Google User")

        user = users.find_one({"email": email})
        if not user:
            users.insert_one({"name": name, "email": email, "password": None, "last_active": datetime.datetime.utcnow().isoformat()})

        token = create_access_token(identity=email, expires_delta=datetime.timedelta(days=1))
        return jsonify({"token": token, "username": name})

    except ValueError:
        return jsonify({"message": "Invalid Google token"}), 400


# ================================
#     FORGOT PASSWORD & RESET
# ================================
@app.route("/users/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")
    user = users.find_one({"email": email})

    if not user or not user.get("password"):
        return jsonify({"message": "Email not found"}), 404

    reset_token = jwt.encode(
        {"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        RESET_SECRET,
        algorithm="HS256"
    )

    reset_link = f"http://localhost:3000/reset-password/{reset_token}"

    try:
        msg = Message("Password Reset Request", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = f"Click the link below to reset your password:\n{reset_link}\nThis link will expire in 1 hour."
        mail.send(msg)
        return jsonify({"message": "Password reset email sent!"})
    except Exception as e:
        return jsonify({"message": "Error sending email", "error": str(e)}), 500


@app.route("/users/reset-password/<token>", methods=["POST"])
def reset_password(token):
    try:
        data = jwt.decode(token, RESET_SECRET, algorithms=["HS256"])
        email = data["email"]

        new_password = request.get_json().get("password")
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

        users.update_one({"email": email}, {"$set": {"password": hashed_password}})
        return jsonify({"message": "Password updated successfully!"})
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Reset link expired!"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid reset link!"}), 400


# ================================
#        RUN FLASK APP
# ================================
if __name__ == "__main__":
    app.run(debug=True)
