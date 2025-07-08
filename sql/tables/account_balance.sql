CREATE TABLE IF NOT EXISTS account_balance (
    date DATE NOT NULL,
    account_id BIGINT NOT NULL,
    balance DECIMAL(19,4) NOT NULL,
    PRIMARY KEY (date, account_id),
    FOREIGN KEY (account_id) REFERENCES account(id)
);