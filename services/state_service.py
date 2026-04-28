from __future__ import annotations

import json
from typing import Any

from db import pool


def _normalise_jsonb(value: Any) -> dict[str, Any]:
    """Convierte de forma segura el valor JSONB devuelto por asyncpg.

    En Supabase/asyncpg puede llegar como dict, str JSON, bytes o incluso valor antiguo
    mal guardado. Nunca debe romper /start ni /cancelar.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except Exception:
            return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    try:
        return dict(value)
    except Exception:
        return {}


async def set_state(user_id: int, state: str, data: dict[str, Any] | None = None) -> None:
    async with pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_states(user_id, state, data, updated_at)
            VALUES($1, $2, $3::jsonb, NOW())
            ON CONFLICT(user_id)
            DO UPDATE SET state=$2, data=$3::jsonb, updated_at=NOW()
            """,
            user_id,
            state,
            json.dumps(data or {}),
        )


async def get_state(user_id: int) -> dict[str, Any] | None:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT state, data FROM user_states WHERE user_id=$1", user_id)
    if not row:
        return None
    return {"state": row["state"], "data": _normalise_jsonb(row["data"])}


async def clear_state(user_id: int) -> None:
    async with pool().acquire() as conn:
        await conn.execute("DELETE FROM user_states WHERE user_id=$1", user_id)


async def reset_state(user_id: int) -> None:
    await clear_state(user_id)
