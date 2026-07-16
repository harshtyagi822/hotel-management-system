"""Application configuration.

Loads environment variables and exposes them via a single Config class.
Environment variables must be present (fail-fast on startup).
"""

from __future__ import annotations

import os


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    """Flask configuration."""

    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "20"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))

    # Refresh tokens
    JWT_TOKEN_LOCATION: list[str] = ["headers"]

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "hotel_management")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "hotel_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "hotel_password")

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5500")

    # Debug
    DEBUG: bool = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}



