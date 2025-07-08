CREATE TABLE IF NOT EXISTS account_type AS
    SELECT 1 AS id, 'Checking' AS name
    UNION ALL
    SELECT 2 AS id, 'Savings' AS name
    UNION ALL
    SELECT 3 AS id, 'Credit Card' AS name
    UNION ALL
    SELECT 4 AS id, 'Investment' AS name
    UNION ALL
    SELECT 5 AS id, 'Loan' AS name
    UNION ALL
    SELECT 6 AS id, 'Mortgage' AS name
    UNION ALL
    SELECT 7 AS id, 'Cash' AS name
    UNION ALL
    SELECT 8 AS id, 'Other' AS name
;