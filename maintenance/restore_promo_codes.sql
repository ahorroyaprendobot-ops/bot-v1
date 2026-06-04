-- SQL manual para recuperar TODOS los códigos retirados sin volver a cargarlos desde el bot.
--
-- IMPORTANTE:
-- 1) Ejecuta primero los SELECT de comprobación.
-- 2) Este script aplica a TODAS las categorías/opciones.
-- 3) Si quieres aplicarlo solo a una opción concreta, descomenta los filtros
--    `AND pc.subcategory_id = :subcategory_id` y define el id afectado.
-- 4) Si usas psql para una opción concreta, puedes definirlo con: \set subcategory_id 123
-- 5) Si los códigos fueron borrados físicamente con DELETE antes del soft-delete,
--    no se pueden recuperar con UPDATE: hay que restaurarlos desde backup/PITR/logs.
-- 6) El bloque ALTER siguiente prepara la tabla si aún no se había ejecutado
--    la migración 003; evita errores como "column pc.deleted_at does not exist".
-- 7) Un código se puede entregar/ver como stock disponible solo si:
--    is_used = FALSE AND deleted_at IS NULL. Si sigue con is_used = TRUE,
--    está guardado en BBDD, pero NO volverá a salir como disponible en el bot.
--    Para reutilizar todos los usados, usa maintenance/make_all_promo_codes_available.sql.

ALTER TABLE promo_codes
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_by_user_id BIGINT;

CREATE INDEX IF NOT EXISTS promo_codes_subcategory_active_available_idx
    ON promo_codes(subcategory_id, is_used, id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS promo_codes_subcategory_deleted_idx
    ON promo_codes(subcategory_id, deleted_at)
    WHERE deleted_at IS NOT NULL;

BEGIN;

-- Comprobar estado actual antes de tocar nada, agrupado por categoría y opción.
SELECT
    c.id AS category_id,
    c.name AS category_name,
    s.id AS subcategory_id,
    s.name AS subcategory_name,
    COUNT(pc.id) FILTER (WHERE pc.is_used = FALSE AND pc.deleted_at IS NULL) AS visibles_disponibles_para_bot,
    COUNT(pc.id) FILTER (WHERE pc.is_used = TRUE AND pc.deleted_at IS NULL) AS guardados_no_visibles_por_usados,
    COUNT(pc.id) FILTER (WHERE pc.deleted_at IS NOT NULL) AS retirados_por_admin
FROM promo_codes pc
JOIN subcategories s ON s.id = pc.subcategory_id
JOIN categories c ON c.id = s.category_id
-- AND pc.subcategory_id = :subcategory_id
GROUP BY c.id, c.name, s.id, s.name
ORDER BY c.name ASC, s.name ASC;

-- Opción segura: recuperar TODOS los códigos retirados por admin para que vuelvan al stock.
-- No reutiliza códigos ya entregados a usuarios.
UPDATE promo_codes pc
SET deleted_at = NULL,
    deleted_by_user_id = NULL
WHERE pc.deleted_at IS NOT NULL
  AND pc.is_used = FALSE
-- AND pc.subcategory_id = :subcategory_id
;

-- Opción excepcional: volver a poner como disponibles códigos ya entregados/usados.
-- Úsala solo si esos códigos NO deberían considerarse consumidos.
-- Por defecto aplica a TODOS; añade el filtro de subcategory_id si necesitas limitarlo.
-- UPDATE promo_codes pc
-- SET is_used = FALSE,
--     used_by_user_id = NULL,
--     used_at = NULL,
--     deleted_at = NULL,
--     deleted_by_user_id = NULL
-- WHERE pc.is_used = TRUE
-- AND pc.subcategory_id = :subcategory_id
-- ;

-- Verificar el resultado antes de confirmar, agrupado por categoría y opción.
SELECT
    c.id AS category_id,
    c.name AS category_name,
    s.id AS subcategory_id,
    s.name AS subcategory_name,
    COUNT(pc.id) FILTER (WHERE pc.is_used = FALSE AND pc.deleted_at IS NULL) AS visibles_disponibles_para_bot,
    COUNT(pc.id) FILTER (WHERE pc.is_used = TRUE AND pc.deleted_at IS NULL) AS guardados_no_visibles_por_usados,
    COUNT(pc.id) FILTER (WHERE pc.deleted_at IS NOT NULL) AS retirados_por_admin
FROM promo_codes pc
JOIN subcategories s ON s.id = pc.subcategory_id
JOIN categories c ON c.id = s.category_id
-- AND pc.subcategory_id = :subcategory_id
GROUP BY c.id, c.name, s.id, s.name
ORDER BY c.name ASC, s.name ASC;

-- Si el resultado es correcto:
COMMIT;

-- Si el resultado NO es correcto, cambia COMMIT por ROLLBACK antes de ejecutar.
-- ROLLBACK;
