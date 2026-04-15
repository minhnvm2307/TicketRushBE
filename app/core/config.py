from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="TicketRush API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    enable_redis: bool = Field(default=True, alias="ENABLE_REDIS")

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    hold_duration_minutes: int = Field(default=10, alias="HOLD_DURATION_MINUTES")
    queue_threshold: int = Field(default=200, alias="QUEUE_THRESHOLD")
    queue_batch_size: int = Field(default=50, alias="QUEUE_BATCH_SIZE")
    queue_token_ttl_minutes: int = Field(default=15, alias="QUEUE_TOKEN_TTL_MINUTES")

    default_admin_email: str = Field(alias="DEFAULT_ADMIN_EMAIL")
    default_admin_password: str = Field(alias="DEFAULT_ADMIN_PASSWORD")
    default_admin_name: str = Field(alias="DEFAULT_ADMIN_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()
