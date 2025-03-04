# 1. Open PostgreSQL Command Line
# Connect to PostgreSQL with your username
psql -U postgres

# 2. List all databases in PostgreSQL
# Shows all available databases in your PostgreSQL instance
\l

# 3. Connect to a specific database
# Connect to the database 'diabetes_predictions'
\c diabetes_predictions

# 4. List all tables in the current database
# Displays all tables within the connected database
\dt

# 5. View the structure of a table
# Displays the table structure for 'predictions' table, including column names and data types
\d public.predictions

# 6. View data from a table
# Displays the first 10 rows from the 'predictions' table
SELECT * FROM public.predictions LIMIT 10;

# 7. Exit PostgreSQL Command Line
# Exits the current PostgreSQL session
\q

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
    prediction_date DATE
);
