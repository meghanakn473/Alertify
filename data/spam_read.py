import pandas as pd

dataset_path = r"C:\Users\megha\Alertify\data\spam_or_not_spam.csv"  # Use full path
df = pd.read_csv(dataset_path)
print(df.head())  # Check if the data loads correctly
