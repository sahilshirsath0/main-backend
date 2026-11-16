from flask import Blueprint, request, jsonify
from config import shops_collection  # Ensure MongoDB connection is set up
from flask import Blueprint, send_from_directory, jsonify
import os
import urllib.parse

shops_bp = Blueprint("shops", __name__)  # ✅ Updated Blueprint name

@shops_bp.route("/nearby", methods=["GET"])
def get_nearby_shops():
    try:
        limit = int(request.args.get("limit", 5))  # Default limit is 5
        skip = int(request.args.get("skip", 0))    # Default skip is 0

        # Fetch shops from MongoDB
        shops_cursor = shops_collection.find({}, {"_id": 0}).skip(skip).limit(limit)
        shops = list(shops_cursor)

        return jsonify({"success": True, "data": shops})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

UPLOAD_FOLDER = "uploads"  # Ensure this path is correct

@shops_bp.route('/api/shop_image/<path:filename>')
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
