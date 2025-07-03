# Dsp-ML-Based-Diabetes-App-Project

# Project Setup

## Introduction

This project is an end-to-end diabetes prediction system that automates data ingestion, validation, prediction, and monitoring. It combines FastAPI, Streamlit, Apache Airflow, Great Expectations, PostgreSQL, and Grafana to deliver reliable and scalable machine learning workflows with easy-to-use interfaces and real-time quality monitoring.


## Project Overview

The project aims to:

- Allow users to make on-demand predictions and Fetch Past predictions via a **Streamlit** web interface.
- Expose a machine learning model via **FastAPI**.
- Automates Data ingestion, validation, and prediction orchestration using **Apache Airflow**.
- Ensures high data quality and consistency by validating incoming data using **Great Expectations**.
- Stores validation metrics and prediction results securely in a **PostgreSQL** database for tracking and analysis.
- Offers comprehensive monitoring of data quality, prediction accuracy, and model drift with interactive **Grafana** dashboards.


### Components

1. **Webapp** (Streamlit): Provides a UI for making predictions and Retrive past predictions.
2. **API** (FastAPI): Exposes endpoints to make and Store predictions, and retrieve past predictions.
3. **Database** (PostgreSQL): Stores On demand Webapp predictions and Scheduled  predictions.
4. **Airflow DAGs**: 
    - Ingest data from raw_data, validates to good_data folder.
    - check data from good_data and Make predictions based on new data.
5. **Great Expectations** integration for robust data validation.
6. **Notebook**: Generates synthetic data errors in the dataset for testing purposes.
7. **Grafana**: Real-time monitoring dashboards for data quality, drift, and prediction insights
8. **Docker**: The entire setup is containerized using Docker to provide easy deployment.

## Installation and Setup
### Prerequisites

- **Diabetes Dataset**: Download required data set from Kaggle [Diabetes Dataset Kaggle](https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset)

Make sure you have the following installed on your machine:

