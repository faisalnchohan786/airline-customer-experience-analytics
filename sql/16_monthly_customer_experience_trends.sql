SELECT
    DATE_TRUNC('month', flight_date) AS flight_month,
    COUNT(*) AS total_journeys,

    ROUND(
        AVG(overall_satisfaction_score), 2
    ) AS avg_satisfaction,

    ROUND(
        AVG(recommendation_score), 2
    ) AS avg_recommendation,

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

GROUP BY DATE_TRUNC('month', flight_date)

ORDER BY flight_month;