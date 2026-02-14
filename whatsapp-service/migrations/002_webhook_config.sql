-- migrations/002_webhook_config.sql

CREATE TABLE IF NOT EXISTS webhook_settings (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    retries INTEGER DEFAULT 3,
    secret TEXT, -- Used to sign the payload for security
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert an initial record so the service has a target immediately
-- INSERT INTO webhook_settings (url, retries, secret) 
-- VALUES ('http://localhost:4000/incoming-msg', 3, 'super_secret_key_123');