- **Docker**: [Docker Installation Guide](https://docs.docker.com/get-docker/)
- **Python 3.8+** (for running notebooks and scripts outside of Docker containers)
- **Git**: To clone the repository
-  **Apache Airflow**: [Airflow Installation Guide with Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html/)
- **Great Expectations v0.18.19**: used for validating the ingested data
-  **Docker Compose File for all services**:Use `docker-compose.yml` file

## Project Structure
- Your Project Structure should look like this:

```bash
DSP-ML-BASED-DIABETES-APP-PROJECT-G1/
├── airflow/
│   ├── dags/
│   │   ├── prediction_job.py
│   │   └── ingestion_pipeline.py
│   ├── data/
│   │   ├── raw_data/
│   │   ├── good_data/
│   │   ├── bad_data/
│   │   ├── generated_errors/
│   │   └── diabetes_data_set.csv
│   ├── great_expectations/
│   │   ├── checkpoints/
│   │   │   └── diabetes_checkpoint.yml
│   │   ├── expectations/
│   │   │   └── diabetes_data_suite.json
│   │   └── uncommitted/
│   │       └── data_docs/
│   │           └── local_site/
│   ├── Dockerfile
│   └── requirements.txt
├── data_generation/
│   └── data_generation_split.py
├── Database/
│   └── database_setup.sql
├── FastApi/
│   ├── api.py
│   ├── diabetes_ml_model.pkl
│   ├── Dockerfile
│   ├── ml_model_training.py
│   └── requirements.txt
├── Grafana/
│   └── grafana_queries.sql
├── NoteBook/
│   └── Error_Generation.ipynb
├── Webapp/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Step 1: Git Ignore Setup

This project excludes certain files and folders from version control to avoid tracking sensitive or large data files. 

### 1. Excluded Files and Folders

The following files and folders are excluded from Git:

- **`data/` folder**: This folder contains raw_data and processed data. It is excluded to avoid tracking large and sensitive files.
- **`.env` file**: This file contains environment variables such as database credentials and API keys. It is excluded to keep sensitive information secure.

### 2. `.gitignore` Configuration

The `.gitignore` file in the project includes the following lines to ensure that the `data/` folder and `.env` file are not tracked by Git:

### 3. How to Use

**Data Folder**:  
- You will need to set up the `data/` folder locally. It should have the following structure:

```bash
  data/
├── raw_data/        # Folder containing raw data after data_generation.
├── good_data/       # Folder containing the files without errors after validating in ingestion dag
├── bad_data/        # Folder containing the files with errors after validating in ingestion dag.
└── dataset.csv      # Main dataset used for the project.
```
- The Generated data for ingestion will store in `raw_data/` folder and cleaned data will strore `good_data/` folder.

**`.env` File**:  
- Create a `.env` file in the root directory by copying the contents of `.env.example`. Update the values in the `.env` file for your specific environment, such as database connection details.

**Example `.env` file**  
- After updating the `.env` file with your values, it should look something like this:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@db:5432/diabetes_predictions
AIRFLOW_UID=50000
```

**Note** : The `data/` folder and `.env` file will not be included when you clone the repository. You will need to add your own data files and configure the environment locally.


## Step 2: Clone the Repository

```bash
git clone https://github.com/Prasanna38430/Dsp-ML-Based-Daibetes-App-Project-G1.git
cd Dsp-ML-Based-Daibetes-App-Project-G1
```

## Step 3:  Start Services with Docker Compose
1. Add your Data Base Credentials to Fastapi database service in **docker-Compose.yml** file.

```bash
docker-compose up --build
```
This will start the following services:
- **Airflow Webserver:** `http://localhost:8080` (Login with `airflow / airflow`)
- **FastAPI API:** `http://localhost:8000`
- **Streamlit Webapp:** `http://localhost:8501`
- **Grafana Dashboard:** `http://localhost:3001` (Login with `dsp / project`)
- **Great Expectations Data Docs (via nginx):** `http://localhost:8085`
- **PGAdmin (Postgres GUI):** `http://localhost:5050` (Login with `admin@example.com / project`)

---

## Step 4: Setup Database

After starting the services, create the `diabetes_predictions` database and `predictions` table.

1. **Open a terminal and run:**
```sh
docker exec -it <postgres_container_name> psql -U postgres -d diabetes_predictions
```

2. **Run the following SQL command inside the PostgreSQL shell:**
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    gender VARCHAR(50),
    age INT,
    heart_disease INT,
    smoking_history VARCHAR(50),
    hbA1c_level FLOAT,
    hypertension INT,
    blood_glucose_level INT,
    bmi FLOAT,
    diabetes_prediction VARCHAR(10),
    source VARCHAR(50),
    prediction_date TIMESTAMP
);
```

3. **Re-initialize the Database Service**
After setting up the database, restart the PostgreSQL service:
```sh
docker-compose restart < database Container id or name >
```

4. **Access pgAdmin**
   1. Open `http://localhost:5050` in your browser.
   2. Login with:
      - **Email**: `admin@example.com`
      - **Password**: `project`
   3. Add a new server:
      - Host: `db`
      - Username: `your_user_name`
      - Password: `your_passowrd`
   4. Create data base for tracking files 

   ```sh
   Data base name : processed_files_db
   ```
   ```sql
   CREATE TABLE IF NOT EXISTS processed_files (
      file_name TEXT PRIMARY KEY
   ); #for table creation
   ```

