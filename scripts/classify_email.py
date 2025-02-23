import pickle
import re
import string

# 1️⃣ Load the Trained Model (Pipeline)
MODEL_PATH = "../models/spam_classifier.pkl"

try:
    with open(MODEL_PATH, "rb") as model_file:
        pipeline = pickle.load(model_file)  # This includes both vectorizer & classifier
    print("✅ Model loaded successfully.")
except FileNotFoundError:
    print(f"❌ Error: Model file not found at {MODEL_PATH}")
    exit()

# 2️⃣ Preprocessing Function (same as in training)
def preprocess_text(text):
    """Clean and preprocess email text."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = text.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation
    text = text.strip()
    return text

# 3️⃣ Function to Classify an Email
def classify_email(email_text):
    """Classify email as Spam or Not Spam."""
    email_text = preprocess_text(email_text)  # Clean text
    
    # Check if the email is empty after preprocessing
    if not email_text:
        return "Not Spam (Empty Email)"
    
    prediction = pipeline.predict([email_text])  # Predict using the trained model
    
    # Debugging: Print raw prediction value
    print(f"🔎 Raw Prediction: {prediction[0]}")  
    
    return "Spam" if prediction[0] == 1 else "Not Spam"

# 4️⃣ Example Usage
if __name__ == "__main__":
    test_emails = [
        "Congratulations! You have won a $1000 gift card. Click here to claim.",  # Likely Spam
        "Meeting scheduled at 3 PM. Please confirm your availability.",  # Not Spam
        "Hurry! Limited time offer on discount coupons.",  # Likely Spam
        "Hey John, can you send me the report?",  # Not Spam
        ""  # Edge case: Empty email
    ]

    for email in test_emails:
        print(f"\n📩 Email: {email}")
        print(f"📝 Prediction: {classify_email(email)}")
