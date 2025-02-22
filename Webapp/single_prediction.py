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