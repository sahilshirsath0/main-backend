import os
from pymongo import MongoClient
from config import client
# MongoDB Configuration

db = client["sample_mflix"]
collection = db["images"]

# Folder containing images
IMAGE_FOLDER = "UploadImages"  # Change this to your folder path

# Ensure the folder exists
if not os.path.exists(IMAGE_FOLDER):
    print("Error: Image folder not found.")
    exit()

# Function to upload images
def bulk_upload():
    files = os.listdir(IMAGE_FOLDER)
    if not files:
        print("No images found in the folder.")
        return

    data_list = []
    for file in files:
        file_path = os.path.join(IMAGE_FOLDER, file)
        if os.path.isfile(file_path):
            data_list.append({
                "filename": file,
                "price": 100,  # Default price set to 0
                "image": file,
                "path": file_path
            })

    if data_list:
        collection.insert_many(data_list)
        print(f"Successfully uploaded {len(data_list)} images to MongoDB.")

# Run the bulk upload
if __name__ == "__main__":
    bulk_upload()
