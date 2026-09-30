from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
            env_file=".env",
            env_ignore_empty=True,
            extra="ignore",
        )

    DEBUG: bool = False

    # Database
    DB_ENGINE: str = "postgresql+asyncpg"
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    ECHO: bool = False
    ECHO_POOL: bool = False
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    POOL_PRE_PING: bool = True

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Uvicorn
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000
    WS_MAX_SIZE: int = 65536
    WORKERS: int | None = None
    LIMIT_CONCURRENCY: int | None = 1000

    # Security
    JWT_ACCESS_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    ALLOW_ORIGINS: list[str]
    ALLOW_CREDENTIALS: bool
    ALLOW_METHODS: list[str]
    ALLOW_HEADERS: list[str]

    # S3 Storage
    S3_ENDPOINT: str
    S3_REGION: str = "default"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_PRIVATE_BUCKET: str
    S3_PUBLIC_BUCKET: str
    S3_BASE_URL: str
    S3_TTL: int = 300

    MAX_AVATAR_SIZE: int
    MAX_ATTACHMENT_SIZE: int

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @field_validator("MAX_ATTACHMENT_SIZE", "MAX_AVATAR_SIZE", mode="before")
    @classmethod
    def convert_mb_to_bytes(cls, value: int) -> int:
        return int(value) * 1024 * 1024


settings = Settings() # type: ignore
