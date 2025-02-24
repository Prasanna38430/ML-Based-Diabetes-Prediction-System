import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel
from typing import List
import pandas as pd
import joblib
import logging
import os
from psycopg2 import pool, DatabaseError
from dotenv import load_dotenv
from datetime import date
import io
import pytz

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Load the pre-trained model on startup
@app.on_event("startup")
def load_model():
    global model
    try:
        model = joblib.load("diabetes_model.pkl")  # Fixed filename
    except FileNotFoundError:
        logging.error("Model file not found. Ensure 'diabetes_pipeline.pkl' is present.")
        raise HTTPException(status_code=500, detail="Model file not found. Please contact the administrator.")