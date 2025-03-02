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
        
        # Make prediction
        predictions = model.predict(df)
        diabetes_prediction = ["Yes" if pred == 1 else "No" for pred in predictions]
        
        # Add prediction to the DataFrame
        df['diabetes_prediction'] = diabetes_prediction
        
        # Store predictions asynchronously
        background_tasks.add_task(insert_predictions_to_db, df, diabetes_prediction, "Webapp Predictions")
        
        # Convert the DataFrame to CSV and return as a response
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return Response(content=output.getvalue(), media_type="text/csv")
    
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.get("/past-predictions")
def get_past_predictions(start_date: date, end_date: date, source: str, page: int = 1, limit: int = None):
    """Retrieve past predictions with error handling and dynamic limit."""
    if source not in ["All", "Scheduled Predictions", "Webapp Predictions"]:
        raise HTTPException(status_code=400, detail="Invalid source provided.")

    
    try:
        # Convert start_date and end_date to datetime with timezone (assuming UTC)
        timezone = pytz.timezone('UTC')  # You can change this to your desired time zone if needed
        start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time()).astimezone(timezone)
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time()).astimezone(timezone)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM predictions WHERE prediction_date BETWEEN %s AND %s"
        params = [start_datetime, end_datetime]

        # Adjust query based on source
        if source == "Scheduled Predictions":
            query += " AND source = 'airflow'"
        elif source == "Webapp Predictions":
            query += " ORDER BY prediction_date DESC"

        # Apply limit only if provided and the source is not Webapp Predictions
        if limit and source != "Webapp Predictions":
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        past_predictions = []
        
        for row in rows:
            prediction_dict = dict(zip(columns, row))

            # Convert binary values to "Yes" or "No" for heart disease and hypertension
            prediction_dict["heart_disease"] = "Yes" if prediction_dict["heart_disease"] == 1 else "No"
            prediction_dict["hypertension"] = "Yes" if prediction_dict["hypertension"] == 1 else "No"
            # prediction_dict["diabetes_prediction"] = "Yes" if prediction_dict["diabetes_prediction"] == "1" else "No"
            past_predictions.append(prediction_dict)

        if not past_predictions:
            raise HTTPException(status_code=404, detail="No past predictions found.")

        return {"past_predictions": past_predictions, "page": page, "limit": limit or "All"}

    except DatabaseError as e:
        logging.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")
    finally:
        cursor.close()
        connection_pool.putconn(conn)
