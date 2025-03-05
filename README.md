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
6. **Data Ingestion Pipeline**: Moves data from the raw folder to the good folder after validation.
7. **Docker**: The entire setup is containerized using Docker to provide easy deployment.

### Installation and Setup
## Prerequisites

Make sure you have the following installed on your machine:

- **Docker**: [Docker Installation Guide](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)
- **Python 3.8+** (for running notebooks and scripts outside of Docker containers)
- **Git**: To clone the repository
-  **Apache Airflow**: [Airflow Installation Guide with Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html/)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Prasanna38430/Dsp-ML-Based-Daibetes-App-Project-G1.git
cd Dsp-ML-Based-Daibetes-App-Project-G1
```

### Step 2: Start Services with Docker Compose
```bash
docker-compose up --build
```
This will start the following services:
- FastAPI backend
- PostgreSQL database
- pgAdmin (database management UI)
- Airflow scheduler & webserver
- Streamlit web app
- pgAdmin for database management

---

### 3 Setup Database
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
### Step 4: Access Services
- **Web App (Streamlit):** `http://localhost:8501`
- **API Service (FastAPI Docs):** `http://localhost:8000/docs`
- **Airflow UI:** `http://localhost:8080` (Login with `airflow / airflow`)

### Step 4: Running Airflow DAGs
- Open the Airflow UI at `http://localhost:8080`.
- Enable and trigger the `data_ingestion_pipeline` and `prediction_job` dags.

