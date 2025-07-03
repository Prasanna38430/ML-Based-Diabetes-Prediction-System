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
def _process_validation_results(result, filepath, total_rows):
        """Process GE validation results into standardized format"""
        import pandas as pd
        vr = result.to_json_dict()
        error_counts = {
            "missing_age": 0,
            "missing_blood_glucose_level": 0,
            "missing_gender": 0,
            "missing_hbA1c_level": 0,
            "invalid_gender": 0,
            "age_out_of_range": 0,
            "bmi_out_of_range": 0,
            "invalid_age_type": 0,
            "invalid_blood_glucose_level_type": 0,
            "invalid_bmi_type": 0,
            "hbA1c_level_format_errors": 0,
            "missing_heart_disease_column": 0,
            "median_age_out_of_range": 0,
            "median_bmi_out_of_range": 0,
        }
        
        bad_rows = set()
        details = []
        table_level_error = False

        
        df = pd.read_csv(filepath)

    
        validation_result = vr

        for r in validation_result["results"]:
            if not r["success"]:
                expectation = r["expectation_config"]["expectation_type"]
                column = r["expectation_config"]["kwargs"].get("column")
                result = r.get("result", {})
                
                # Count errors
                count = result.get("unexpected_count", result.get("missing_count", 1))
                # Capture unexpected indices for failed expectations
                if "unexpected_index_list" in result:
                    bad_rows.update(result["unexpected_index_list"])
                elif "partial_unexpected_index_list" in result:
                    bad_rows.update(result["partial_unexpected_index_list"])
                elif expectation == "expect_column_values_to_not_be_null" and count > 0:
                    # Use Pandas to find null indices for this column
                    if column in df.columns:
                        null_indices = df[df[column].isnull()].index.tolist()
                        bad_rows.update(null_indices)
                elif expectation == "expect_column_values_to_be_between" and column in df.columns:
                        min_val = r["expectation_config"]["kwargs"].get("min_value")
                        max_val = r["expectation_config"]["kwargs"].get("max_value")
                        condition = ~df[column].between(min_val, max_val, inclusive='both')
                        fallback_indices = df[condition].index.tolist()
                        bad_rows.update(fallback_indices)
                elif expectation == "expect_column_values_to_be_in_set" and column in df.columns:
                        valid_set = set(r["expectation_config"]["kwargs"].get("value_set", []))
                        invalid_indices = df[~df[column].isin(valid_set)].index.tolist()
                        bad_rows.update(invalid_indices)
                elif expectation == "expect_column_values_to_be_in_set" and column in df.columns:
                        valid_set = set(r["expectation_config"]["kwargs"].get("value_set", []))
                        invalid_indices = df[~df[column].isin(valid_set)].index.tolist()
                        bad_rows.update(invalid_indices)
                elif expectation == "expect_column_values_to_be_in_type_list" and column in df.columns:
                        expected_types = r["expectation_config"]["kwargs"].get("type_list", [])
                        invalid_indices = df[~df[column].apply(lambda x: isinstance(x, tuple(map(eval, expected_types))) if pd.notnull(x) else True)].index.tolist()
                        bad_rows.update(invalid_indices)
                elif expectation == "expect_column_values_to_match_regex" and column in df.columns:
                        regex = r["expectation_config"]["kwargs"].get("regex")
                        invalid_indices = df[~df[column].astype(str).str.match(regex)].index.tolist()
                        bad_rows.update(invalid_indices)
                
                if expectation == "expect_column_to_exist":
                    table_level_error = True
                    error_counts["missing_heart_disease_column"] = count
                elif expectation == "expect_column_values_to_not_be_null":
                    error_counts[f"missing_{column}"] = count
                elif expectation == "expect_column_values_to_be_in_set":
                    error_counts[f"invalid_{column}"] = count
                elif expectation == "expect_column_values_to_be_between":
                    error_counts[f"{column}_out_of_range"] = count
                elif expectation == "expect_column_values_to_be_in_type_list":
                    error_counts[f"invalid_{column}_type"] = count
                elif expectation == "expect_column_values_to_match_regex":
                    error_counts[f"{column}_format_errors"] = count
                elif expectation == "expect_column_median_to_be_between":
                    error_counts[f"median_{column}_out_of_range"] = count

                details.append(f"{column or 'table'}: {expectation} failed ({count})")

       
        invalid_count = len(bad_rows) if not table_level_error else total_rows
        valid_count = total_rows - invalid_count
        error_ratio = invalid_count / total_rows if total_rows else 0
        criticality = "low" if error_ratio < 0.1 else "medium" if error_ratio < 0.5 else "high"

        return {
            "filepath": filepath,
            "total_rows": total_rows,
            "valid_rows": valid_count,
            "invalid_rows": invalid_count,
            "criticality": criticality,
            "errors_summary": "; ".join(details),
            "error_counts": error_counts,
            "created_on": datetime.now().isoformat(),
            "bad_row_indices": sorted(bad_rows) if not table_level_error else list(range(total_rows)),
        }
