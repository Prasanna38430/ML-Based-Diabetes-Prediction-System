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