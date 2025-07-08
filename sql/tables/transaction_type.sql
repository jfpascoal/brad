CREATE TABLE IF NOT EXISTS transaction_type AS
    SELECT 1 AS id, 'Purchase' AS name
    UNION ALL
    SELECT 2 AS id, 'Sale' AS name
    UNION ALL
    SELECT 3 AS id, 'Dividend' AS name
    UNION ALL
    SELECT 4 AS id, 'Interest' AS name
    UNION ALL
    SELECT 5 AS id, 'Fee' AS name
    UNION ALL
    SELECT 6 AS id, 'Transfer' AS name
;