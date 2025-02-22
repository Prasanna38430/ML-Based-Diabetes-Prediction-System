import streamlit as st
import pandas as pd
import requests
import datetime
import os
from io import StringIO
# Past Predictions Page

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