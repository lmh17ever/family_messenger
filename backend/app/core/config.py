from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
            env_file=".env",
            env_ignore_empty=True,
            extra="ignore",
        )
    DATABASE_URL: str

    # Security
    JWT_SECRET_KEY: str
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
    ECHO_SQL: bool = False

    MAX_AVATAR_SIZE: int
    MAX_ATTACHMENT_SIZE: int

    @field_validator("MAX_ATTACHMENT_SIZE", "MAX_AVATAR_SIZE", mode="before")
    @classmethod
    def convert_mb_to_bytes(cls, value: int) -> int:
        return int(value) * 1024 * 1024


settings = Settings() # type: ignore
