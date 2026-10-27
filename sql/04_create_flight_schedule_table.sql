CREATE EXTERNAL TABLE IF NOT EXISTS airline_cx_analytics.flight_schedule (
    flight_instance_id STRING,
    flight_date DATE,
    flight_number STRING,
    route STRING,
    origin_airport STRING,
    destination_airport STRING,
    scheduled_departure_time STRING,
    scheduled_arrival_time STRING,
    aircraft_type STRING,
    haul_category STRING,
    distance_km_estimate INT
)
STORED AS PARQUET
LOCATION 's3://airline-cx-analytics-2026-786/data/flight_schedule/';