-- Mantiene los códigos en bbdd cuando se retiran del stock desde admin.
-- Las entregas a usuarios siguen marcándose con is_used/used_at, nunca se borran.

ALTER TABLE promo_codes
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_by_user_id BIGINT;

CREATE INDEX IF NOT EXISTS promo_codes_subcategory_active_available_idx
    ON promo_codes(subcategory_id, is_used, id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS promo_codes_subcategory_deleted_idx
    ON promo_codes(subcategory_id, deleted_at)
    WHERE deleted_at IS NOT NULL;
