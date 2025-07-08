CREATE TABLE IF NOT EXISTS product_transaction (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    financial_product_id BIGINT NOT NULL,
    transaction_type_id BIGINT NOT NULL,
    units DECIMAL(19, 4) NULL,
    unit_value DECIMAL(19, 4) NULL,
    transaction_amount DECIMAL(19, 4) NOT NULL,
    FOREIGN KEY (financial_product_id) REFERENCES financial_product(id),
    FOREIGN KEY (transaction_type_id) REFERENCES transaction_type(id)
);