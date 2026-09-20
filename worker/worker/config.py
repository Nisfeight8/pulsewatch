from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str

    tick_interval_seconds: int = 15
    http_timeout_seconds: float = 10.0
    check_concurrency: int = 20

    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
