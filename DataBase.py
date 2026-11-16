from flask import Flask, request, jsonify, send_file
from flask_pymongo import PyMongo
from gridfs import GridFS
from bson import ObjectId
import os

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/agri_shop"
mongo = PyMongo(app)
grid_fs = GridFS(mongo.db)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    file_id = grid_fs.put(file, filename=file.filename)
    mongo.db.images.insert_one({"file_id": file_id, "filename": file.filename})
    return jsonify({"message": "Image uploaded successfully", "file_id": str(file_id)})

@app.route("/images", methods=["GET"])
def get_images():
    images = list(mongo.db.images.find({}, {"_id": 0, "file_id": 1, "filename": 1}))
    return jsonify(images)

@app.route("/image/<file_id>", methods=["GET"])
def get_image(file_id):
    file = grid_fs.get(ObjectId(file_id))
    return send_file(file, mimetype="image/jpeg")

@app.route("/delete/<file_id>", methods=["DELETE"])
def delete_image(file_id):
    grid_fs.delete(ObjectId(file_id))
    mongo.db.images.delete_one({"file_id": ObjectId(file_id)})
    return jsonify({"message": "Image deleted successfully"})

@app.route("/search", methods=["GET"])
def search_images():
    query = request.args.get("name", "")
    images = list(mongo.db.images.find({"filename": {"$regex": query, "$options": "i"}}, {"_id": 0, "file_id": 1, "filename": 1}))
    return jsonify(images)

if __name__ == "__main__":
    app.run(debug=True)
