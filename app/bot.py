"""Telegram command handlers.

Design choice: the brief's `/subscribe <symbol> <price|pct> <value>` syntax
has no asset-type argument, so asset type is inferred by trying the crypto
price source first and falling back to the stock price source if the
symbol isn't a known CoinGecko id. This keeps the command simple at the
cost of an extra lookup call on subscribe; documented as a trade-off in the
report rather than adding a fourth required argument.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.models import (
    AssetType,
    ConditionType,
    SubscriptionStatus,
    create_subscription,
    delete_subscription,
    list_subscriptions,
)
from app.price_sources import get_price_source

logger = logging.getLogger(__name__)

USAGE = (
    "Usage:\n"
    "/subscribe <symbol> <price|pct> <value> - e.g. /subscribe bitcoin price 70000\n"
    "/list - show your subscriptions\n"
    "/unsubscribe <id> - remove a subscription"
)


def _resolve_price(context: ContextTypes.DEFAULT_TYPE, symbol: str) -> tuple[AssetType, float]:
    """Try crypto then stock, returning the asset type that resolved and its price."""
    crypto_api_key = context.bot_data.get("crypto_api_key")
    stock_api_key = context.bot_data.get("stock_api_key")

    try:
        source = get_price_source(AssetType.CRYPTO, crypto_api_key=crypto_api_key)
        return AssetType.CRYPTO, source.get_price(symbol)
    except Exception:  # noqa: BLE001 - fall through to stock lookup
        pass

    source = get_price_source(AssetType.STOCK, stock_api_key=stock_api_key)
    return AssetType.STOCK, source.get_price(symbol)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! I'll notify you about price alerts.\n" + USAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(USAGE)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) != 3:
        await update.message.reply_text(USAGE)
        return

    symbol, condition_str, value_str = args
    condition_str = condition_str.lower()
    if condition_str not in ("price", "pct"):
        await update.message.reply_text(f"Unknown condition type '{condition_str}'.\n" + USAGE)
        return

    try:
        target_value = float(value_str)
    except ValueError:
        await update.message.reply_text(f"'{value_str}' is not a number.\n" + USAGE)
        return

    condition_type = ConditionType.PRICE if condition_str == "price" else ConditionType.PERCENT

    try:
        asset_type, base_price = _resolve_price(context, symbol)
    except Exception:
        logger.exception("Failed to resolve price for symbol %s", symbol)
        await update.message.reply_text(
            f"Couldn't find a price for '{symbol}'. Check the symbol and try again."
        )
        return

    session_factory = context.bot_data["session_factory"]
    with session_factory() as session:
        subscription = create_subscription(
            session,
            chat_id=update.effective_chat.id,
            symbol=symbol,
            asset_type=asset_type,
            condition_type=condition_type,
            target_value=target_value,
            base_price=base_price,
        )

    await update.message.reply_text(
        f"Subscribed (#{subscription.id}): {subscription.symbol} [{asset_type.value}] "
        f"{condition_str} {target_value} (current price: {base_price})"
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session_factory = context.bot_data["session_factory"]
    with session_factory() as session:
        subscriptions = list_subscriptions(session, chat_id=update.effective_chat.id)

    if not subscriptions:
        await update.message.reply_text("You have no subscriptions.")
        return

    lines = []
    for sub in subscriptions:
        condition = "price" if sub.condition_type == ConditionType.PRICE else "pct"
        status = "triggered" if sub.status == SubscriptionStatus.TRIGGERED else "active"
        lines.append(
            f"#{sub.id} {sub.symbol} [{sub.asset_type.value}] {condition} "
            f"{sub.target_value} - {status}"
        )
    await update.message.reply_text("\n".join(lines))


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) != 1:
        await update.message.reply_text("Usage: /unsubscribe <id>")
        return

    try:
        subscription_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Subscription id must be a number.")
        return

    session_factory = context.bot_data["session_factory"]
    with session_factory() as session:
        removed = delete_subscription(
            session, chat_id=update.effective_chat.id, subscription_id=subscription_id
        )

    if removed:
        await update.message.reply_text(f"Unsubscribed #{subscription_id}.")
    else:
        await update.message.reply_text(f"No subscription #{subscription_id} found.")


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
