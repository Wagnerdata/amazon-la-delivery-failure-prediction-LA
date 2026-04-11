-- ============================================================
-- EDA Queries — Amazon LMRC Delivery Packages
-- Table  : packages  (loaded from data/packages_validation.csv)
-- Failure: damaged_on_arrival = 1  (DELIVERY_ATTEMPTED in source)
-- ============================================================


-- 1. Total Packages and Overall Failure Rate
SELECT
    COUNT(*)                                          AS total_packages,
    SUM(damaged_on_arrival)                           AS total_failures,
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)        AS failure_rate_pct,
    ROUND(AVG(cr_number_missing)  * 100.0, 2)        AS cr_missing_pct,
    ROUND(AVG(double_scan)        * 100.0, 2)        AS double_scan_pct,
    ROUND(AVG(locker_issue)       * 100.0, 2)        AS locker_issue_pct
FROM packages;


-- 2. Failure Rate by Carrier
SELECT
    carrier,
    COUNT(*)                                          AS packages,
    SUM(damaged_on_arrival)                           AS failures,
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)        AS failure_rate_pct,
    ROUND(AVG(route_distance_km), 2)                 AS avg_distance_km
FROM packages
GROUP BY carrier
ORDER BY failure_rate_pct DESC;


-- 3. Failure Rate by Shift
SELECT
    shift,
    COUNT(*)                                          AS packages,
    SUM(damaged_on_arrival)                           AS failures,
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)        AS failure_rate_pct
FROM packages
GROUP BY shift
ORDER BY failure_rate_pct DESC;


-- 4. Failure Rate by Package Type
SELECT
    package_type,
    COUNT(*)                                          AS packages,
    SUM(damaged_on_arrival)                           AS failures,
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)        AS failure_rate_pct
FROM packages
GROUP BY package_type
ORDER BY failure_rate_pct DESC;


-- 5. Average Route Distance and Route Load by Carrier
SELECT
    carrier,
    COUNT(DISTINCT route_distance_km)                 AS unique_routes,
    ROUND(AVG(route_distance_km), 2)                 AS avg_distance_km,
    ROUND(MIN(route_distance_km), 2)                 AS min_distance_km,
    ROUND(MAX(route_distance_km), 2)                 AS max_distance_km,
    ROUND(AVG(packages_in_route), 1)                 AS avg_packages_in_route
FROM packages
GROUP BY carrier
ORDER BY avg_distance_km DESC;


-- 6. Count and Rate of Each Binary Operational Flag
SELECT
    'double_scan'        AS flag,
    SUM(double_scan)     AS flagged_count,
    COUNT(*)             AS total,
    ROUND(AVG(double_scan)        * 100.0, 2) AS flag_rate_pct
FROM packages
UNION ALL
SELECT
    'locker_issue',
    SUM(locker_issue),
    COUNT(*),
    ROUND(AVG(locker_issue)       * 100.0, 2)
FROM packages
UNION ALL
SELECT
    'damaged_on_arrival',
    SUM(damaged_on_arrival),
    COUNT(*),
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)
FROM packages
UNION ALL
SELECT
    'cr_number_missing',
    SUM(cr_number_missing),
    COUNT(*),
    ROUND(AVG(cr_number_missing)  * 100.0, 2)
FROM packages
ORDER BY flagged_count DESC;


-- 7. Failure Rate by Route Distance Bucket
SELECT
    CASE
        WHEN route_distance_km < 40          THEN '1. Under 40 km'
        WHEN route_distance_km BETWEEN 40 AND 60 THEN '2. 40–60 km'
        ELSE                                      '3. Over 60 km'
    END                                           AS distance_bucket,
    COUNT(*)                                      AS packages,
    SUM(damaged_on_arrival)                       AS failures,
    ROUND(AVG(damaged_on_arrival) * 100.0, 2)    AS failure_rate_pct,
    ROUND(AVG(route_distance_km), 2)             AS avg_distance_km
FROM packages
GROUP BY distance_bucket
ORDER BY distance_bucket;
