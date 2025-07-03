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
