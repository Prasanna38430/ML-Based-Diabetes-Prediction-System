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
                        response = requests.post(PREDICTION_API_URL, json={"data": data_payload})
                        
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