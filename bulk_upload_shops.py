import os
from pymongo import MongoClient
from config import client

# MongoDB Configuration
db = client["sample_mflix"]  # Change this to your actual database name
collection = db["shops"]  # Collection for shops

# Folder containing shop images
SHOP_IMAGE_FOLDER = "shop_image"  # Ensure this folder exists

# Ensure the folder exists
if not os.path.exists(SHOP_IMAGE_FOLDER):
    print("Error: Shop image folder not found.")
    exit()

# Function to upload shop images and data
def bulk_upload_shops():
    files = os.listdir(SHOP_IMAGE_FOLDER)
    if not files:
        print("No shop images found in the folder.")
        return

    data_list = []
    for file in files:
        file_path = os.path.join(SHOP_IMAGE_FOLDER, file)
        if os.path.isfile(file_path):
            shop_name = os.path.splitext(file)[0]  # Use filename as shop name
            
            shop_data = {
                "shop_name": shop_name,
                "shop_image": file,  # Store image filename
                "items_available": ["Fertilizer", "Pesticide"],  # Default items
                "latitude": 0.0,  # Placeholder, update later
                "longitude": 0.0,  # Placeholder, update later
                "rating": 5,
                "address": "Sample Address",
                "contact_number": "1234567890",
                "opening_time": "09:00 AM",
                "closing_time": "09:00 PM"
            }
            data_list.append(shop_data)

    if data_list:
        collection.insert_many(data_list)
        print(f"Successfully uploaded {len(data_list)} shop entries to MongoDB.")

# Run the bulk upload
if __name__ == "__main__":
    bulk_upload_shops()
