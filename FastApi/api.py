import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Header
from pydantic import BaseModel
from typing import List, Optional
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
 
logging.basicConfig(level=logging.INFO)
load_dotenv()
 
 
@app.on_event("startup")
def load_model():
    global model
    try:
        model = joblib.load("diabetes_ml_model.pkl")  
    except FileNotFoundError:
        logging.error("Model file not found. Ensure 'diabetes_ml_model.pkl' is present.")
        raise HTTPException(status_code=500, detail="Model file not found. Please contact the administrator.")
 
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")
connection_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)
 
 
class PredictionRequest(BaseModel):
    data: List[dict]
 
 
def get_db_connection():
    try:
        conn = connection_pool.getconn()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection pool exhausted.")
        return conn
    except DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")
   
def insert_predictions_to_db(df: pd.DataFrame, predictions: List[str], confidences: List[float],source: str,actual_labels: List[str]):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        now = pd.Timestamp.now()
        confidences = [float(c) for c in confidences]
        df = df.reset_index(drop=True)
 
        # Prepare all data tuples for batch insert
        data = [
            (
                row['gender'], row['age'], row['heart_disease'], row['smoking_history'],
                row['hbA1c_level'], row['hypertension'], row['blood_glucose_level'],
                row['bmi'], predictions[i], confidences[i], source, now,actual_labels[i]
            )
            for i, row in df.iterrows()
        ]
 
        cursor.executemany(
            """
            INSERT INTO predictions
            (gender, age, heart_disease, smoking_history, hbA1c_level, hypertension, blood_glucose_level, bmi, diabetes_prediction, prediction_confidence, source, prediction_date,actual_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            """,
            data
        )
 
        conn.commit()
    except DatabaseError as e:
        logging.error(f"Database insertion error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving predictions to the database: {str(e)}")
    finally:
        cursor.close()
        connection_pool.putconn(conn)
 
       
@app.post("/predict")
def predict(request: PredictionRequest,background_tasks: BackgroundTasks,x_request_source: Optional[str] = Header(default="Webapp Predictions")):
   
    try:
       
        df = pd.DataFrame(request.data)
        if df.empty:
            raise ValueError("No data provided for prediction.")
       
        required_columns = ["gender", "age", "heart_disease", "smoking_history", "hbA1c_level", "hypertension", "blood_glucose_level", "bmi"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
       
       
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)
        diabetes_prediction = ["Yes" if pred == 1 else "No" for pred in predictions]
        confidence_scores = probabilities.max(axis=1)
        confidence_scores = [float(c) for c in confidence_scores]
       
        df['diabetes_prediction'] = diabetes_prediction
 
        if 'actual_label' in df.columns:
            actual_labels = df['actual_label'].apply(lambda x: "Yes" if x == 1 else "No").tolist()
        else:
            actual_labels = diabetes_prediction  # fallback # Use prediction as actual_label if missing
 
       
        background_tasks.add_task(insert_predictions_to_db, df, diabetes_prediction,confidence_scores, x_request_source,actual_labels)
       
        #
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
       
        timezone = pytz.timezone('UTC')  
        start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time()).astimezone(timezone)
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time()).astimezone(timezone)
 
        conn = get_db_connection()
        cursor = conn.cursor()
 
        query = "SELECT * FROM predictions WHERE prediction_date BETWEEN %s AND %s"
        params = [start_datetime, end_datetime]
 
       
        if source == "Scheduled Predictions":
            query += " AND source = 'Scheduled Predictions' ORDER BY prediction_date DESC"
        elif source == "Webapp Predictions":
            query += " AND source = 'Webapp Predictions' ORDER BY prediction_date DESC"
 
       
        if limit and source != "Webapp Predictions":
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])
 
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        past_predictions = []
       
        for row in rows:
            prediction_dict = dict(zip(columns, row))
 
           
            prediction_dict["heart_disease"] = "Yes" if prediction_dict["heart_disease"] == 1 else "No"
            prediction_dict["hypertension"] = "Yes" if prediction_dict["hypertension"] == 1 else "No"
           
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