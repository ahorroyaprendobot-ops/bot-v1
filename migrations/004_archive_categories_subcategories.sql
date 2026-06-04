-- Archiva categorías y opciones sin borrarlas físicamente.
-- Los servicios filtran deleted_at IS NULL para que no aparezcan en admin ni usuarios.

ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_by_user_id BIGINT;

ALTER TABLE subcategories
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_by_user_id BIGINT;

ALTER TABLE categories
    DROP CONSTRAINT IF EXISTS categories_name_key;

ALTER TABLE subcategories
    DROP CONSTRAINT IF EXISTS subcategories_category_id_name_key;

CREATE UNIQUE INDEX IF NOT EXISTS categories_lower_name_not_deleted_unique
    ON categories(lower(name))
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS subcategories_category_lower_name_not_deleted_unique
    ON subcategories(category_id, lower(name))
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS categories_not_deleted_idx
    ON categories(id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS subcategories_category_not_deleted_idx
    ON subcategories(category_id, id)
    WHERE deleted_at IS NULL;
