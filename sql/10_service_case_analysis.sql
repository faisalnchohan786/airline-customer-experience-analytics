SELECT
    case_type,
    case_status,
    COUNT(*) AS total_cases,
    ROUND(
        AVG(case_resolution_days),
        2
    ) AS avg_resolution_days,
    
    ROUND(
        CAST(SUM(compensation_flag) AS DOUBLE)
        / COUNT(*) * 100,
        2
    ) AS compensation_rate_percentage
    
FROM airline_cx_analytics.service_case
GROUP BY case_type, case_status
ORDER BY case_type, case_status;