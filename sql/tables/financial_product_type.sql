CREATE TABLE IF NOT EXISTS financial_product_type AS
    SELECT 1 AS id, 'Stock' AS name
    UNION ALL
    SELECT 2 AS id, 'Bond' AS name
    UNION ALL
    SELECT 3 AS id, 'Investment Fund' AS name
    UNION ALL
    SELECT 4 AS id, 'Exchange-Traded Fund (ETF)' AS name
    UNION ALL
    SELECT 5 AS id, 'Real Estate Investment Trust (REIT)' AS name
    UNION ALL
    SELECT 6 AS id, 'Cryptocurrency' AS name
;