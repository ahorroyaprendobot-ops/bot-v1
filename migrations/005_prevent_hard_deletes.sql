-- Bloquea borrados físicos de datos principales desde la base de datos.
-- Los códigos se retiran con deleted_at/deleted_by_user_id y las categorías/opciones
-- se archivan con is_active=FALSE; ninguna consulta de usuario debe borrar datos.

CREATE OR REPLACE FUNCTION prevent_hard_delete_core_data()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Hard delete disabled for table %. Archive or retire rows instead.', TG_TABLE_NAME;
END;
$$;

DROP TRIGGER IF EXISTS prevent_hard_delete_promo_codes ON promo_codes;
CREATE TRIGGER prevent_hard_delete_promo_codes
    BEFORE DELETE ON promo_codes
    FOR EACH ROW
    EXECUTE FUNCTION prevent_hard_delete_core_data();

DROP TRIGGER IF EXISTS prevent_hard_delete_categories ON categories;
CREATE TRIGGER prevent_hard_delete_categories
    BEFORE DELETE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION prevent_hard_delete_core_data();

DROP TRIGGER IF EXISTS prevent_hard_delete_subcategories ON subcategories;
CREATE TRIGGER prevent_hard_delete_subcategories
    BEFORE DELETE ON subcategories
    FOR EACH ROW
    EXECUTE FUNCTION prevent_hard_delete_core_data();
