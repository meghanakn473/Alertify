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


# 🌟 Twilio Setup
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")  # Twilio sandbox number
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def get_user_phone(user_id):
    """Fetch user phone number from Firestore."""
    user_ref = db_firestore.collection("users").document(user_id)
    user = user_ref.get()
    
    if user.exists:
        user_data = user.to_dict()
        phone = user_data.get("phone_number")  # ✅ Correct field name
        if phone:
            return f"whatsapp:+91{phone}"  # ✅ Add country code
    return None

def send_whatsapp_message(user_id, message):
    """Send a WhatsApp notification to the user."""
    phone_number = get_user_phone(user_id)
    if phone_number:
        response = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=phone_number
        )
        print(f"✅ Message sent to {phone_number}: {response.sid}")
    else:
        print(f"❌ No phone number found for user {user_id}")

# 🌟 Match Emails with Keywords & Notify Users
def process_and_notify():
    for user in user_keywords_data:
        user_phone = user["phone_number"]
        keywords = user["keywords"]
        
        if not keywords:
            print(f"⚠ No keywords for {user_phone}. Skipping...")
            continue
        
        match_found = False  # Flag to track if a match is found
        
        for email in processed_emails:
            if any(keyword in email for keyword in keywords):
                print(f"✅ Match found! Sending WhatsApp notification to {user_phone}...")
                try:
                    send_whatsapp_message(user_phone, f"📢 Match found in email: {email[:100]}")
                    match_found = True  # Set flag to True if match found
                except Exception as e:
                    print(f"❌ Failed to send WhatsApp notification: {e}")
                break  # Stop checking once a match is found
        
        if not match_found:
            print(f"⚠ No matching emails found for {user_phone}.")

# 🌟 Run Processing & Notification
process_and_notify()