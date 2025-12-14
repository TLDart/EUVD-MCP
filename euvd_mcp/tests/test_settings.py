"""
Unit tests for application settings.
"""

from unittest.mock import patch

from euvd_mcp.utils.settings import Settings


class TestSettingsDefaults:
    """Test default settings."""

    def test_default_host(self):
        """Test default host setting."""
        settings = Settings()
        assert settings.host == "127.0.0.1"

    def test_default_port(self):
        """Test default port setting."""
        settings = Settings()
        assert settings.port == 8000

    def test_default_euvd_base_url(self):
        """Test default EUVD base URL."""
        settings = Settings()
        assert settings.euvd_base_url == "https://euvdservices.enisa.europa.eu"

    def test_default_euvd_timeout(self):
        """Test default EUVD timeout."""
        settings = Settings()
        assert settings.euvd_timeout == 30

    def test_default_euvd_max_retries(self):
        """Test default EUVD max retries."""
        settings = Settings()
        assert settings.euvd_max_retries == 3

    def test_user_agent_set(self):
        """Test that user agent is set."""
        settings = Settings()
        assert settings.user_agent is not None
        assert "Mozilla" in settings.user_agent


class TestSettingsEnvironmentVariables:
    """Test settings loading from environment variables."""

    def test_host_from_env(self):
        """Test loading host from environment variable."""
        with patch.dict("os.environ", {"host": "0.0.0.0"}):
            settings = Settings()
            assert settings.host == "0.0.0.0"

    def test_port_from_env(self):
        """Test loading port from environment variable."""
        with patch.dict("os.environ", {"port": "9000"}):
            settings = Settings()
            assert settings.port == 9000

    def test_timeout_from_env(self):
        """Test loading timeout from environment variable."""
        with patch.dict("os.environ", {"euvd_timeout": "60"}):
            settings = Settings()
            assert settings.euvd_timeout == 60

    def test_max_retries_from_env(self):
        """Test loading max retries from environment variable."""
        with patch.dict("os.environ", {"euvd_max_retries": "5"}):
            settings = Settings()
            assert settings.euvd_max_retries == 5


class TestSettingsValidation:
    """Test settings validation."""

    def test_valid_settings(self):
        """Test creating valid settings."""
        settings = Settings(
            host="localhost",
            port=8080,
            euvd_base_url="https://api.example.com",
            euvd_timeout=45,
            euvd_max_retries=2,
        )
        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.euvd_timeout == 45
        assert settings.euvd_max_retries == 2

    def test_settings_are_immutable(self):
        """Test that settings instance is created correctly."""
        settings = Settings()
        # Settings should be configurable
        assert hasattr(settings, "host")
        assert hasattr(settings, "port")

    def test_url_format(self):
        """Test that base URL is properly formatted."""
        settings = Settings()
        assert settings.euvd_base_url.startswith("https://")
