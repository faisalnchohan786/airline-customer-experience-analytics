SELECT
    CASE
        WHEN disruption_flag = 1 THEN 'Disrupted'
        ELSE 'Not disrupted'
    END AS disruption_status,
    COUNT(*) AS total_journeys,
    ROUND(AVG(overall_satisfaction_score), 2) AS avg_satisfaction,
    ROUND(AVG(recommendation_score), 2) AS avg_recommendation,
    ROUND(
        100.0 * SUM(complaint_flag) / COUNT(*),
        2
    ) AS complaint_rate_percentage
FROM airline_cx_analytics.customer_journey
GROUP BY disruption_flag
ORDER BY disruption_status;