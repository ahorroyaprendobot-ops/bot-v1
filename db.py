import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None


async def get_pool():
    global _pool
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool


async def init_db(database_url: str):
    global _pool

    _pool = await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=5,
        statement_cache_size=0,  # 🔥 CLAVE: evita error de Supabase
    )


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def run_migrations():
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id BIGINT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id SERIAL PRIMARY KEY,
            category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
            code_value TEXT NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_by_user_id BIGINT,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(category_id, code_value)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            user_id BIGINT PRIMARY KEY,
            state TEXT,
            data JSONB DEFAULT '{}'::jsonb,
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """)