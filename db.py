from __future__ import annotations

import asyncpg
from config import settings

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("La base de datos no está conectada")
    return _pool


async def run_migrations() -> None:
    with open("migrations/001_initial.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    async with pool().acquire() as conn:
        await conn.execute(sql)
        if settings.initial_admin_id:
            await conn.execute(
                """
                INSERT INTO admins(telegram_id, name)
                VALUES($1, 'Admin inicial')
                ON CONFLICT (telegram_id) DO NOTHING
                """,
                settings.initial_admin_id,
            )
