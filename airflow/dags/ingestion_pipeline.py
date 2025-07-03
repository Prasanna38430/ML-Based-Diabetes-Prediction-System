import os
import random
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowFailException, AirflowSkipException


PROJECT_ROOT = "/opt/airflow"
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_data")
GOOD_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "good_data")
BAD_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "bad_data")
GE_DATA_CONTEXT_ROOT = os.path.join(PROJECT_ROOT, "great_expectations")
SUITE_NAME = "diabetes_data_suite"

@dag(
    dag_id="diabetes_ingestion_dag",
    description="Diabetes data ingestion and validation pipeline",
    schedule_interval=timedelta(minutes=2),
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["diabetes", "validation", "data-quality"],
)
def diabetes_ingestion_dag():

    @task(task_id="read_data")
    def read_data() -> str:
        """Select random CSV file from raw data directory"""
        files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]
        if not files:
            raise AirflowSkipException("No CSV files found in raw-data folder")
        return os.path.join(RAW_DATA_DIR, random.choice(files))
 
# Task 2: Save the file by moving it to the good-data folder
def save_file(**kwargs):
    file_path = kwargs['ti'].xcom_pull(task_ids='read-data')
   
    if not file_path:
        print("No file selected. Skipping save-file task.")
        return  
 
    destination_path = os.path.join(GOOD_DATA_PATH, os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    print(f"File moved: {file_path} → {destination_path}")
 

read_task = PythonOperator(
    task_id='read-data',
    python_callable=read_data,
    dag=dag,
)
 
save_task = PythonOperator(
    task_id='save-file',
    python_callable=save_file,
    provide_context=True,  
    dag=dag,
)
 
read_task >> save_task