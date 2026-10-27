SELECT
    booking_channel,
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
    ) AS complaint_rate_percentage

FROM airline_cx_analytics.customer_journey

GROUP BY booking_channel

ORDER BY avg_satisfaction DESC;