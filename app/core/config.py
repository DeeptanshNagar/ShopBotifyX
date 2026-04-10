"""
config.py — Centralized application configuration.

Uses pydantic-settings to load from environment variables and .env files.
All paths, API keys, and tunables live here — nowhere else.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Derived paths ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class Settings(BaseSettings):
    """
    Application settings loaded from environment / .env file.

    Attributes:
        groq_api_key:       API key for the Groq inference service.
        model_name:         LLM model identifier to use.
        max_tool_rounds:    Safety cap on consecutive tool-call loops.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str
    model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_tool_rounds: int = 5


def get_settings() -> Settings:
    """Factory that creates a validated Settings instance."""
    return Settings()
