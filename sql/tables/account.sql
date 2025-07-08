CREATE TABLE IF NOT EXISTS account (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    account_type_id BIGINT NOT NULL,
    provider_id BIGINT NOT NULL,
    holder_1_id BIGINT NOT NULL,
    holder_2_id BIGINT,
    holder_3_id BIGINT,
    FOREIGN KEY (account_type_id) REFERENCES account_type(id),
    FOREIGN KEY (provider_id) REFERENCES provider(id),
    FOREIGN KEY (holder_1_id) REFERENCES holder(id),
    FOREIGN KEY (holder_2_id) REFERENCES holder(id),
    FOREIGN KEY (holder_3_id) REFERENCES holder(id)
);