5. Create new database of `diabetes_errors` with table `diabetes_data_ingestion_stats` with follwing schema

   ```sql
   CREATE TABLE diabetes_data_ingestion_stats (
      id SERIAL PRIMARY KEY,
      file_name VARCHAR(255),
      total_rows INTEGER,
      valid_rows INTEGER,
      invalid_rows INTEGER,
      missing_age INTEGER,
      missing_blood_glucose_level INTEGER,
      missing_gender INTEGER,
      missing_hbA1c_level INTEGER,
      invalid_gender INTEGER,
      age_out_of_range INTEGER,
      bmi_out_of_range INTEGER,
      invalid_age_type INTEGER,
      invalid_blood_glucose_level_type INTEGER,
      invalid_bmi_type INTEGER,
      hbA1c_level_format_errors INTEGER,
      missing_heart_disease_column INTEGER,
      median_age_out_of_range INTEGER,
      median_bmi_out_of_range INTEGER,
      criticality VARCHAR(50),
      error_summary TEXT,
      created_on TIMESTAMP
   );
   ```

---

## Step 5: Setting Up Database Connection in Airflow UI

- Open the Airflow UI at `http://localhost:8080`.

- To set up a PostgreSQL connection in the Airflow UI for tracking processed files, follow these steps:

1. **Login to Airflow Web UI**
   - Open your browser and go to the Airflow Web UI (usually available at `http://localhost:8080`).

2. **Navigate to Connections**
   - In the top menu, click on **Admin** > **Connections**.

