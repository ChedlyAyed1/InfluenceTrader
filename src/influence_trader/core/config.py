from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InfluenceTrader"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-20b"
    groq_timeout_seconds: float = 20.0

    x_accounts_db_path: Path = Path("data/twscrape/accounts.db")
    x_poll_limit_per_handle: int = 5
    x_twscrape_enable_xclid_workaround: bool = True
    x_twscrape_ondemand_script_url: str = (
        "https://abs.twimg.com/responsive-web/client-web/ondemand.s.2507f89a.js"
    )
    x_default_handles: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "realDonaldTrump",
            "elonmusk",
            "warrenbuffett",
            "jeromepowell",
        ]
    )
    x_account_username: str | None = None
    x_account_password: str | None = None
    x_account_email: str | None = None
    x_account_email_password: str | None = None
    x_account_cookies: str | None = None

    relevance_keywords: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "tariff",
            "sanction",
            "inflation",
            "interest rate",
            "fed",
            "federal reserve",
            "powell",
            "treasury",
            "debt",
            "deficit",
            "oil",
            "opec",
            "iran",
            "china",
            "trade",
            "export",
            "import",
            "regulation",
            "tax",
            "subsidy",
            "nvidia",
            "semiconductor",
            "ai",
            "bitcoin",
            "crypto",
            "energy",
            "manufacturing",
            "war",
            "ceasefire",
            "recession",
            "gdp",
            "jobs",
            "unemployment",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("x_default_handles", "relevance_keywords", mode="before")
    @classmethod
    def _parse_comma_separated_values(cls, value: Any) -> Any:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def ensure_runtime_directories(self) -> None:
        self.x_accounts_db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_directories()
    return settings
