"""Integration test that calls the real Telegram Bot API."""

import os

import pytest
from telegram import Bot
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

pytestmark = pytest.mark.skipif(
    not TELEGRAM_BOT_TOKEN,
    reason="TELEGRAM_BOT_TOKEN not set; skipping live Telegram API check",
)


async def test_bot_token_is_accepted_by_telegram():
    """Checks Telegram accepts the configured bot token."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    me = await bot.get_me()
    assert me.is_bot
    assert me.username


async def test_invalid_token_is_rejected_by_telegram():
    """Checks Telegram rejects an unissued bot token."""
    bot = Bot(token="123456:invalid-token-value")
    with pytest.raises(TelegramError):
        await bot.get_me()
