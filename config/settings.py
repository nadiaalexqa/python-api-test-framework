"""
Central configuration for the API test framework.

Loads settings from environment variables with sensible defaults.
Local development reads from .env; CI reads from GitHub Secrets.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env for local development. In CI, env vars are already set.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable settings object for the framework."""

    base_url: str
    api_timeout: int
    api_token: str
    environment: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables with safe defaults."""
        return cls(
            base_url=os.getenv("BASE_URL", "https://jsonplaceholder.typicode.com").rstrip("/"),
            api_timeout=int(os.getenv("API_TIMEOUT", "10")),
            api_token=os.getenv("API_TOKEN", ""),
            environment=os.getenv("ENVIRONMENT", "local"),
        )


# Singleton instance — import this in tests when you need settings directly.
settings = Settings.from_env()