-- migrations/001_initial_schema.sql

CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id SERIAL PRIMARY KEY,
    whatsapp_id TEXT UNIQUE,
    from_number TEXT,
    body TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_from_me BOOLEAN
);

-- You can add more tables here later
-- CREATE TABLE IF NOT EXISTS users (...);