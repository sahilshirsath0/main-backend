import torch
import torch.nn as nn
import joblib
import numpy as np
from flask import Blueprint, request, jsonify

# Blueprint Setup
fertilizer_bp = Blueprint("fertilizer", __name__)

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

@fertilizer_bp.route('/predict_fertilizer', methods=['POST'])
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
