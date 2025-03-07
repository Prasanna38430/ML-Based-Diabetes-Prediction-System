# Dsp-ML-Based-Diabetes-App-Project

# Project Setup

This repository contains the setup for an end-to-end data science project involving data validation, ingestion, prediction, and monitoring using various tools and technologies like FastAPI, Streamlit, PostgreSQL, Apache Airflow, and Docker.

## Project Overview

The project aims to:

- Allow users to make on-demand predictions and Fetch Past predictions via a **Streamlit** web interface.
- Expose a machine learning model via **FastAPI**.
- Store predictions in a **PostgreSQL** database.
- Schedule and run Ingestion pipeline, and prediction jobs using **Apache Airflow**.

### Components

1. **Webapp** (Streamlit): Provides a UI for making predictions and visualizing past predictions.
2. **API** (FastAPI): Exposes endpoints to make predictions and retrieve past predictions.
3. **Database** (PostgreSQL): Stores predictions, data quality metrics, and logs.
4. **Airflow DAGs**: 
    - Ingest data from raw_data to good_data folder.
    - check data from good_data and Make predictions based on new data.
5. **Notebook**: Generates synthetic data errors in the dataset for testing purposes.
6. **Docker**: The entire setup is containerized using Docker to provide easy deployment.

## Installation and Setup
### Prerequisites

- **Diabetes Dataset**: Download required data set from Kaggle [Diabetes Dataset Kaggle](https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset)

Make sure you have the following installed on your machine:

- **Docker**: [Docker Installation Guide](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)
- **Python 3.8+** (for running notebooks and scripts outside of Docker containers)
- **Git**: To clone the repository
-  **Apache Airflow**: [Airflow Installation Guide with Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html/)

-  **Docker Compose File for all services**:Use docker-compose.yml file

## Project Structure
- Your Project Structure should look like this:

DSP-ML-BASED-DIABETES-APP-PROJECT-G1/
├── airflow/
│   ├── dags/
│   │   ├── prediction_job.py
│   │   └── ingestion_pipeline.py
│   └── data/
│       ├── raw_data/
│       ├── good_data/
│       └── diabetes_data_set.csv
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
├── NoteBook/
│   └── Error_Generation.ipynb
├── Webapp/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── .gitignore
├── docker-compose.vml
└── README.md

### Step 1: Git Ignore Setup

This project excludes certain files and folders from version control to avoid tracking sensitive or large data files. 

### 1. Excluded Files and Folders

The following files and folders are excluded from Git:

- **`data/` folder**: This folder contains raw_data and processed data. It is excluded to avoid tracking large and sensitive files.
- **`.env` file**: This file contains environment variables such as database credentials and API keys. It is excluded to keep sensitive information secure.

### 2. `.gitignore` Configuration

The `.gitignore` file in the project includes the following lines to ensure that the `data/` folder and `.env` file are not tracked by Git:

### 3. How to Use

- **Data Folder**:  
  You will need to set up the `data/` folder locally. It should have the following structure:

  data/
├── raw_data/        # Folder containing raw data after data_generation.
├── good_data/       # Folder containing the files after simple ingestion dag.
└── dataset.csv      # Main dataset used for the project.

Add your raw data to the `raw_data/` folder and cleaned data to the `good_data/` folder.

- **`.env` File**:  
Create a `.env` file in the root directory by copying the contents of `.env.example`. Update the values in the `.env` file for your specific environment, such as database connection details.

**Example `.env` file**  
After updating the `.env` file with your values, it should look something like this:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/diabetes_predictions
AIRFLOW_UID=50000
```

**Note** : The `data/` folder and `.env` file will not be included when you clone the repository. You will need to add your own data files and configure the environment locally.


## Step 2: Clone the Repository

```bash
git clone https://github.com/Prasanna38430/Dsp-ML-Based-Daibetes-App-Project-G1.git
cd Dsp-ML-Based-Daibetes-App-Project-G1
```

### 3. Start Services with Docker Compose
1. Add your Data Base Credentials to Fastapi database service in **docker-Compose.yml** file.

```bash
docker-compose up --build
```
This will start the following services:
- FastAPI backend
- PostgreSQL database
- pgAdmin (database management UI)
- Airflow scheduler & webserver
- Streamlit web app

---

## Step 4: Setup Database
After starting the services, create the `diabetes_predictions` database and `predictions` table.

1. Open a terminal and run:
```sh
docker exec -it <postgres_container_name> psql -U postgres -d diabetes_predictions
```

2. Run the following SQL command inside the PostgreSQL shell:
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

### Reinitialize the Database Service
After setting up the database, restart the PostgreSQL service:
```sh
docker-compose restart db
```

### Access pgAdmin
1. Open `http://localhost:5050` in your browser.
2. Login with:
   - **Email**: `admin@admin.com`
   - **Password**: `admin`
3. Add a new server:
   - Host: `db`
   - Username: `postgres`
   - Password: `postgres`

---
### Step 5: Access Services
- **Web App (Streamlit):** `http://localhost:8501`
- **API Service (FastAPI Docs):** `http://localhost:8000/docs`
- **Airflow UI:** `http://localhost:8080` (Login with `airflow / airflow`)

### Step 5: Setting Up Database Connection in Airflow UI

- Open the Airflow UI at `http://localhost:8080`.

- To set up a PostgreSQL connection in the Airflow UI for track processed files, follow these steps:

1. **Login to Airflow Web UI**
   - Open your browser and go to the Airflow Web UI (usually available at `http://localhost:8080`).

2. **Navigate to Connections**
   - In the top menu, click on **Admin** > **Connections**.

3. **Add New Connection**
   - Click the **+** button to add a new connection.
   - Fill in the following details for the new connection:
     - **Conn Id**: `postgres_default`
     - **Conn Type**: `PostgreSQL`
     - **Host**: `localhost` (or your PostgreSQL server's IP)
     - **Schema**: `your_db_name` (the name of your database)
     - **Login**: `your_db_user` (your PostgreSQL username)
     - **Password**: `your_db_password` (your PostgreSQL password)
     - **Port**: `5432` (default PostgreSQL port)

4. **Test the Connection**
   - After filling out the details, click **Test Connection** to verify the connection.
   - If the test is successful, click **Save** to store the connection details.

5. **Use the Connection in Your DAGs**
   - In your Airflow tasks (such as PythonOperators), you can now use this connection by referring to it with `postgres_conn_id='postgres_default'`.

---

By following these steps, you will have successfully set up your PostgreSQL connection in Airflow.

### Step 6: Running Airflow DAGs

- Enable and trigger the `data_ingestion_pipeline` and `prediction_job` dags.

Good Luck 🤞
