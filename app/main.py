"""Application entrypoint: wires config, persistence, bot handlers and scheduler."""

from __future__ import annotations

import logging

from telegram.ext import Application

from app.bot import register_handlers
from app.config import Config
from app.models import init_db
from app.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    config = Config.from_env()
    session_factory = init_db(config.database_path)

    application = Application.builder().token(config.telegram_bot_token).build()
    application.bot_data["session_factory"] = session_factory
    application.bot_data["crypto_api_key"] = config.crypto_api_key
    application.bot_data["stock_api_key"] = config.stock_api_key
    register_handlers(application)

    async def _on_startup(app: Application) -> None:
        start_scheduler(
            app,
            session_factory,
            poll_interval_seconds=config.poll_interval_seconds,
            crypto_api_key=config.crypto_api_key,
            stock_api_key=config.stock_api_key,
        )

    application.post_init = _on_startup
    application.run_polling()


if __name__ == "__main__":
    main()
