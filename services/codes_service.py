from __future__ import annotations

from db import pool


async def add_codes(subcategory_id: int, raw_text: str) -> dict[str, int]:
    lines = [line.strip() for line in raw_text.splitlines()]
    codes: list[str] = []
    seen = set()
    empty = 0
    repeated_in_message = 0
    original_unique_count = 0

    for line in lines:
        if not line:
            empty += 1
            continue
        if line in seen:
            repeated_in_message += 1
            continue
        seen.add(line)
        original_unique_count += 1
        codes.append(line)

    limited = original_unique_count > 500
    if limited:
        codes = codes[:500]

    added = 0
    duplicated_db = 0
    async with pool().acquire() as conn:
        subcategory = await conn.fetchrow("SELECT category_id FROM subcategories WHERE id=$1", subcategory_id)
        if not subcategory:
            return {"added": 0, "duplicated": 0, "empty": empty, "available": 0, "limited": int(limited)}

        category_id = int(subcategory["category_id"])
        for code in codes:
            result = await conn.execute(
                """
                INSERT INTO promo_codes(category_id, subcategory_id, code_value)
                VALUES($1, $2, $3)
                ON CONFLICT DO NOTHING
                """,
                category_id,
                subcategory_id,
                code,
            )
            if result.endswith("1"):
                added += 1
            else:
                duplicated_db += 1

        available = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM promo_codes
            WHERE subcategory_id=$1 AND is_used=FALSE AND deleted_at IS NULL
            """,
            subcategory_id,
        )

    return {
        "added": added,
        "duplicated": duplicated_db + repeated_in_message,
        "empty": empty,
        "available": int(available or 0),
        "limited": int(limited),
    }


async def deliver_code(user_id: int, subcategory_id: int) -> str | None:
    # Consultar/entregar un código a un usuario no debe consumirlo ni ocultarlo del stock.
    # Solo los administradores lo retiran explícitamente con deleted_at/deleted_by_user_id.
    async with pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT code_value
            FROM promo_codes
            WHERE subcategory_id=$1 AND is_used=FALSE AND deleted_at IS NULL
            ORDER BY id ASC
            LIMIT 1
            """,
            subcategory_id,
        )
    return row["code_value"] if row else None


async def stock_summary() -> list[dict]:
    async with pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                c.id AS category_id,
                c.name AS category_name,
                c.is_active AS category_active,
                s.id AS subcategory_id,
                s.name AS subcategory_name,
                s.is_active AS subcategory_active,
                COUNT(pc.id) FILTER (WHERE pc.is_used=FALSE AND pc.deleted_at IS NULL) AS available,
                COUNT(pc.id) FILTER (WHERE pc.is_used=TRUE AND pc.deleted_at IS NULL) AS used,
                COUNT(pc.id) FILTER (WHERE pc.deleted_at IS NOT NULL) AS deleted
            FROM categories c
            LEFT JOIN subcategories s ON s.category_id = c.id
            LEFT JOIN promo_codes pc ON pc.subcategory_id = s.id
            GROUP BY c.id, c.name, c.is_active, s.id, s.name, s.is_active
            ORDER BY c.name ASC, s.name ASC
            """
        )
    return [dict(r) for r in rows]


async def delete_codes_by_subcategory(subcategory_id: int, admin_user_id: int) -> int:
    async with pool().acquire() as conn:
        deleted = await conn.fetchval(
            """
            WITH removed AS (
                UPDATE promo_codes
                SET deleted_at=NOW(), deleted_by_user_id=$2
                WHERE subcategory_id=$1 AND deleted_at IS NULL
                RETURNING 1
            )
            SELECT COUNT(*) FROM removed
            """,
            subcategory_id,
            admin_user_id,
        )
    return int(deleted or 0)
