import os
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from config import MONGO_URI  # MongoDB connection string
from flask_cors import CORS
from bson.objectid import ObjectId
from datetime import datetime
from bson import Binary
import io
from io import BytesIO
import base64
import re
from werkzeug.utils import secure_filename
from users_routes import users_routes
# from flask_jwt_extended import JWTManager
from flask_session import Session
from flask_pymongo import PyMongo
from auth import auth_bp 
from config import DevelopmentConfig
from shop_routes import shop_bp 
from auth import auth_bp  # Import the Blueprint
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://YOUR-FRONTEND.vercel.app"
        ]
    }
})
app.config.from_object(DevelopmentConfig)
from shops_api import shops_bp

# Database Setup
client = MongoClient(MONGO_URI)
DB_NAME = "sample_mflix"  # Ensure this is your correct database name
COLLECTION_NAME = "images"  # Collection inside farmDB
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

print("🚀 [SERVER STARTED] Flask App Running!")

# ----------------------------------------------------------------------
# 1️⃣ Add Product with Image Upload
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "UploadImages")

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure folder exists
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        name = request.form.get("name")
        price = request.form.get("price")
        out_of_stock = request.form.get("out_of_stock", "false").lower() == "true"
        image_file = request.files.get("image")

        if not name or not price or not image_file:
            return jsonify({"error": "Name, price, and image are required"}), 400

        if not allowed_file(image_file.filename):
            return jsonify({"error": "Invalid file format. Only PNG and JPG allowed."}), 400

        file_ext = image_file.filename.rsplit(".", 1)[1].lower()
        filename = f"{secure_filename(name)}.{file_ext}"

        upload_folder = UPLOAD_FOLDER

        file_path = os.path.join(upload_folder, filename)
        image_file.save(file_path)

        product = {
            "filename": filename,
            "price": float(price),
            "image": filename,
            "path": os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__))),
            "out_of_stock": out_of_stock
        }

        collection.insert_one(product)

        return jsonify({
            "message": f"Product '{filename}' added successfully!"
        }), 201

    except Exception as e:
        app.logger.exception("Error adding product")
        return jsonify({"error": str(e)}), 500

@app.route('/get_price/<filename>', methods=['GET'])
def get_price(filename):
    try:
        print(f"📡 [INFO] Fetching price for: {filename}")

        # Find the product by filename and retrieve only the price
        product = collection.find_one(
            {"filename": filename}, {"_id": 0, "price": 1}
        )

        if product:
            return jsonify(product["price"]), 200
        else:
            print(f"❌ [ERROR] Price not found for: {filename}")
            return jsonify({"error": "Price not found"}), 404

    except Exception as e:
        print(f"❌ [ERROR] Exception in /get_price: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------------------------
# 2️⃣ Retrieve All Products (with image data)
# ----------------------------------------------------------------------
@app.route('/get_all_products', methods=['GET'])
@app.route('/api/get_all_products', methods=['GET'])
def get_all_products():
    try:
        products = list(collection.find(
            {},
            {"_id": 1, "filename": 1, "image": 1, "path": 1, "price": 1, "out_of_stock": 1}
        ))

        for product in products:
            product["_id"] = str(product["_id"])
            product["image_url"] = (
    f"{request.host_url.rstrip('/')}/api/get_image/{product['filename']}"
)
        return jsonify(products), 200

    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return jsonify({"error": str(e)}), 500



# ----------------------------------------------------------------------
# 3️⃣ Serve Image by ID (Fetch from MongoDB)
# ----------------------------------------------------------------------

@app.route('/get_image/<path:filename>', methods=['GET'])
@app.route('/api/get_image/<path:filename>', methods=['GET'])
def get_image(filename):
    try:
        product = collection.find_one({"filename": filename})

        if not product:
            return jsonify({"error": "Image not found in MongoDB"}), 404

        stored_path = product.get("path")

        if not stored_path:
            return jsonify({"error": "Image path not found"}), 404

        # Handle Windows and Linux path separators
        stored_path = str(stored_path).replace("\\", "/")

        # All product images are stored in UploadImages
        image_filename = os.path.basename(stored_path)
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)

        if not os.path.isfile(image_path):
            return jsonify({
                "error": "Image file not found on server",
                "filename": filename,
                "stored_path": stored_path,
                "searched_path": image_path
            }), 404

        return send_file(image_path)

    except Exception:
        app.logger.exception("Error fetching image: %s", filename)
        return jsonify({"error": "Failed to fetch image"}), 500


# ----------------------------------------------------------------------
# 4️⃣ Delete Product by ID (with image removal from DB)
# ----------------------------------------------------------------------
@app.route('/delete_product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        # Delete product from database (no need to delete image from file system)
        collection.delete_one({"_id": ObjectId(product_id)})

        return jsonify({"message": "✅ Product deleted successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# 5️⃣ Update Product (including image update in DB)
# ----------------------------------------------------------------------
@app.route("/update_product", methods=["PUT"])
def update_product():
    try:
        # Debug: Log incoming request data
        print("Received request to update product")

        # Parse JSON body
        data = request.get_json()
        print("Request Data:", data)

        product_id = data.get("id")
        name = data.get("filename")
        price = data.get("price")
        image_file = request.files.get("image")  # Handle image file separately

        # Debug: Log the extracted values from the request
        print(f"Extracted product_id: {product_id}, name: {name}, price: {price}, image: {image_file}")

        # Check if product_id is present
        if not product_id:
            print("Error: Product ID is missing")
            return jsonify({"error": "Product ID is required"}), 400

        update_data = {}

        if name:
            update_data["filename"] = name
        if price:
            update_data["price"] = float(price)

        if image_file:
            # Debug: Log the image being uploaded
            print("Processing image upload...")

            # Fetch existing product
            product = collection.find_one({"_id": ObjectId(product_id)})

            if not product:
                print(f"Product with ID {product_id} not found!")
                return jsonify({"error": "Product not found"}), 404

            # Update image in MongoDB (save image as binary data)
            file_ext = image_file.filename.rsplit(".", 1)[1].lower()
            
            if not allowed_file(image_file.filename):
                return jsonify({"error": "Invalid image format"}), 400
            new_filename = f"{secure_filename(name or product['filename'].rsplit('.', 1)[0])}.{file_ext}"
            upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UploadImages")
            os.makedirs(upload_folder, exist_ok=True)
            new_path = os.path.join(upload_folder, new_filename)
            image_file.save(new_path)
            update_data["filename"] = new_filename
            update_data["image"] = new_filename
            update_data["path"] = os.path.relpath(
            new_path, os.path.dirname(os.path.abspath(__file__)))



        # Update the product in the database
        result = collection.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
        print("Database update result:", result)

        # Return success message
        return jsonify({"message": "✅ Product updated successfully!"}), 200

    except Exception as e:
        # Debug: Log any exceptions that occur during processing
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Initialize authentication and session


# Register blueprints

app.register_blueprint(users_routes)
# Register Blueprints
# Register Blueprints

app.register_blueprint(shop_bp, url_prefix="/api")
app.register_blueprint(shops_bp, url_prefix="/shop")

app.config["JWT_SECRET_KEY"] = ""

# Email Setup (SMTP Gmail Configuration)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = ""
app.config["MAIL_PASSWORD"] = ""

# Initialize extensions
bcrypt = Bcrypt(app)
jwt_manager = JWTManager(app)
mail = Mail(app)



# Register the authentication Blueprint
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)