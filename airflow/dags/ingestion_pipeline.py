import os
import random
import shutil
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
 
# Define paths for raw-data and good-data folders
RAW_DATA_PATH = "/opt/airflow/data/raw_data"
GOOD_DATA_PATH = "/opt/airflow/data/good_data"
 

dag = DAG(
    'simple_ingestion_pipeline',
    description='Ingest data from raw-data to good-data',
    schedule_interval='*/1 * * * *',  
    start_date=datetime(2025, 3, 5),
    catchup=False,
)
 
# Task 1: Read one file randomly from the raw-data folder
def read_data():
    files = [f for f in os.listdir(RAW_DATA_PATH) if os.path.isfile(os.path.join(RAW_DATA_PATH, f))]
 
    if not files:
        print("No files found in raw-data folder. Skipping execution.")
        return None  
 
    selected_file = random.choice(files)
    file_path = os.path.join(RAW_DATA_PATH, selected_file)
    print(f"Selected file: {file_path}")
    return file_path
 
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