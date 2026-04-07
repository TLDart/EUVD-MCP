"""
Application settings using Pydantic Settings.

Loads configuration from environment variables and .env file.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application Configuration
    # Transport mode: "http" for standalone/Docker, "stdio" for subprocess (e.g. Claude Desktop)
    transport: str = "http"
    host: str = "127.0.0.1"
    port: int = 8000

    # EUVD API Configuration
    euvd_base_url: str = "https://euvdservices.enisa.europa.eu"
    euvd_timeout: int = 30
    euvd_max_retries: int = 3

    # Cache TTL in seconds for the latest/exploited/critical endpoints
    cache_ttl: int = 30
    # Maximum number of entries in the response cache
    cache_max_size: int = 128

    # Logging level (DEBUG, INFO, WARNING, ERROR)
    log_level: str = "INFO"

    # User Agent for API Requests
    user_agent: str = "euvd-mcp-tool"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Create a singleton instance
settings = Settings()
