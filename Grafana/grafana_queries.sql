-- Grafana Monitoring SQL Queries
-- For Data Ingestion Quality, Data Drift, and Prediction Monitoring
 
-- ===============================
-- Ingested Data Monitoring Dashboard
-- ===============================
 
-- Invalid Rows Percentage Gauge (Last 10 Minutes)
SELECT
  MAX(created_on) AS "time",
  SUM(invalid_rows)::float / NULLIF(SUM(total_rows), 0) * 100 AS invalid_percentage
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '10 minutes';
 
-- Valid vs Invalid Rows Over Time (Last 10 Records)
SELECT
  created_on AS "time",
  valid_rows,
  invalid_rows
FROM diabetes_data_ingestion_stats
ORDER BY created_on DESC
LIMIT 10;

-- Missing Values Drift Percentage (Last 24 Hours, aggregated every 10 minutes)
SELECT
  date_trunc('minute', created_on) 
    - INTERVAL '1 minute' * (EXTRACT(MINUTE FROM created_on)::int % 10) AS time,
  ROUND(
    (SUM(missing_age + missing_blood_glucose_level + missing_gender + missing_hbA1c_level)::numeric
    / NULLIF(SUM(total_rows), 0)) * 100, 2
  ) AS missing_values_percentage
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '24 hours'
GROUP BY time
ORDER BY time ASC;

-- Error Categories Summary (Last 1 Hour)
SELECT 'Missing Values' AS error_type, 
       SUM(missing_age + missing_blood_glucose_level + missing_gender + missing_hbA1c_level) AS total_errors
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 'Invalid Categories', SUM(invalid_gender)
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 'Out of Range', SUM(age_out_of_range + bmi_out_of_range + median_age_out_of_range + median_bmi_out_of_range)
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 'Wrong Data Types', SUM(invalid_age_type + invalid_blood_glucose_level_type + invalid_bmi_type)
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 'Regex Format Errors', SUM(hbA1c_level_format_errors)
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 'Missing Columns', SUM(missing_heart_disease_column)
FROM diabetes_data_ingestion_stats
WHERE created_on >= NOW() - INTERVAL '1 hour';


-- Missing Values Distribution by Feature (Last 30 Minutes)
SELECT error_type, SUM(error_count) AS total_errors
FROM (
  SELECT created_on, error_type, error_count
  FROM diabetes_data_ingestion_stats,
  LATERAL (VALUES
    ('missing_age', missing_age),
    ('missing_blood_glucose_level', missing_blood_glucose_level),
    ('missing_gender', missing_gender),
    ('missing_hbA1c_level', missing_hbA1c_level),
    ('missing_heart_disease_column', missing_heart_disease_column)
  ) AS errors(error_type, error_count)
  WHERE created_on >= NOW() - INTERVAL '30 minutes'
) AS missing_errors
GROUP BY error_type
ORDER BY total_errors DESC;


-- ===============================
-- Data Drift and Prediction Issues Dashboard
-- ===============================
 
-- Prediction Class Distribution (Last 1 Hour)
SELECT
  diabetes_prediction AS prediction_class,
  COUNT(*) AS count_of_predictions
FROM predictions
WHERE prediction_date >= NOW() - INTERVAL '1 hour'
GROUP BY diabetes_prediction;

-- Model Prediction Confidence Over Time (Last 24 Hours)
SELECT
  date_trunc('minute', prediction_date) + INTERVAL '30 minutes' * FLOOR(EXTRACT(minute FROM prediction_date) / 30) AS "time",
  AVG(prediction_confidence) AS model_prediction_average_confidence
FROM predictions
WHERE prediction_date >= NOW() - INTERVAL '24 hours'
  AND prediction_confidence IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Age Feature Drift vs Training Data (Last 24 Hours)
WITH training_avg AS (
  SELECT AVG(age) AS base_age FROM training_data
),
pred_half_hourly AS (
  SELECT 
    date_trunc('hour', prediction_date) + 
      INTERVAL '1 minute' * (FLOOR(EXTRACT(minute FROM prediction_date) / 30) * 30) AS time,
    AVG(age) AS pred_age
  FROM predictions
  WHERE prediction_date >= NOW() - INTERVAL '24 hours'
  GROUP BY time
)
SELECT 
  p.time,
  100 * (p.pred_age - t.base_age) / t.base_age AS drift_percentage
FROM pred_half_hourly p, training_avg t
ORDER BY p.time;

-- Model Accuracy Over Time (Hourly)
SELECT
  date_trunc('hour', prediction_date) AS hour,
  AVG(CASE WHEN diabetes_prediction = actual_label THEN 1 ELSE 0 END)::float AS accuracy
FROM predictions
GROUP BY hour
ORDER BY hour;
 
