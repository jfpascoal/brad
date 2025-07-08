CREATE TABLE IF NOT EXISTS exchange_rate (
    date DATE NOT NULL,
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    exchange_rate DECIMAL(19,4) NOT NULL,
    PRIMARY KEY (date, base_currency, target_currency)
);