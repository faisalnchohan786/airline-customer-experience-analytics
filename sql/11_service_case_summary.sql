SELECT
    case_type,
    COUNT(*) AS total_cases,

    SUM(
        CASE WHEN case_status = 'Closed'
             THEN 1 ELSE 0
        END
    ) AS closed_cases,

    ROUND(
        AVG(
            CASE WHEN case_status = 'Closed'
                 THEN case_resolution_days
            END
        ),
        2
    ) AS avg_closed_resolution_days,

    ROUND(
        100.0 * SUM(compensation_flag) / COUNT(*),
        2
    ) AS compensation_rate_percentage

FROM airline_cx_analytics.service_case
GROUP BY case_type
ORDER BY total_cases DESC;