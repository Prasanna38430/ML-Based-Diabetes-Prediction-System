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
    
def insert_predictions_to_db(df: pd.DataFrame, predictions: List[str], source: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for index, row in df.iterrows():
            cursor.execute(
                """
                INSERT INTO predictions (gender, age, heart_disease, smoking_history, hbA1c_level, hypertension, blood_glucose_level, bmi, diabetes_prediction, source, prediction_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row['gender'], row['age'], row['heart_disease'], row['smoking_history'],
                    row['hbA1c_level'], row['hypertension'], row['blood_glucose_level'],
                    row['bmi'], predictions[index], source, pd.Timestamp.now()
                )
            )

        conn.commit()
    except DatabaseError as e:
        logging.error(f"Database insertion error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving predictions to the database: {str(e)}")
    finally:
        cursor.close()
        connection_pool.putconn(conn)  # Return the connection to the pool
        
@app.post("/predict")
def predict(request: PredictionRequest, background_tasks: BackgroundTasks):
    try:
        # Convert input data to DataFrame
        df = pd.DataFrame(request.data)
        if df.empty:
            raise ValueError("No data provided for prediction.")
        
        # Check if all required columns are present
        required_columns = ["gender", "age", "heart_disease", "smoking_history", "hbA1c_level", "hypertension", "blood_glucose_level", "bmi"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        