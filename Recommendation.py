import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.models as models
import joblib
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import io
from flask import Flask, request, jsonify
from PIL import Image
import os

# Load the trained model
MODEL_PATH = "crop_disease_model.pth"
CLASS_PATH = "classes.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
class_names = torch.load(CLASS_PATH)

model = models.resnet18(pretrained=False)  # Must match your trained model architecture
model.fc = nn.Linear(model.fc.in_features, len(class_names))  # Adjust for output classes
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model = model.to(DEVICE)
model.eval()

# Define image transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


app = Flask(__name__)

# Enable CORS (Optional: If integrating with frontend)
from flask_cors import CORS
CORS(app)


# Load Encoders and Scaler for Fertilizer Model
encoders = joblib.load("encoders.pkl")
scaler = joblib.load("scaler.pkl")

class FertilizerModel(nn.Module):
    def __init__(self):
        super(FertilizerModel, self).__init__()
        self.fc1 = nn.Linear(8, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 5)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Load Fertilizer Model
fertilizer_model = FertilizerModel()
fertilizer_model.load_state_dict(torch.load("fertilizer_model.pt", map_location=torch.device('cpu')))
fertilizer_model.eval()

@app.route('/predict_fertilizer', methods=['POST'])
def predict_fertilizer():
    try:
        data = request.json

        # Validate Input
        required_fields = ["Soil Type", "Crop Type", "Temperature", "Humidity", "Moisture", "Nitrogen", "Phosphorus", "Potassium"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Encode Soil Type and Crop Type
        soil_type_encoded = encoders["Soil Type"].transform([data["Soil Type"]])[0]
        crop_type_encoded = encoders["Crop Type"].transform([data["Crop Type"]])[0]

        # Normalize Numerical Features
        numerical_features = np.array([[data["Temperature"], data["Humidity"], data["Moisture"],
                                        data["Nitrogen"], data["Phosphorus"], data["Potassium"]]])
        numerical_features = scaler.transform(numerical_features)[0]

        # Prepare Input Array (Ensure Correct Order)
        model_input = np.array([soil_type_encoded, crop_type_encoded] + list(numerical_features)).reshape(1, -1)
        model_input_tensor = torch.tensor(model_input, dtype=torch.float32)

        # Make Prediction
        with torch.no_grad():
            output = fertilizer_model(model_input_tensor)
            predicted_class = torch.argmax(output).item()

        # Decode Prediction
        predicted_fertilizer = encoders["Fertilizer_Name"].inverse_transform([predicted_class])[0]

        return jsonify({"fertilizer": predicted_fertilizer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Get the uploaded file
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        
        # Convert image to correct format
        image = Image.open(file).convert("RGB")
        image = transform(image).unsqueeze(0).to(DEVICE)  # Add batch dimension

        # Make prediction
        with torch.no_grad():
            outputs = model(image)
            _, predicted = torch.max(outputs, 1)
            disease_name = class_names[predicted.item()]

        return jsonify({"disease": disease_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

