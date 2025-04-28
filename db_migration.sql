ALTER TABLE contracts
ADD COLUMN signature_method VARCHAR(50),
ADD COLUMN token_email VARCHAR(255),
ADD COLUMN token_expiry TIMESTAMP,
ADD COLUMN certificate_info JSONB;

CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO settings (key, value, created_at, updated_at)
VALUES ('default_signature_method', 'signature_click_only', NOW(), NOW());
