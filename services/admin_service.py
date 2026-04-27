from __future__ import annotations

from db import pool


async def is_admin(user_id: int) -> bool:
    async with pool().acquire() as conn:
        return bool(await conn.fetchval("SELECT 1 FROM admins WHERE telegram_id=$1", user_id))


async def add_admin(user_id: int, name: str | None = None) -> None:
    async with pool().acquire() as conn:
        await conn.execute(
            "INSERT INTO admins(telegram_id, name) VALUES($1, $2) ON CONFLICT DO NOTHING",
            user_id,
            name,
        )
