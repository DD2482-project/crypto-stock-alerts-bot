"""Environment variable loading for the bot."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    crypto_api_key: str | None
    stock_api_key: str | None
    poll_interval_seconds: int
    database_path: str

    @classmethod
    def from_env(cls) -> Config:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")
        return cls(
            telegram_bot_token=token,
            crypto_api_key=os.environ.get("CRYPTO_API_KEY") or None,
            stock_api_key=os.environ.get("STOCK_API_KEY") or None,
            poll_interval_seconds=int(os.environ.get("POLL_INTERVAL_SECONDS", "60")),
            database_path=os.environ.get("DATABASE_PATH", "alerts.db"),
        )
