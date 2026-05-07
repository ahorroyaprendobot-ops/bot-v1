from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    initial_admin_id: int | None = None
    public_base_url: str | None = None
    webhook_secret: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("DATABASE_URL debe ser texto")

        # Evita errores por copiar/pegar comillas o espacios
        cleaned = value.strip().strip('"').strip("'")
        cleaned = re.sub(r"\s+", "", cleaned)

        if not cleaned:
            raise ValueError("DATABASE_URL está vacío")

        parsed = urlsplit(cleaned)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("DATABASE_URL debe empezar por postgres:// o postgresql://")

        if not parsed.hostname:
            raise ValueError("DATABASE_URL no tiene host válido")

        # asyncpg exige esquema postgresql
        scheme = "postgresql"

        # Forzamos sslmode=require para proveedores gestionados (Render/Supabase/Railway)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("sslmode", "require")

        normalized = parsed._replace(scheme=scheme, query=urlencode(query))
        return urlunsplit(normalized)


settings = Settings()
