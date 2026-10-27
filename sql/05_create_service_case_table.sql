CREATE EXTERNAL TABLE IF NOT EXISTS airline_cx_analytics.service_case (
    case_id STRING,
    journey_id STRING,
    case_type STRING,
    case_open_date DATE,
    case_resolution_days DOUBLE,
    case_status STRING,
    compensation_flag INT
)
STORED AS PARQUET
LOCATION 's3://airline-cx-analytics-2026-786/data/service_case/';