3. **Setting up Airflow Connections and Variables**
   1. Add PostgreSQL Connection (for processed files)
   - Click the **+** button to add a new connection.
   - Fill in the following details for the new connection:
     - **Conn Id**: `postgres_default`
     - **Conn Type**: `PostgreSQL`
     - **Host**: `localhost` (or your PostgreSQL server's IP)
     - **Schema**: `your_db_name` (the name of your database)
     - **Login**: `your_db_user` (your PostgreSQL username)
     - **Password**: `your_db_password` (your PostgreSQL password)
     - **Port**: `5432` (default PostgreSQL port)
   - Save the connection.


   2. Add PostgreSQL Connection (for saving validation stats)
   - Go to **Admin** → **Connections**
   - Click the **+** button to add a new connection.
   - Fill in the following details for the new connection:
      - **Conn Id**: `postgres_dsp`
      - **Conn Type**: `PostgreSQL`
      - **Host**: `localhost` (or your PostgreSQL server IP)
      - **Schema**: `<your_database_name>` (e.g., `diabetes_db`)
      - **Login**: `<your_db_user>` (PostgreSQL username)
      - **Password**: `<your_db_password>` (PostgreSQL password)
      - **Port**: `5432` (default PostgreSQL port)
   - Save the connection.


   3. Add Microsoft Teams Webhook URL Variable (for sending alerts)
   - Go to **Admin** → **Variables**
   - Click the **+** button to add a new variable.
   - Fill in the following details:
      - **Key**: `TEAMS_WEBHOOK_URL`
      - **Value**: `<your_teams_webhook_url>` (the full URL to your Teams incoming webhook)
   - Save the variable.
   

By following above steps, you will have successfully set up your PostgreSQL connections and Team Webhook Connection in Airflow.

### Step 6: Setting up Great Expectations with Airflow and Docker

- **Great Expectations (version 0.18.19)** to ensure high-quality, reliable data ingestion for diabetes prediction.

- The `Dockerfile` and accompanying `requirements.txt` are pre-configured to install Great Expectations within the Airflow container environment.
- This ensures that all data validation logic and dependencies are available when Airflow runs the ingestion and validation DAGs.
- The project mounts the Great Expectations configuration and expectation suites inside the Airflow container, enabling seamless execution of validation checkpoints as part of the workflow.

## Step 6: Setting Up Grafana (via Docker Compose)

Grafana is pre-configured via `docker-compose.yml` — no manual installation required.

- **URL**: [http://localhost:3001](http://localhost:3001)  
- **Username**: `dsp`  
- **Password**: `project`


## Step 7: Running Airflow DAGs
- Enable and trigger the `diabetes_ingestion_dag` and `prediction_job` dags.

✅ By following the above steps, you will have successfully set up the **Diabetes ML Prediction System** with automated data validation, real-time monitoring, and user-friendly prediction interfaces.



## 🔍  Role of Each Service
### 🧑‍💻 User-Facing Services (On-Demand)
These components allow manual user interaction, real-time prediction, and history lookup:

## 1. Streamlit Webapp

The Streamlit app provides an interactive UI for diabetes prediction with two main features:

- **Prediction Page**  
  - Supports single and batch predictions.  
  - Users can input features manually or upload CSV files with multiple records.  
  - Sends data to the FastAPI backend for inference and displays results in a table.  
  - Allows downloading prediction results as CSV.

- **Past Predictions Page**  
  - Enables users to query and view historical predictions filtered by date range and source.  
  - Displays results in a table with download option for CSV export.

The app interacts with the FastAPI API endpoints (`/predict` and `/past-predictions`) to perform real-time predictions and retrieve stored data, providing a seamless user experience for diabetes risk assessment.


## 2. Model Training & FastAPI Backend

### Model Training Script

The model training pipeline involves:

- Loading and preprocessing the diabetes dataset (handling numerical and categorical features with scaling and one-hot encoding).
- Splitting the data into train and test sets.
- Training a Random Forest classifier on the training data.
- Evaluating accuracy on the test set.
- Saving the trained pipeline (including preprocessing and model) as `diabetes_ml_model.pkl` for use by the FastAPI service.

The model training script is located in the `FastApi/ml_model_training.py` file and outputs the trained model used by the API.

### FastAPI Service

The FastAPI backend exposes endpoints to make diabetes predictions and retrieve past predictions. Key features include:

- **Model Loading:** Loads a pre-trained Random Forest model (`diabetes_ml_model.pkl`) on startup.
- **Prediction Endpoint (`/predict`):** Accepts input data as JSON, validates required columns, predicts diabetes risk, calculates confidence scores, and asynchronously saves results to PostgreSQL.
- **Past Predictions Endpoint (`/past-predictions`):** Retrieves historical prediction records filtered by date range and source.
- **Database Connection:** Uses a PostgreSQL connection pool for efficient data storage and retrieval.
- **Background Tasks:** Inserts predictions into the database asynchronously to keep API responses fast and responsive.

## ⚙️ Automated Pipelines (Airflow Orchestration)

These pipelines run automatically and handle data ingestion, validation, and prediction:

### 1. The following Airflow DAGs automate the entire backend workflow: 

### Airflow DAG 1: `diabetes_ingestion_dag`

- Picks a random `.csv` file from `raw_data/` folder
- Validates with Great Expectations
- Stores validation metrics in PostgreSQL
- Sends Teams alerts if data quality is poor
- Moves file to either `good_data/` or `bad_data/` based on results

### Airflow DAG 2: ``prediction_job``
- Check any new `.csv` files in `good_data/` folder
- Send those files to fastapi to make predictions


### 2. Data Validation with Great Expectations

- Validates incoming data using a comprehensive expectation suite (`diabetes_data_suite.json`) that includes:
  - Checks for **null values** in critical columns (`age`, `gender`, `blood_glucose_level`, `hbA1c_level`).
  - Verifies **data types** (int, float) for numeric columns.
  - Ensures **value ranges** are respected (e.g., `age` between 0 and 120, `bmi` between 10 and 70).
  - Validates **regex format** for `hbA1c_level`.
  - Confirms existence of key columns like `heart_disease`.
  - Checks **median values** within specified bounds for `age` and `bmi`.
  - Validates `gender` values to be within allowed set (`Male`, `Female`, `Other`).

- Validation is orchestrated using a **Great Expectations checkpoint** configured in `diabetes_checkpoint.yml`.

- The Airflow DAG `ingestion_pipeline.py` runs this GE checkpoint to validate incoming data files against the defined expectations automatically.

- Validation results are:
  - Stored in a **PostgreSQL** table for further analysis.
  - Presented as rich **Data Docs** served through an Nginx container, accessible at `http://localhost:8085`.
  - Monitored and visualized through **Grafana dashboards** for real-time data quality insights.

## Database Tables

- `predictions` – Stores model outputs
- `diabetes_data_ingestion_stats` – Stores ingestion and validation results
- `training_data` – Used as baseline for drift detection
- `processed_files` – Prevents reprocessing of already-ingested files


## 📊 Grafana Dashboards

### Monitoring Dashboards for Data Quality and Model Performance

Effective monitoring of both data ingestion quality and model predictive performance is essential for maintaining the reliability and robustness of machine learning systems in production. 

---

### 1. Ingested Data Quality Monitoring Dashboard

This dashboard provides real-time insights into the quality and integrity of incoming data streams. Monitoring these metrics facilitates early detection of data anomalies that may compromise downstream predictive accuracy.

- **Invalid Rows Percentage Gauge**  
  Displays the proportion of invalid rows within the last 10-minute ingestion window.  
  **Purpose:** Quickly identifies bad or incomplete patient records so they can be fixed before affecting predictions.

- **Valid vs Invalid Row Trends**  
  Temporal visualization of counts of valid versus invalid records across recent ingestion batches.  
  **Purpose:** Helps track if data quality is improving or getting worse over time.

- **Missing Value Percentage Drift**  
  Measures the percentage of missing values aggregated over 10-minute intervals across the past 24 hours.  
  **Purpose:** Tracks missing data in key features like blood glucose or HbA1c, which are important for diabetes prediction.

- **Error Category Breakdown**  
  Categorical distribution of ingestion errors over the past hour, encompassing missing values, type mismatches, range violations, and format errors.  
  **Purpose:** Categorizing error types directs and helps focus on fixing the most common data problems.

- **Missing Values Distribution**  
  Feature-level aggregation of missing value counts within the most recent 30-minute period.  
  **Purpose:** Identifies which specific features suffer from data gaps, informing feature-specific data quality improvements.

---

### 2. Data Drift and Model Prediction Monitoring Dashboard

This dashboard tracks key indicators of model input drift and predictive performance, enabling the detection of degradation and informing model maintenance decisions.

- **Prediction Class Distribution**  
  Distribution of predicted classes ("Yes" vs "No") within the last hour.  
  **Purpose:** Monitoring class prediction ratios assists in detecting shifts in input data distribution or model bias.

- **Age Feature Drift Relative to Training Data**  
  Percentage deviation of average predicted age (calculated in 30-minute intervals) compared to the training dataset mean.  
  **Purpose:** Helps identify changes in the patient population that might affect the model’s accuracy since age is an important factor.

- **Model Confidence Score Over Time**  
  Average confidence of model predictions aggregated over 30-minute intervals.  
  **Purpose:** Lower confidence might indicate the model is less certain due to new or different patient data..

- **Model Accuracy Over Time**  
  Hourly aggregated accuracy metric derived by comparing predicted labels to actual ground truth.  
  **Purpose:** Measures how well the model is performing with real data, which is key to trusting its predictions.

---
- Grafana queries for all these graphs are provided in a separate `grafana_queries.sql` file.

### 3. Grafana Alerts:
- Alerts monitor critical metrics such as data ingestion quality, prediction class balance, and model accuracy.
- They notify the team immediately about data errors, imbalanced predictions, or declining model performance.
- Proactive alerting helps maintain system reliability and enables timely corrective actions.


## Contributors
- **Prasanna Kumar ADABALA**
- **Mouna Priya Pokuru**
- **Raghuram Munagala**
- **Bhargavi Akula**
- **Nithin Naga Sai Gajula**


## Conclusion

Thank you for checking out this project! This project provides a complete, automated diabetes prediction system with reliable data validation, real-time monitoring, and user-friendly interfaces. It demonstrates a practical approach to deploying trustworthy machine learning solutions in healthcare.

Contributions and feedback are welcome!



Good Luck 🤞
