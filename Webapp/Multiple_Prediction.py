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