import pickle
import os
import re
import string
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API Scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 1️⃣ Authenticate & Connect to Gmail API
def authenticate_gmail():
    creds = None
    TOKEN_PATH = "credentials/token.json"  # Stores OAuth token

    # Load saved credentials
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid credentials, authenticate user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials/credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save credentials
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# 2️⃣ Fetch Emails from Inbox
def fetch_emails(service, max_results=9):
    """Fetch recent emails from Gmail."""
    result = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        email_snippet = msg_data.get("snippet", "")
        emails.append(email_snippet)

    return emails

# 3️⃣ Load Spam Classifier Model
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Moves up one directory
MODEL_PATH = os.path.join(BASE_DIR, "models", "spam_classifier.pkl")

if not os.path.exists(MODEL_PATH):
    print(f"❌ Model file not found at: {MODEL_PATH}. Please train the model first.")
    exit(1)

with open(MODEL_PATH, "rb") as model_file:
    pipeline = pickle.load(model_file)

# 4️⃣ Preprocessing Function
def preprocess_text(text):
    """Clean email text before classification."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\d+", "", text)  # Remove numbers
    text = text.translate(str.maketrans("", "", string.punctuation))  # Remove punctuation
    text = text.strip()
    return text

# 5️⃣ Classify Email
def classify_email(email_text):
    """Classify fetched Gmail emails as Spam or Not Spam."""
    email_text = preprocess_text(email_text)
    if not email_text:
        return "Not Spam (Empty Email)"

    prediction = pipeline.predict([email_text])
    return "Spam" if prediction[0] == 1 else "Not Spam"

# 6️⃣ Save Not Spam Emails to JSON
def save_not_spam_emails(not_spam_emails):
    """Save Not Spam emails to JSON file inside scripts/data/."""
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(DATA_DIR, exist_ok=True)  # Ensure directory exists

    FILE_PATH = os.path.join(DATA_DIR, "not_spam_emails.json")

    with open(FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(not_spam_emails, file, indent=4, ensure_ascii=False)

    print(f"\n✅ Not Spam emails saved to: {FILE_PATH}")

# 7️⃣ Main Function
if __name__ == "__main__":
    service = authenticate_gmail()
    fetched_emails = fetch_emails(service)

    not_spam_emails = []

    print("\n📬 *Fetched Emails & Classification*:")
    for email in fetched_emails:
        classification = classify_email(email)
        print(f"\n📩 Email: {email}")
        print(f"📝 Prediction: {classification}")

        if classification == "Not Spam":
            not_spam_emails.append(email)  # Store Not Spam emails

    # Save Not Spam emails to JSON
    save_not_spam_emails(not_spam_emails)