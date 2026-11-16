from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from config import db  # Ensure this imports the correct MongoDB connection

app = Flask(__name__)

# Configuration
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

# Ensure the upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has a valid extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# ✅ Convert MongoDB Documents to JSON-Safe Format
def convert_mongo_document(doc):
    """Convert MongoDB document to JSON-safe format."""
    print(f"🔍 Before conversion: {doc}")  # Debugging
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
    print(f"✅ After conversion: {doc}")  # Debugging
    return doc

# ✅ Upload Image & Add Product
@app.route("/upload", methods=["POST"])
def upload_product():
    print("📥 Received request at /upload")  # Debugging

    if "image" not in request.files:
        print("❌ No image found in request")  # Debugging
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    name = request.form.get("name")
    type_ = request.form.get("type")
    price = request.form.get("price")

    if not name or not type_ or not price:
        print("❌ Missing product details")  # Debugging
        return jsonify({"error": "Missing product details"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        product_data = {
            "name": name,
            "image_path": file_path,
            "type": type_,
            "price": float(price),
        }

        print(f"📦 Inserting product: {product_data}")  # Debugging
        inserted_product = db.products.insert_one(product_data)

        # Convert `_id` to string to prevent JSON serialization error
        product_data["_id"] = str(inserted_product.inserted_id)

        response_data = {
            "message": "Product added successfully",
            "product_id": str(inserted_product.inserted_id),
            "data": product_data
        }

        print(f"✅ Response Data: {response_data}")  # Debugging
        return jsonify(response_data), 201

    print("❌ Invalid file format")  # Debugging
    return jsonify({"error": "Invalid file format"}), 400


# ✅ Get All Products
@app.route("/products", methods=["GET"])
def get_all_products():
    print("📥 Received request at /products")  # Debugging
    products = list(db.products.find())

    print(f"🔍 Raw MongoDB Data: {products}")  # Debugging
    products = [convert_mongo_document(product) for product in products]  # ✅ Convert _id

    print(f"✅ Processed Products Data: {products}")  # Debugging
    return jsonify(products), 200

# ✅ Get Single Product by Name
@app.route("/product/<name>", methods=["GET"])
def get_product_by_name(name):
    print(f"📥 Received request for product: {name}")  # Debugging
    product = db.products.find_one({"name": name})
    
    if product:
        print(f"🔍 Found Product: {product}")  # Debugging
        return jsonify(convert_mongo_document(product)), 200
    
    print("❌ Product not found")  # Debugging
    return jsonify({"error": "Product not found"}), 404

# ✅ Serve Image from Local Folder
@app.route("/images/<filename>")
def serve_image(filename):
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    if not os.path.exists(image_path):
        print("❌ Image not found")  # Debugging
        return jsonify({"error": "Image not found"}), 404

    print(f"📤 Serving Image: {filename}")  # Debugging
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ✅ Update Product Price
@app.route("/update_price/<name>", methods=["PUT"])
def update_product_price(name):
    print(f"📥 Received price update for: {name}")  # Debugging
    data = request.json
    new_price = data.get("price")

    if new_price is None:
        print("❌ Price not provided")  # Debugging
        return jsonify({"error": "Price not provided"}), 400

    updated = db.products.update_one({"name": name}, {"$set": {"price": float(new_price)}})
    
    if updated.matched_count == 0:
        print("❌ Product not found")  # Debugging
        return jsonify({"error": "Product not found"}), 404

    print(f"✅ Updated price of {name} to {new_price}")  # Debugging
    return jsonify({"message": f"Updated price of {name} to {new_price}"}), 200

# ✅ Delete Product
@app.route("/delete/<name>", methods=["DELETE"])
def delete_product(name):
    print(f"📥 Received delete request for: {name}")  # Debugging
    product = db.products.find_one({"name": name})
    
    if not product:
        print("❌ Product not found")  # Debugging
        return jsonify({"error": "Product not found"}), 404

    # Delete image file from storage
    image_path = product.get("image_path")
    if image_path and os.path.exists(image_path):
        os.remove(image_path)

    db.products.delete_one({"name": name})
    print(f"✅ Deleted product: {name}")  # Debugging
    return jsonify({"message": f"Deleted product: {name}"}), 200

if __name__ == "__main__":
    app.run(debug=True)
