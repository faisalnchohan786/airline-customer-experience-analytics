SELECT
    CASE
        WHEN baggage_issue_flag = 1 THEN 'Baggage issue'
        ELSE 'No baggage issue'
    END AS baggage_status,

    COUNT(*) AS total_journeys,

    ROUND(
        AVG(overall_satisfaction_score), 2
    ) AS avg_satisfaction,
    
        ROUND(
        CAST(SUM(complaint_flag) AS DOUBLE)
        / COUNT(*) * 100,
        2
    ) AS complaint_rate_percentage

FROM airline_cx_analytics.customer_journey

GROUP BY baggage_issue_flag

ORDER BY baggage_issue_flag;