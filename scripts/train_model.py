import os
import pandas as pd
import pickle
import re
import string
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE

# 1️⃣ Load Dataset
DATA_PATH = r"C:\Users\megha\Alertify\data\spam_or_not_spam.csv"
MODEL_DIR = "../models"
MODEL_PATH = os.path.join(MODEL_DIR, "spam_classifier.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")

try:
    df = pd.read_csv(DATA_PATH)  
    print("✅ Dataset loaded successfully.")
except FileNotFoundError:
    print(f"❌ Error: Dataset not found at {DATA_PATH}")
    exit()

# ✅ Check Column Names
if "email" not in df.columns or "label" not in df.columns:
    print("❌ Error: Required columns ('email', 'label') not found in dataset!")
    exit()

print("📌 Columns in dataset:", df.columns)

# 2️⃣ Data Preprocessing Function
def preprocess_text(text):
    """Clean and preprocess email text."""
    if pd.isna(text):  
        return ""
    text = text.lower()  
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()  
    return text

# ✅ Apply preprocessing to 'email' column
df["email"] = df["email"].astype(str).apply(preprocess_text)

# 3️⃣ Define Features (X) and Labels (y)
X = df["email"]  
y = df["label"].astype(int)  

# ✅ Check Dataset Balance
spam_count = y.sum()
non_spam_count = len(y) - spam_count
print(f"📊 Spam Count: {spam_count}, Non-Spam Count: {non_spam_count}")

# 4️⃣ Split Data into Train & Test Sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ✅ Apply SMOTE if dataset is imbalanced
if spam_count < non_spam_count * 0.2:
    print("⚠️ Imbalanced dataset detected! Applying SMOTE oversampling...")
    
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train.values.reshape(-1, 1), y_train)
    
    # Convert back to Pandas Series
    X_train = pd.Series(X_train_resampled.flatten())
    y_train = pd.Series(y_train_resampled)

    print(f"✅ After SMOTE - Spam: {y_train.sum()}, Non-Spam: {len(y_train) - y_train.sum()}")

# 5️⃣ Train TF-IDF + Classifier
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_df=0.95, min_df=2)

# 🔄 Choose Model (Naïve Bayes or Logistic Regression)
USE_LOGISTIC_REGRESSION = True  # Set False to use Naïve Bayes

if USE_LOGISTIC_REGRESSION:
    model = LogisticRegression(class_weight='balanced')
    print("🔹 Using Logistic Regression Model with Balanced Class Weights")
else:
    model = MultinomialNB()
    print("🔹 Using Naïve Bayes Model")

pipeline = make_pipeline(vectorizer, model)  
pipeline.fit(X_train, y_train)  

# 6️⃣ Evaluate the Model
y_pred = pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy: {accuracy:.2f}")

# 7️⃣ Ensure 'models/' folder exists before saving
os.makedirs(MODEL_DIR, exist_ok=True)

# 8️⃣ Save Model and Vectorizer as .pkl Files
with open(MODEL_PATH, "wb") as model_file:
    pickle.dump(pipeline, model_file)

with open(VECTORIZER_PATH, "wb") as vectorizer_file:
    pickle.dump(vectorizer, vectorizer_file)

print(f"🎉 Model and vectorizer saved successfully in `{MODEL_DIR}/` folder.")
