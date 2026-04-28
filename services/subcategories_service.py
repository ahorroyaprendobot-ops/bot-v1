from __future__ import annotations

from db import pool


async def create_subcategory(category_id: int, name: str) -> tuple[bool, str, int | None]:
    clean = " ".join(name.strip().split())
    if not clean:
        return False, "El nombre no puede estar vacío.", None
    if clean.startswith("/"):
        return False, "Ese texto parece un comando. Escribe solo el nombre.", None
    if len(clean) > 50:
        return False, "El nombre no puede superar 50 caracteres.", None

    async with pool().acquire() as conn:
        category = await conn.fetchrow("SELECT id FROM categories WHERE id=$1", category_id)
        if not category:
            return False, "La categoría principal ya no existe.", None

        existing = await conn.fetchrow(
            "SELECT id FROM subcategories WHERE category_id=$1 AND lower(name)=lower($2)",
            category_id,
            clean,
        )
        if existing:
            return False, f"Ya existe una opción llamada: {clean}", int(existing["id"])

        row = await conn.fetchrow(
            "INSERT INTO subcategories(category_id, name) VALUES($1, $2) RETURNING id",
            category_id,
            clean,
        )
        return True, f"Opción creada: {clean}", int(row["id"])


async def list_subcategories(category_id: int, active_only: bool = False) -> list[dict]:
    where_active = "AND s.is_active = TRUE" if active_only else ""
    async with pool().acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT s.id, s.category_id, s.name, s.is_active, c.name AS category_name, c.is_active AS category_active
            FROM subcategories s
            JOIN categories c ON c.id = s.category_id
            WHERE s.category_id=$1 {where_active}
            ORDER BY s.name ASC
            """,
            category_id,
        )
    return [dict(r) for r in rows]


async def get_subcategory(subcategory_id: int) -> dict | None:
    async with pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.id, s.category_id, s.name, s.is_active, c.name AS category_name, c.is_active AS category_active, c.empty_message
            FROM subcategories s
            JOIN categories c ON c.id = s.category_id
            WHERE s.id=$1
            """,
            subcategory_id,
        )
    return dict(row) if row else None


async def set_subcategory_active(subcategory_id: int, active: bool) -> bool:
    async with pool().acquire() as conn:
        result = await conn.execute(
            "UPDATE subcategories SET is_active=$2, updated_at=NOW() WHERE id=$1",
            subcategory_id,
            active,
        )
    return result.endswith("1")


async def delete_subcategory(subcategory_id: int) -> bool:
    async with pool().acquire() as conn:
        result = await conn.execute("DELETE FROM subcategories WHERE id=$1", subcategory_id)
    return result.endswith("1")
