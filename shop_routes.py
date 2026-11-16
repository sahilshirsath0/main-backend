import os
import urllib.parse
from flask import Blueprint, request, jsonify, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import client
from flask_cors import CORS  

# Initialize Blueprint
shop_bp = Blueprint("shop", __name__)
CORS(shop_bp)  

# MongoDB Connection
db = client["sample_mflix"]
shops_collection = db["shops"]

# Image Upload Folder
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "shop_image")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Convert MongoDB document to JSON-friendly format
def serialize_shop(shop):
    """Serialize shop data and attach valid image URLs."""
    shop["_id"] = str(shop["_id"])
    shop_name = shop.get("shop_name", "Unknown Shop")
    
    image_filename = shop.get("shop_image", "").strip().replace(" ", "_")
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)

    # Debugging Information
    print(f"\n🔍 Processing Shop: {shop_name}")
    print(f"   📂 Stored Image Filename: {shop.get('shop_image', '')}")
    print(f"   🔄 Converted Filename: {image_filename}")
    print(f"   📍 Expected Image Path: {image_path}")

    if image_filename and os.path.isfile(image_path):
        print(f"✅ Image found: {image_path}")
        shop["shop_image"] = f"/shop_image/{image_filename}"
    else:
        print(f"❌ Warning: Image NOT FOUND for '{shop_name}'!")
        shop["shop_image"] = None

    return shop

# Route to get all shops
@shop_bp.route("/shop", methods=["GET"])
def get_shops():
    try:
        print("\n🔍 Fetching all shops from the database...")
        shops = list(shops_collection.find())
        print(f"✅ Total shops fetched: {len(shops)}")

        serialized_shops = [serialize_shop(shop) for shop in shops]

        print("📦 Sending shop data to frontend...")
        return jsonify(serialized_shops), 200

    except Exception as e:
        print("❌ Error fetching shops:", e)
        return jsonify({"error": str(e)}), 500

# Route to delete a shop by ID
@shop_bp.route("/shop/<shop_id>", methods=["DELETE"])
def delete_shop(shop_id):
    try:
        print(f"\n🗑️ Attempting to delete shop with ID: {shop_id}")
        result = shops_collection.delete_one({"_id": ObjectId(shop_id)})

        if result.deleted_count == 1:
            print(f"✅ Shop with ID {shop_id} deleted successfully.")
            return jsonify({"message": "Shop deleted successfully"}), 200
        else:
            print(f"⚠️ Shop with ID {shop_id} not found.")
            return jsonify({"error": "Shop not found"}), 404
    except Exception as e:
        print("❌ Error deleting shop:", e)
        return jsonify({"error": str(e)}), 500

# Route to serve images from 'shop_image' folder
@shop_bp.route('/shop_image/<path:filename>')
def get_shop_image(filename):
    decoded_filename = urllib.parse.unquote(filename).replace(" ", "_")
    image_path = os.path.join(UPLOAD_FOLDER, decoded_filename)

    print(f"\n📸 Image Request Received: {filename}")
    print(f"   🔄 Decoded Filename: {decoded_filename}")
    print(f"   📍 Full Image Path: {image_path}")

    if os.path.isfile(image_path):
        print(f"✅ Image found. Serving {decoded_filename}.")
        return send_from_directory(UPLOAD_FOLDER, decoded_filename)
    else:
        print(f"❌ Image NOT FOUND: {decoded_filename}. Returning 404.")
        return jsonify({"error": "Image not found"}), 404
    
@shop_bp.route("/update_shop", methods=["PUT"])
def update_shop():
    try:
        print("🛠️ Received request to update shop...")

        # Ensure request data is JSON
        data = request.get_json()
        if not data:
            print("❌ Error: No JSON data received")
            return jsonify({"error": "Request must be JSON"}), 400

        print("📩 Request Data:", data)

        # Extract required fields
        shop_id = data.get("shop_id")  # ✅ Use shop_id to match frontend
        shop_name = data.get("shop_name")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        rating = data.get("rating")
        address = data.get("address")
        contact_number = data.get("contact_number")
        opening_time = data.get("opening_time")
        closing_time = data.get("closing_time")
        items_available = data.get("items_available")

        print(f"🔍 Extracted -> shop_id: {shop_id}, shop_name: {shop_name}")

        # Validate shop_id
        if not shop_id:
            print("❌ Error: Shop ID is missing")
            return jsonify({"error": "Shop ID is required"}), 400

        update_data = {}

        # Add only the provided fields to update
        if shop_name:
            update_data["shop_name"] = shop_name
        if latitude:
            update_data["latitude"] = latitude
        if longitude:
            update_data["longitude"] = longitude
        if rating:
            update_data["rating"] = rating
        if address:
            update_data["address"] = address
        if contact_number:
            update_data["contact_number"] = contact_number
        if opening_time:
            update_data["opening_time"] = opening_time
        if closing_time:
            update_data["closing_time"] = closing_time
        if items_available:
            update_data["items_available"] = items_available

        print(f"🔄 Updating shop with data: {update_data}")

        # Perform database update
        result = shops_collection.update_one({"_id": ObjectId(shop_id)}, {"$set": update_data})

        if result.matched_count == 0:
            print("❌ Error: No shop found with the given ID")
            return jsonify({"error": "No shop found with the given ID"}), 404

        print("✅ Database update result:", result.raw_result)

        return jsonify({"message": "✅ Shop updated successfully!", "updated_fields": update_data}), 200

    except Exception as e:
        print(f"🔥 Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@shop_bp.route('/shops/add', methods=['POST'])
def add_shop():
    try:
        print("DEBUG: Received request to add shop")  # Debugging log

        data = request.form
        print(f"DEBUG: Form data received: {data}")  # Log form data

        image = request.files.get('image')
        image_filename = ""

        if image:
            image_filename = image.filename
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image.save(image_path)
            print(f"DEBUG: Image saved as {image_filename}")  # Log image path

        shop_data = {
            "shop_name": data.get("name"),
            "shop_image": image_filename,  # Store only filename
            "items_available": [item.strip() for item in data.get("items_available", "").split(",")],  # Convert to list
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "rating": int(data.get("rating")),
            "address": data.get("address"),
            "contact_number": data.get("contact"),
            "opening_time": data.get("opening_time"),
            "closing_time": data.get("closing_time")
        }

        print(f"DEBUG: Shop data to be inserted: {shop_data}")  # Log final data before inserting

        shops_collection.insert_one(shop_data)
        print("DEBUG: Shop successfully added to MongoDB")  # Confirm insertion

        return jsonify({"message": "Shop added successfully!"}), 201

    except Exception as e:
        print(f"ERROR: {str(e)}")  # Log error messages
        return jsonify({"error": str(e)}), 500

