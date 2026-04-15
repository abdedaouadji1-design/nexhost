"""
NexHost V6 - Configuration (ClawCloud Ready)
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "NexHost V6"
    APP_VERSION: str = "6.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    HOST: str = "0.0.0.0"
    PORT: int = 5000
    WORKERS: int = 1

    SECRET_KEY: str = "nexhost-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "nexhost-jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SQLite - no external DB needed
    DATABASE_URL: str = "sqlite+aiosqlite:////app/data/nexhost.db"

    # AI APIs
    AI_PRIMARY_URL: str = "https://6946d34b48b4c.xvest3.ru/Deebseek/Deesk.php"
    AI_PRIMARY_KEY: str = "SGR_9C0662AE7979"
    AI_SECONDARY_URL: str = "https://api-rlh33.onrender.com/deepseek_api"
    AI_SECONDARY_KEY: str = "Satan-DeepAI-9D5D05E70B50F7B7F2BDFE80"
    AI_TERTIARY_URL: str = "https://zecora0.serv00.net/deepseek.php"
    AI_MODEL_V3: str = "deepseek chat"
    AI_MODEL_R1: str = "deepseek reasoning"
    AI_TIMEOUT: int = 60
    AI_MAX_RETRIES: int = 3

    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "/app/data/uploads"
    BOTS_DIR: str = "/app/data/bots"
    LOGS_DIR: str = "/app/data/logs"

    DEFAULT_MAX_PYTHON_FILES: int = 10
    DEFAULT_MAX_PHP_FILES: int = 10
    DEFAULT_MAX_READY_BOTS: int = 3

    SUPER_ADMIN_USERNAME: str = "superadmin"
    SUPER_ADMIN_PASSWORD: str = "superadmin123"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
