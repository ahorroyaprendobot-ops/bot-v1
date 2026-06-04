-- Evita que los códigos se borren por cascada al eliminar una categoría u opción.
-- La app ahora archiva categorías/opciones en vez de borrarlas, y estas constraints
-- protegen la BBDD ante DELETE manuales o rutas antiguas que intenten borrar padres.

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'promo_codes'::regclass
      AND confrelid = 'categories'::regclass
      AND contype = 'f'
      AND confdeltype = 'c'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE promo_codes DROP CONSTRAINT %I', constraint_name);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'promo_codes'::regclass
          AND confrelid = 'categories'::regclass
          AND contype = 'f'
    ) THEN
        ALTER TABLE promo_codes
            ADD CONSTRAINT promo_codes_category_id_fkey_no_cascade
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    END IF;
END $$;

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'promo_codes'::regclass
      AND confrelid = 'subcategories'::regclass
      AND contype = 'f'
      AND confdeltype = 'c'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE promo_codes DROP CONSTRAINT %I', constraint_name);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'promo_codes'::regclass
          AND confrelid = 'subcategories'::regclass
          AND contype = 'f'
    ) THEN
        ALTER TABLE promo_codes
            ADD CONSTRAINT promo_codes_subcategory_id_fkey_no_cascade
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE RESTRICT;
    END IF;
END $$;

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'subcategories'::regclass
      AND confrelid = 'categories'::regclass
      AND contype = 'f'
      AND confdeltype = 'c'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE subcategories DROP CONSTRAINT %I', constraint_name);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'subcategories'::regclass
          AND confrelid = 'categories'::regclass
          AND contype = 'f'
    ) THEN
        ALTER TABLE subcategories
            ADD CONSTRAINT subcategories_category_id_fkey_no_cascade
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    END IF;
END $$;
