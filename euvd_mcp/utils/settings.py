"""
Application settings using Pydantic Settings.

Loads configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    # EUVD API Configuration
    euvd_base_url: str = "https://euvdservices.enisa.europa.eu"
    euvd_timeout: int = 30
    euvd_max_retries: int = 3

    # User Agent for API Requests
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    class Config:
        """Pydantic settings configuration."""

        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a singleton instance
settings = Settings()
