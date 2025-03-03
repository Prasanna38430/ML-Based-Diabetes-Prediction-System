# Dsp-ML-Based-Daibetes-App-Project-G1

# Project Setup

This repository contains the setup for an end-to-end data science project involving data validation, ingestion, prediction, and monitoring using various tools and technologies like FastAPI, Streamlit, PostgreSQL, Apache Airflow, and Docker.

## Project Overview

The project aims to:

- Allow users to make on-demand predictions via a **Streamlit** web interface.
- Expose a machine learning model via **FastAPI**.
- Store predictions and data quality information in a **PostgreSQL** database.
- Schedule and run ingestion pipeline, and prediction jobs using **Apache Airflow**.

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

## Prerequisites

Make sure you have the following installed on your machine:

- **Docker**: [Docker Installation Guide](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)
- **Python 3.8+** (for running notebooks and scripts outside of Docker containers)
- **Git**: To clone the repository