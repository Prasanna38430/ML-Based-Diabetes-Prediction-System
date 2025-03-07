import streamlit as st
import pandas as pd
import requests
import datetime
import os
from io import StringIO

# API URLs from environment variables (for easier configuration)
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "http://localhost:8000/predict")
PAST_PREDICTIONS_API_URL = os.getenv("PAST_PREDICTIONS_API_URL", "http://localhost:8000/past-predictions")

st.title("ML-Based Diabetes Prediction App")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.selectbox("Go to", ["Prediction", "Past Predictions"])


def get_feature_inputs():
    st.subheader("Enter Features for Prediction:")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    heart_disease = st.selectbox("Heart Disease", ["Yes", "No"])
    smoking_history = st.selectbox("Smoking History", ["Current", "Former", "Never", "No Info"])
    hbA1c_level = st.number_input("HbA1c Level", min_value=0.0, max_value=15.0, step=0.1)
    hypertension = st.selectbox("Hypertension", ["Yes", "No"])
    glucose_level = st.number_input("Glucose Level", min_value=0, max_value=500, step=1)
    bmi = st.number_input("BMI", min_value=10.0, max_value=70.0, step=0.1)

    features = {
        "gender": gender,
        "age": age,
        "heart_disease": 1 if heart_disease == "Yes" else 0,
        "smoking_history": smoking_history,
        "hbA1c_level": hbA1c_level,
        "hypertension": 1 if hypertension == "Yes" else 0,
        "blood_glucose_level": glucose_level,
        "bmi": bmi
    }
    return features


# Prediction Page (Single and Multiple)
if page == "Prediction":
    st.subheader("Prediction")

    # Tabs for single and multiple predictions
    tab1, tab2 = st.tabs(["Single Prediction", "Multiple Predictions"])

    with tab1:
        features = get_feature_inputs()
        if st.button("Predict"):
            try:
                headers = {"X-Request-Source": "Webapp Predictions"}
                response = requests.post(
                    PREDICTION_API_URL,
                    json={"data": [features]},
                    headers=headers
                )
                
                # Check if the response is empty
                if not response.text.strip():
                    st.error("The response from the API is empty.")
                    st.stop()  # Stop the execution here

                if response.status_code == 200:
                    # If the response is CSV, we will parse it as such
                    if response.text.strip().startswith("gender"):
                        # Read CSV response into a DataFrame
                        df = pd.read_csv(StringIO(response.text))
                        
                        # Drop any unwanted empty columns
                        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                        
                        # Set gender as the index
                        df.set_index('gender', inplace=True)

                        st.write("Prediction Result:")
                        st.dataframe(df)  # Show the DataFrame without index
                        st.download_button(
                            label="Download Prediction as CSV",
                            data=df.to_csv(index=True).encode('utf-8'),
                            file_name='single_prediction_result.csv',
                            mime='text/csv'
                        )
                    else:
                        st.error("Unexpected response format")
                else:
                    st.error(f"Failed to get a valid response from the API. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab2:
        uploaded_file = st.file_uploader("Upload a CSV file for Multiple Predictions", type=["csv"])

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of Uploaded Data:")
            st.dataframe(df)

            # Ensure required columns are present
            required_columns = ["gender", "age", "heart_disease", "smoking_history", "hbA1c_level", "hypertension", "blood_glucose_level", "bmi"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                # Prepare JSON payload
                data_payload = df.to_dict(orient="records")
                if st.button("Predict Multiple"):
                    try:
                        headers = {"X-Request-Source": "Webapp Predictions"}
                        response = requests.post(PREDICTION_API_URL,json={"data": data_payload},headers=headers)

                        # Check if the response is empty
                        if not response.text.strip():
                            st.error("The response from the API is empty.")
                            st.stop()  # Stop the execution here

                        if response.status_code == 200:
                            # If the response is CSV, we will parse it as such
                            if response.text.strip().startswith("gender"):
                                df = pd.read_csv(StringIO(response.text))

                                # Drop any unwanted empty columns
                                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                                # Set gender as the index
                                df.set_index('gender', inplace=True)

                                st.success("Predictions Completed")
                                st.write("Results:")
                                st.dataframe(df)  # Show the DataFrame without index
                                st.download_button(
                                    label="Download Predictions as CSV",
                                    data=df.to_csv(index=True).encode('utf-8'),
                                    file_name='multiple_prediction_results.csv',
                                    mime='text/csv'
                                )
                            else:
                                st.error("Unexpected response format")
                        else:
                            st.error(f"Failed to get a valid response from the API. Status code: {response.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")


# Past Predictions Page
else:
    st.subheader("Past Predictions")
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = st.date_input("End Date", datetime.date.today())
    source = st.selectbox("Prediction Source", ["All", "Scheduled Predictions", "Webapp Predictions"])

    if st.button("Get Past Predictions"):
        try:
            response = requests.get(PAST_PREDICTIONS_API_URL, params={"start_date": start_date, "end_date": end_date, "source": source})

            # Check if the response is empty
            if not response.text.strip():
                st.error("The response from the API is empty.")
                st.stop()  # Stop the execution here

            if response.status_code == 200:
                # Handle JSON response format from the API
                data = response.json()
                if "past_predictions" in data and isinstance(data["past_predictions"], list):
                    past_predictions_df = pd.DataFrame(data["past_predictions"])

                    if not past_predictions_df.empty:
                        st.write("Past Predictions:")
                        st.dataframe(past_predictions_df)
                        st.download_button(
                            label="Download Past Predictions as CSV",
                            data=past_predictions_df.to_csv(index=False).encode('utf-8'),
                            file_name='past_predictions.csv',
                            mime='text/csv'
                        )
                    else:
                        st.warning("No past predictions found for the selected date range and source.")
                else:
                    st.error("Unexpected response format")
            else:
                st.warning("No past predictions found for the selected date range and source.")
        except Exception as e:
            st.error(f"Error: {str(e)}")