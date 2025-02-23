import os
import base64
import json
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd

# Define Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Paths
CREDENTIALS_PATH = "credentials/credentials.json"
TOKEN_PATH = "credentials/token.json"
EMAILS_CSV_PATH = "data/fetched_emails.csv"

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    # Load existing credentials if available
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        except Exception:
            print("⚠️ Invalid token, re-authenticating...")
            creds = None

    # If no valid credentials, authenticate user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)  # Fixed port instead of random

        # Save credentials for future use
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    # Build and return Gmail service
    service = build("gmail", "v1", credentials=creds)
    return service

def fetch_recent_emails(max_results=10):
    """Fetch recent emails and store in a DataFrame."""
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])

    email_data = []

    for msg in messages:
        msg_details = service.users().messages().get(userId="me", id=msg["id"]).execute()

        email_info = {
            "id": msg["id"],
            "snippet": msg_details.get("snippet", ""),  # Short preview of the email
            "subject": "",
            "body": "",
            "body_html": "",
        }

        # Extract email subject
        for header in msg_details["payload"]["headers"]:
            if header["name"] == "Subject":
                email_info["subject"] = header["value"]

        # Extract full email body (supports both plain text & HTML emails)
        if "parts" in msg_details["payload"]:
            for part in msg_details["payload"]["parts"]:
                if "data" in part["body"]:
                    decoded_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    if part["mimeType"] == "text/plain":
                        email_info["body"] = decoded_body
                    elif part["mimeType"] == "text/html":
                        email_info["body_html"] = decoded_body

        email_data.append(email_info)

    # Convert to DataFrame
    df = pd.DataFrame(email_data)

    # Ensure 'data' folder exists
    os.makedirs(os.path.dirname(EMAILS_CSV_PATH), exist_ok=True)

    # Save fetched emails to CSV with UTF-8 encoding
    df.to_csv(EMAILS_CSV_PATH, index=False, encoding="utf-8")

    print("✅ Emails fetched successfully!")
    return df

if __name__ == "__main__":
    emails_df = fetch_recent_emails()
    print(emails_df.head())  # Display first few emails
