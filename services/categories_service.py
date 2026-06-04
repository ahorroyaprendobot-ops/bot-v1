from __future__ import annotations

from db import pool


async def create_category(name: str) -> tuple[bool, str, int | None]:
    clean = " ".join(name.strip().split())
    if not clean:
        return False, "El nombre no puede estar vacío.", None
    if clean.startswith("/"):
        return False, "Ese texto parece un comando. Escribe solo el nombre de la categoría.", None
    if len(clean) > 50:
        return False, "El nombre no puede superar 50 caracteres.", None

    async with pool().acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM categories WHERE lower(name)=lower($1) AND deleted_at IS NULL",
            clean,
        )
        if existing:
            return False, f"Ya existe una categoría llamada: {clean}", int(existing["id"])

        row = await conn.fetchrow("INSERT INTO categories(name) VALUES($1) RETURNING id", clean)
        return True, f"Categoría creada: {clean}", int(row["id"])


async def list_categories(active_only: bool = False) -> list[dict]:
    filters = ["deleted_at IS NULL"]
    if active_only:
        filters.append("is_active = TRUE")
    where = "WHERE " + " AND ".join(filters)
    async with pool().acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, name, is_active, empty_message FROM categories {where} ORDER BY name ASC"
        )
    return [dict(r) for r in rows]


async def get_category(category_id: int) -> dict | None:
    async with pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, is_active, empty_message FROM categories WHERE id=$1 AND deleted_at IS NULL",
            category_id,
        )
    return dict(row) if row else None


async def set_category_active(category_id: int, active: bool) -> bool:
    async with pool().acquire() as conn:
        result = await conn.execute(
            "UPDATE categories SET is_active=$2, updated_at=NOW() WHERE id=$1 AND deleted_at IS NULL",
            category_id,
            active,
        )
    return result.endswith("1")


async def delete_category(category_id: int, admin_user_id: int) -> bool:
    async with pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute(
                """
                UPDATE categories
                SET is_active=FALSE, deleted_at=NOW(), deleted_by_user_id=$2, updated_at=NOW()
                WHERE id=$1 AND deleted_at IS NULL
                """,
                category_id,
                admin_user_id,
            )
            await conn.execute(
                """
                UPDATE subcategories
                SET is_active=FALSE, deleted_at=NOW(), deleted_by_user_id=$2, updated_at=NOW()
                WHERE category_id=$1 AND deleted_at IS NULL
                """,
                category_id,
                admin_user_id,
            )
            await conn.execute(
                """
                UPDATE promo_codes
                SET deleted_at=NOW(), deleted_by_user_id=$2
                WHERE category_id=$1 AND deleted_at IS NULL
                """,
                category_id,
                admin_user_id,
            )
    return result.endswith("1")
