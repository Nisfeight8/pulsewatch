from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str
    db_echo: bool = False
    
    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 1 day

    # SMTP
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_from_email: str = "noreply@pulsewatch.local"

    email_verification_token_expire_hours: int = 24
    frontend_url: str = "http://localhost:5173"

    # App
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    # Cached so we don't re-parse .env on every request
    return Settings()
