import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


# Load dataset safely
try:
    df = pd.read_csv("diabetes_dataset.csv", low_memory=False)
except FileNotFoundError:
    raise FileNotFoundError("❌ The file 'diabetes_dataset.csv' was not found. Ensure it's in the correct directory.")

# Clean column names (remove spaces)
df.columns = df.columns.str.strip()

# Debugging step: Print dataset info
print("✅ Loaded dataset with columns:", df.columns)
print(df.head())

# Ensure the target column exists
if "diabetes" not in df.columns:
    raise ValueError("❌ 'diabetes' column is missing from the dataset! Check for typos or incorrect column names.")

# Split features and target variable
X = df.drop(columns=["diabetes"])
y = df["diabetes"]

# Identify categorical & numerical features
categorical_features = ["gender", "smoking_history"]
numerical_features = ["age", "hypertension", "heart_disease", "bmi", "hbA1c_level", "blood_glucose_level"]

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ]
)