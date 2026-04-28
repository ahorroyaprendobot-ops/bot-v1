-- Añade soporte para dos niveles: categoría principal -> subcategoría/promoción -> códigos.
-- Es idempotente: se puede ejecutar varias veces sin romper nada.

CREATE TABLE IF NOT EXISTS subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, name)
);

ALTER TABLE promo_codes
    ADD COLUMN IF NOT EXISTS subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS promo_codes_subcategory_code_unique
    ON promo_codes(subcategory_id, code_value)
    WHERE subcategory_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS promo_codes_subcategory_available_idx
    ON promo_codes(subcategory_id, is_used);
