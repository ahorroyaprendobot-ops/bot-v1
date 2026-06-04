-- SQL manual para que TODOS los códigos existentes vuelvan a estar visibles/disponibles en el bot.
--
-- IMPORTANTE:
-- - Un código se puede entregar/ver como stock disponible solo si:
--   is_used = FALSE AND deleted_at IS NULL.
-- - Si is_used = TRUE, el código está guardado en BBDD, pero el bot NO lo considera disponible.
-- - Ejecuta este script solo si quieres reutilizar también códigos ya entregados a usuarios.
-- - Esto no recupera filas borradas físicamente con DELETE; para eso hace falta backup/PITR/logs.

ALTER TABLE promo_codes
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_by_user_id BIGINT;

BEGIN;

-- Ver estado antes de cambiar nada.
SELECT
    COUNT(*) AS total_en_bbdd,
    COUNT(*) FILTER (WHERE is_used = FALSE AND deleted_at IS NULL) AS visibles_disponibles_para_bot,
    COUNT(*) FILTER (WHERE is_used = TRUE) AS no_visibles_por_is_used_true,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) AS no_visibles_por_retirados_admin
FROM promo_codes;

-- Dejar TODOS los códigos existentes como visibles/disponibles para el bot.
UPDATE promo_codes
SET is_used = FALSE,
    used_by_user_id = NULL,
    used_at = NULL,
    deleted_at = NULL,
    deleted_by_user_id = NULL;

-- Ver estado después de cambiar todo.
SELECT
    COUNT(*) AS total_en_bbdd,
    COUNT(*) FILTER (WHERE is_used = FALSE AND deleted_at IS NULL) AS visibles_disponibles_para_bot,
    COUNT(*) FILTER (WHERE is_used = TRUE) AS no_visibles_por_is_used_true,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) AS no_visibles_por_retirados_admin
FROM promo_codes;

-- Si el resultado es correcto:
COMMIT;

-- Si el resultado NO es correcto, cambia COMMIT por ROLLBACK antes de ejecutar.
-- ROLLBACK;
