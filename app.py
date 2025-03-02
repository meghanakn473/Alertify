from flask import Flask, request, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)

# Initialize Firebase
firebase_config_path = "config/alertify-firebase.json"
if os.path.exists(firebase_config_path):
    cred = credentials.Certificate(firebase_config_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully.")
else:
    print("❌ Firebase config file not found!")
    db = None

@app.route('/')
def index():
    return render_template("details.html")

@app.route('/submit', methods=['POST'])
def submit():
    try:
        if not request.form:
            return jsonify({"error": "No form data received"}), 400

        name = request.form.get("name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")  # Use this as Document ID
        keywords = request.form.get("keywords").split(",")  # Store as a list

        if not name or not email or not phone_number or not keywords:
            return jsonify({"error": "Missing required fields"}), 400

        # Store data with phone_number as the Document ID (Prevents duplication)
        db.collection("users").document(phone_number).set({
            "name": name,
            "email": email,
            "phone_number": phone_number,
            "keywords": [kw.strip() for kw in keywords]  # Save as a list, remove spaces
        })

        return jsonify({"message": "Data saved successfully!", "phone_number": phone_number}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "_main_":
    app.run(debug=True)