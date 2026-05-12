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
    cors_allow_origins: str = Field(
        default="http://localhost:4200,http://127.0.0.1:4200",
        alias="CORS_ALLOW_ORIGINS",
    )

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    enable_redis: bool = Field(default=True, alias="ENABLE_REDIS")

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    default_max_bookable_per_user: int = Field(default=6, alias="DEFAULT_MAX_BOOKABLE_PER_USER")

    hold_duration_minutes: int = Field(default=10, alias="HOLD_DURATION_MINUTES")
    queue_threshold: int = Field(default=200, alias="QUEUE_THRESHOLD")
    queue_batch_size: int = Field(default=50, alias="QUEUE_BATCH_SIZE")
    queue_token_ttl_minutes: int = Field(default=15, alias="QUEUE_TOKEN_TTL_MINUTES")

    embedding_provider: str = Field(default="http", alias="EMBEDDING_PROVIDER")
    embedding_service_url: str = Field(default="http://embedding:80", alias="EMBEDDING_SERVICE_URL")
    embedding_model_name: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", alias="EMBEDDING_MODEL_NAME")
    embedding_timeout_seconds: float = Field(default=5.0, alias="EMBEDDING_TIMEOUT_SECONDS")
    embedding_onnx_model_path: str = Field(default="/models/model.onnx", alias="EMBEDDING_ONNX_MODEL_PATH")
    embedding_onnx_tokenizer_path: str = Field(default="/models/tokenizer.json", alias="EMBEDDING_ONNX_TOKENIZER_PATH")
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    embedding_similarity_threshold: float = Field(default=0.7, alias="EMBEDDING_SIMILARITY_THRESHOLD")

    default_admin_email: str = Field(alias="DEFAULT_ADMIN_EMAIL")
    default_admin_password: str = Field(alias="DEFAULT_ADMIN_PASSWORD")
    default_admin_name: str = Field(alias="DEFAULT_ADMIN_NAME")
    default_user_email: str = Field(alias="DEFAULT_USER_EMAIL")
    default_user_password: str = Field(alias="DEFAULT_USER_PASSWORD")
    default_user_name: str = Field(alias="DEFAULT_USER_NAME")

    @property
    def access_token_ttl_seconds(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def hold_ttl_seconds(self) -> int:
        return self.hold_duration_minutes * 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
