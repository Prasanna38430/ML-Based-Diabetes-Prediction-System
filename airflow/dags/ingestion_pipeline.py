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

    @task(task_id="validate_data")
    def validate_data(filepath: str) -> dict:
        from airflow.exceptions import AirflowFailException
        import pandas as pd
        import great_expectations as gx
        from great_expectations.datasource.fluent import BatchRequest
        from datetime import datetime
        
        try:
            
            context = gx.get_context(context_root_dir=GE_DATA_CONTEXT_ROOT)

            
            df = pd.read_csv(filepath)
            total_rows = len(df)

            
            if "diabetes_datasource" not in context.datasources:
                datasource = context.sources.add_pandas(name="diabetes_datasource")
            else:
                datasource = context.datasources["diabetes_datasource"]

        
            if "diabetes_asset" in datasource.get_asset_names():
                datasource.delete_asset("diabetes_asset")

            
            asset = datasource.add_csv_asset(name="diabetes_asset", filepath_or_buffer=filepath)

            
            batch_request = BatchRequest(
                datasource_name="diabetes_datasource",
                data_asset_name="diabetes_asset",
                options={}
            )

           
            try:
                suite = context.get_expectation_suite(SUITE_NAME)
            except gx.exceptions.DataContextError:
                suite = context.add_expectation_suite(SUITE_NAME)

           
            validator = context.get_validator(
                batch_request=batch_request,
                expectation_suite=suite
            )

            
            result = validator.validate()
            context.build_data_docs()

            return _process_validation_results(result, filepath, total_rows)

        except Exception as e:
            raise AirflowFailException(f"Validation failed: {str(e)}")
