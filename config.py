from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    initial_admin_id: int | None = None
    public_base_url: str | None = None
    webhook_secret: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
