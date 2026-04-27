CREATE TABLE IF NOT EXISTS admins (
    telegram_id BIGINT PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    empty_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS promo_codes (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    code_value TEXT NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    used_by_user_id BIGINT,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, code_value)
);

CREATE INDEX IF NOT EXISTS idx_promo_codes_available
ON promo_codes(category_id, is_used, id);

CREATE TABLE IF NOT EXISTS user_states (
    user_id BIGINT PRIMARY KEY,
    state TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP DEFAULT NOW()
);
