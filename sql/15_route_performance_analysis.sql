SELECT
    route,
    origin_airport,
    destination_airport,
    COUNT(*) AS total_journeys,

    ROUND(
        AVG(overall_satisfaction_score), 2
    ) AS avg_satisfaction,

    ROUND(
        CAST(SUM(complaint_flag) AS DOUBLE)
        / COUNT(*) * 100,
        2
    ) AS complaint_rate_percentage,

    ROUND(
        CAST(SUM(disruption_flag) AS DOUBLE)
        / COUNT(*) * 100,
        2
    ) AS disruption_rate_percentage

FROM airline_cx_analytics.customer_journey

GROUP BY
    route,
    origin_airport,
    destination_airport

HAVING COUNT(*) >= 200

ORDER BY
    avg_satisfaction ASC,
    complaint_rate_percentage DESC;