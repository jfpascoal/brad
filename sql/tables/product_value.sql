CREATE TABLE IF NOT EXISTS product_value (
    date DATE NOT NULL,
    financial_product_id BIGINT NOT NULL,
    current_value DECIMAL(19, 4) NOT NULL,
    units DECIMAL(19, 4) NULL,
    unit_value DECIMAL(19, 4) NULL,
    PRIMARY KEY (date, financial_product_id),
    FOREIGN KEY (financial_product_id) REFERENCES financial_product(id)
);