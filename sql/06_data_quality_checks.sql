SELECT 'airport' AS table_name, COUNT(*) AS row_count
FROM airline_cx_analytics.airport

UNION ALL

SELECT 'customer_journey', COUNT(*)
FROM airline_cx_analytics.customer_journey

UNION ALL

SELECT 'flight_schedule', COUNT(*)
FROM airline_cx_analytics.flight_schedule

UNION ALL

SELECT 'service_case', COUNT(*)
FROM airline_cx_analytics.service_case;