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
                st.error(f"Failed to get a valid response from the API. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")  