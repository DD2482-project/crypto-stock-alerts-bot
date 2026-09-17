"""Background job: poll prices, evaluate subscriptions, notify on trigger."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from app.conditions import is_triggered
from app.models import get_active_subscriptions, mark_triggered
from app.price_sources import get_price_source

logger = logging.getLogger(__name__)


async def poll_and_notify(
    application: Application,
    session_factory,
    *,
    crypto_api_key: str | None,
    stock_api_key: str | None,
) -> None:
    with session_factory() as session:
        subscriptions = get_active_subscriptions(session)

        for subscription in subscriptions:
            try:
                source = get_price_source(
                    subscription.asset_type,
                    crypto_api_key=crypto_api_key,
                    stock_api_key=stock_api_key,
                )
                current_price = source.get_price(subscription.symbol)
            except Exception:
                logger.exception(
                    "Failed to fetch price for subscription #%s (%s)",
                    subscription.id,
                    subscription.symbol,
                )
                continue

            if not is_triggered(
                subscription.condition_type,
                subscription.target_value,
                subscription.base_price,
                current_price,
            ):
                continue

            try:
                await application.bot.send_message(
                    chat_id=subscription.chat_id,
                    text=(
                        f"Alert: {subscription.symbol} is now {current_price} "
                        f"(target: {subscription.condition_type.value} "
                        f"{subscription.target_value})"
                    ),
                )
            except Exception:
                logger.exception(
                    "Failed to notify chat %s for subscription #%s",
                    subscription.chat_id,
                    subscription.id,
                )
                continue

            mark_triggered(session, subscription)


def start_scheduler(
    application: Application,
    session_factory,
    *,
    poll_interval_seconds: int,
    crypto_api_key: str | None,
    stock_api_key: str | None,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_and_notify,
        "interval",
        seconds=poll_interval_seconds,
        args=[application, session_factory],
        kwargs={"crypto_api_key": crypto_api_key, "stock_api_key": stock_api_key},
        id="poll_and_notify",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler
