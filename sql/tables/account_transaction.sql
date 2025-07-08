CREATE TABLE IF NOT EXISTS account_transaction (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    account_id BIGINT NOT NULL,
    transaction_type_id BIGINT NOT NULL,
    transaction_amount DECIMAL(19,4) NOT NULL,
    description TEXT NULL,
    FOREIGN KEY (account_id) REFERENCES account(id),
    FOREIGN KEY (transaction_type_id) REFERENCES transaction_type(id)
);