from __future__ import annotations

import asyncpg
from config import settings
from pathlib import Path

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=1,
            max_size=5,
            statement_cache_size=0,  # Necesario para Supabase Pooler / PgBouncer
        )


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
    migrations_dir = Path("migrations")
    async with pool().acquire() as conn:
        for migration in sorted(migrations_dir.glob("*.sql")):
            sql = migration.read_text(encoding="utf-8")
            if sql.strip():
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
