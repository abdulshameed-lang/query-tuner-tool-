"""Application configuration."""

from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import json


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Query Tuner Tool"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # API
    api_version: str = "v1"
    allowed_hosts: Union[List[str], str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )

    @field_validator('allowed_hosts', 'cors_origins', mode='before')
    @classmethod
    def parse_list(cls, v):
        """Parse list from string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [s.strip() for s in v.split(',') if s.strip()]
        return v

    # Oracle Database
    oracle_user: str = Field(default="", env="ORACLE_USER")
    oracle_password: str = Field(default="", env="ORACLE_PASSWORD")
    oracle_dsn: str = Field(default="", env="ORACLE_DSN")
    oracle_min_pool_size: int = Field(default=5, env="ORACLE_MIN_POOL_SIZE")
    oracle_max_pool_size: int = Field(default=20, env="ORACLE_MAX_POOL_SIZE")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # Security
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    jwt_secret: str = Field(default="change-me-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, env="JWT_EXPIRE_MINUTES")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Don't fail if .env file doesn't exist (Railway doesn't have one)
        extra = "ignore"


# Global settings instance
settings = Settings()
