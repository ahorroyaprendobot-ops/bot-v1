from __future__ import annotations

from db import pool


async def create_category(name: str) -> tuple[bool, str]:
    clean = " ".join(name.strip().split())
    if not clean:
        return False, "El nombre no puede estar vacío."
    if len(clean) > 50:
        return False, "El nombre no puede superar 50 caracteres."
    async with pool().acquire() as conn:
        try:
            await conn.execute("INSERT INTO categories(name) VALUES($1)", clean)
            return True, f"Categoría creada: {clean}"
        except Exception:
            return False, "No se ha podido crear. Quizá ya existe una categoría con ese nombre."


async def list_categories(active_only: bool = False) -> list[dict]:
    where = "WHERE is_active = TRUE" if active_only else ""
    async with pool().acquire() as conn:
        rows = await conn.fetch(f"SELECT id, name, is_active, empty_message FROM categories {where} ORDER BY name ASC")
    return [dict(r) for r in rows]


async def get_category(category_id: int) -> dict | None:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, is_active, empty_message FROM categories WHERE id=$1", category_id)
    return dict(row) if row else None


async def set_category_active(category_id: int, active: bool) -> bool:
    async with pool().acquire() as conn:
        result = await conn.execute(
            "UPDATE categories SET is_active=$2, updated_at=NOW() WHERE id=$1", category_id, active
        )
    return result.endswith("1")


async def delete_category(category_id: int) -> bool:
    async with pool().acquire() as conn:
        result = await conn.execute("DELETE FROM categories WHERE id=$1", category_id)
    return result.endswith("1")
