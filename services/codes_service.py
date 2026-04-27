from __future__ import annotations

from db import pool


async def add_codes(category_id: int, raw_text: str) -> dict[str, int]:
    lines = [line.strip() for line in raw_text.splitlines()]
    codes = []
    seen = set()
    empty = 0
    repeated_in_message = 0
    for line in lines:
        if not line:
            empty += 1
            continue
        if line in seen:
            repeated_in_message += 1
            continue
        seen.add(line)
        codes.append(line)

    if len(codes) > 500:
        codes = codes[:500]

    added = 0
    duplicated_db = 0
    async with pool().acquire() as conn:
        for code in codes:
            result = await conn.execute(
                """
                INSERT INTO promo_codes(category_id, code_value)
                VALUES($1, $2)
                ON CONFLICT(category_id, code_value) DO NOTHING
                """,
                category_id,
                code,
            )
            if result.endswith("1"):
                added += 1
            else:
                duplicated_db += 1
        available = await conn.fetchval(
            "SELECT COUNT(*) FROM promo_codes WHERE category_id=$1 AND is_used=FALSE", category_id
        )
    return {
        "added": added,
        "duplicated": duplicated_db + repeated_in_message,
        "empty": empty,
        "available": int(available or 0),
        "limited": 1 if len(seen) > 500 else 0,
    }


async def deliver_code(user_id: int, category_id: int) -> str | None:
    async with pool().acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE promo_codes
                SET is_used=TRUE, used_by_user_id=$1, used_at=NOW()
                WHERE id = (
                    SELECT id
                    FROM promo_codes
                    WHERE category_id=$2 AND is_used=FALSE
                    ORDER BY id ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING code_value
                """,
                user_id,
                category_id,
            )
    return row["code_value"] if row else None


async def stock_summary() -> list[dict]:
    async with pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                c.id,
                c.name,
                c.is_active,
                COUNT(pc.id) FILTER (WHERE pc.is_used=FALSE) AS available,
                COUNT(pc.id) FILTER (WHERE pc.is_used=TRUE) AS used
            FROM categories c
            LEFT JOIN promo_codes pc ON pc.category_id = c.id
            GROUP BY c.id, c.name, c.is_active
            ORDER BY c.name ASC
            """
        )
    return [dict(r) for r in rows]
