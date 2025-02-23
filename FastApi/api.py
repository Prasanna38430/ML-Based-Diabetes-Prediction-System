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
# Database connection pool setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")
connection_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)

# Define the request schema for prediction
class PredictionRequest(BaseModel):
    data: List[dict]

# Utility function to get database connection
def get_db_connection():
    try:
        conn = connection_pool.getconn()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection pool exhausted.")
        return conn
    except DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")