SELECT
    CASE
        WHEN delay_minutes = 0 THEN '0. On time'
        WHEN delay_minutes <= 15 THEN '1. 1–15 minutes'
        WHEN delay_minutes <= 60 THEN '2. 16–60 minutes'
        ELSE '3. Over 60 minutes'
    END AS delay_band,

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

GROUP BY
    CASE
        WHEN delay_minutes = 0 THEN '0. On time'
        WHEN delay_minutes <= 15 THEN '1. 1–15 minutes'
        WHEN delay_minutes <= 60 THEN '2. 16–60 minutes'
        ELSE '3. Over 60 minutes'
    END

ORDER BY delay_band;