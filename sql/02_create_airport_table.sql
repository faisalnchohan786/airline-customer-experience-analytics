CREATE EXTERNAL TABLE IF NOT EXISTS airline_cx_analytics.airport (
    airport_code STRING,
    airport_name STRING,
    country STRING,
    region STRING,
    airport_type STRING,
    airport_size_category STRING
)
STORED AS PARQUET
LOCATION 's3://airline-cx-analytics-2026-786/data/airport/';