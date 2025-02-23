import streamlit as st
import pandas as pd
import requests
import datetime
import os
from io import StringIO

# API URLs from environment variables (for easier configuration)
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "http://localhost:8000/predict")
PAST_PREDICTIONS_API_URL = os.getenv("PAST_PREDICTIONS_API_URL", "http://localhost:8000/past-predictions")

st.title("ML-Based Diabetes Prediction App")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.selectbox("Go to", ["Prediction", "Past Predictions"])


def get_feature_inputs():
    st.subheader("Enter Features for Prediction:")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    heart_disease = st.selectbox("Heart Disease", ["Yes", "No"])
    smoking_history = st.selectbox("Smoking History", ["Current", "Former", "Never", "No Info"])
    hbA1c_level = st.number_input("HbA1c Level", min_value=0.0, max_value=15.0, step=0.1)
    hypertension = st.selectbox("Hypertension", ["Yes", "No"])
    glucose_level = st.number_input("Glucose Level", min_value=0, max_value=500, step=1)
    bmi = st.number_input("BMI", min_value=10.0, max_value=70.0, step=0.1)

    features = {
        "gender": gender,
        "age": age,
        "heart_disease": 1 if heart_disease == "Yes" else 0,
        "smoking_history": smoking_history,
        "hbA1c_level": hbA1c_level,
        "hypertension": 1 if hypertension == "Yes" else 0,
        "blood_glucose_level": glucose_level,
        "bmi": bmi
    }
    return features