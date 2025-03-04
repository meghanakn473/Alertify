import os
import json
import re
import string
import firebase_admin
from firebase_admin import credentials, firestore
import subprocess
from twilio.rest import Client

# 🌟 Load Not Spam Emails
def load_emails(file_path):
    if not os.path.exists(file_path):
        print(f"❌ No Not Spam emails found at {file_path}. Exiting...")
        exit(1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            emails = json.load(file)
            if not emails:
                print("❌ No emails found in not_spam_emails.json. Exiting...")
                exit(1)
            return emails
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in not_spam_emails.json. Exiting...")
        exit(1)

def preprocess_text(text):
    """Cleans email text before keyword matching."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\d+", "", text)  # Remove numbers
    text = text.translate(str.maketrans("", "", string.punctuation))  # Remove punctuation
    return text.strip()

# Load Emails
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FILE_PATH = os.path.join(DATA_DIR, "not_spam_emails.json")
not_spam_emails = load_emails(FILE_PATH)
processed_emails = [preprocess_text(email) for email in not_spam_emails]

# 🌟 Firebase Setup
def initialize_firebase():
    cred_path = os.path.join(os.path.dirname(__file__), "credentials", "serviceAccountKey.json")
    if not os.path.exists(cred_path):
        print(f"❌ Firebase credentials file not found at {cred_path}. Exiting...")
        exit(1)
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        print("✅ Firebase connected successfully.")
        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        exit(1)

db_firestore = initialize_firebase()

# 🌟 Fetch User Keywords & Phone Numbers
def fetch_user_keywords():
    try:
        users_ref = db_firestore.collection("users")
        users_list = []
        for doc in users_ref.stream():
            user_info = doc.to_dict()
            if "phone_number" in user_info and "keywords" in user_info:
                users_list.append({
                    "phone_number": user_info["phone_number"],
                    "keywords": [preprocess_text(kw) for kw in user_info["keywords"]]
                })
        print(f"✅ {len(users_list)} users retrieved from Firestore.")
        return users_list if users_list else exit("❌ No user data available. Exiting...")
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        exit(1)

user_keywords_data = fetch_user_keywords()