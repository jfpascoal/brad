CREATE TABLE IF NOT EXISTS financial_product (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    financial_product_type_id BIGINT NOT NULL,
    currency TEXT NOT NULL,
    provider_id BIGINT NOT NULL,
    holder_id BIGINT NOT NULL,
    ticker TEXT NULL,
    isin TEXT NULL,
    FOREIGN KEY (financial_product_type_id) REFERENCES financial_product_type(id),
    FOREIGN KEY (provider_id) REFERENCES provider(id),
    FOREIGN KEY (holder_id) REFERENCES holder(id)
);
