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

    @task(task_id="save_statistics")
    def save_statistics(results: dict) -> None:
        """Save validation statistics to database"""
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        from airflow.exceptions import AirflowFailException

        conn = None
        cursor = None
        try:
            hook = PostgresHook(postgres_conn_id="postgres_dsp")
            conn = hook.get_conn()
            cursor = conn.cursor()

            query = """
                INSERT INTO diabetes_data_ingestion_stats (
                    file_name, total_rows, valid_rows, invalid_rows,
                    missing_age, missing_blood_glucose_level, missing_gender, missing_hbA1c_level,
                    invalid_gender, age_out_of_range, bmi_out_of_range,
                    invalid_age_type, invalid_blood_glucose_level_type, invalid_bmi_type,
                    hbA1c_level_format_errors, missing_heart_disease_column,
                    median_age_out_of_range, median_bmi_out_of_range,
                    criticality, error_summary, created_on
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            ec = results["error_counts"]
            cursor.execute(query, (
                os.path.basename(results["filepath"]),
                results["total_rows"],
                results["valid_rows"],
                results["invalid_rows"],
                ec["missing_age"],
                ec["missing_blood_glucose_level"],
                ec["missing_gender"],
                ec["missing_hbA1c_level"],
                ec["invalid_gender"],
                ec["age_out_of_range"],
                ec["bmi_out_of_range"],
                ec["invalid_age_type"],
                ec["invalid_blood_glucose_level_type"],
                ec["invalid_bmi_type"],
                ec["hbA1c_level_format_errors"],
                ec["missing_heart_disease_column"],
                ec["median_age_out_of_range"],
                ec["median_bmi_out_of_range"],
                results["criticality"],
                results["errors_summary"],
                results["created_on"],
            ))
            conn.commit()
        except Exception as e:
            raise AirflowFailException(f"Database error: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @task(task_id="send_alerts")
    def send_alerts(results: dict) -> None:
        """Send validation alerts to Teams"""
        import requests
        import great_expectations as gx
        from airflow.models import Variable
        from airflow.exceptions import AirflowFailException
        import logging
        import os
        import glob

        try:
            # Attempt to get the webhook URL, with a fallback
            try:
                webhook_url = Variable.get("TEAMS_WEBHOOK_URL")
            except KeyError:
                logging.warning("TEAMS_WEBHOOK_URL variable not found. Skipping alert.")
                return  # Skip sending alert if variable is missing

            # Load Great Expectations context
            context = gx.get_context(context_root_dir=GE_DATA_CONTEXT_ROOT)

            # Get data docs URLs from configured sites
            docs_url = "http://localhost:8085/validation_results.html"  # Default fallback
            try:
                # Rebuild data docs to ensure latest validation results are included
                context.build_data_docs()
                # Access data docs sites from context configuration
                sites = context.get_config().data_docs_sites
                if sites:
                    for site_name, site_config in sites.items():
                        if "validation_result" in site_name.lower() or "local_site" in site_name.lower():
                            base_url = site_config.get("site_url", docs_url)
                            # Find the latest validation result for the file
                            batch_identifier = os.path.basename(results["filepath"]).replace(".csv", "")
                            validation_glob = f"{GE_DATA_CONTEXT_ROOT}/uncommitted/data_docs/local_site/validations/{SUITE_NAME}/*/{batch_identifier}/validation_result.html"
                            validation_files = glob.glob(validation_glob)
                            if validation_files:
                                latest_validation = max(validation_files, key=os.path.getmtime)
                                validation_path = latest_validation.replace(f"{GE_DATA_CONTEXT_ROOT}/uncommitted/data_docs/local_site/", "")
                                docs_url = f"{base_url.rstrip('/')}/{validation_path}"
                                break
                logging.info(f"Data docs URL: {docs_url}")
            except Exception as e:
                logging.warning(f"Failed to retrieve data docs URL: {str(e)}. Using fallback URL: {docs_url}")

            alert = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "body": [
                            {"type": "TextBlock", "text": "Diabetes Data Validation", "weight": "bolder", "size": "medium"},
                            {"type": "TextBlock", "text": f"File: {os.path.basename(results['filepath'])}"},
                            {"type": "TextBlock", "text": f"Status: {results['criticality'].upper()} ({results['invalid_rows']}/{results['total_rows']} issues)"},
                            {"type": "TextBlock", "text": "Issues:", "weight": "bolder"},
                            {"type": "TextBlock", "text": results["errors_summary"], "wrap": True}
                        ],
                        "actions": [{
                            "type": "Action.OpenUrl",
                            "title": "View Details",
                            "url": docs_url
                        }]
                    }
                }]
            }

            for _ in range(3):  # Retry up to 3 times
                try:
                    response = requests.post(webhook_url, json=alert, timeout=10)
                    if response.status_code == 200:
                        logging.info("Successfully sent alert to Teams.")
                        return
                    else:
                        logging.warning(f"Teams webhook request failed with status {response.status_code}: {response.text}")
                except requests.RequestException as e:
                    logging.warning(f"Attempt to send alert failed: {str(e)}")
                    continue
            raise Exception("Failed to send alert after 3 attempts")
        except Exception as e:
            raise AirflowFailException(f"Alert failed: {str(e)}")

    @task(task_id="save_files")
    def save_files(results: dict) -> None:
        """Save good/bad data files"""
        import pandas as pd

        try:
            df = pd.read_csv(results["filepath"])
            base_name = os.path.basename(results["filepath"])
            
            if results["invalid_rows"] == 0:
                # Save all rows to GOOD_DATA_DIR
                df.to_csv(os.path.join(GOOD_DATA_DIR, base_name), index=False)
            elif results["valid_rows"] == 0:
                # Save all rows to BAD_DATA_DIR
                df.to_csv(os.path.join(BAD_DATA_DIR, base_name), index=False)
            else:
                # Split good and bad rows
                good_indices = [i for i in range(len(df)) if i not in results["bad_row_indices"]]
                good_df = df.iloc[good_indices]
                bad_df = df.iloc[results["bad_row_indices"]]
                if not good_df.empty:
                    good_df.to_csv(os.path.join(GOOD_DATA_DIR, base_name), index=False)
                if not bad_df.empty:
                    bad_df.to_csv(os.path.join(BAD_DATA_DIR, base_name), index=False)
            
            os.remove(results["filepath"])
        except Exception as e:
            raise AirflowFailException(f"File operation failed: {str(e)}")

    # DAG structure
    data_file = read_data()
    validation_results = validate_data(data_file)
    
    data_file >> validation_results >> [
        send_alerts(validation_results),
        save_files(validation_results),
        save_statistics(validation_results)
    ]

# Instantiate the DAG
diabetes_ingestion_dag = diabetes_ingestion_dag()