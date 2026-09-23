"""Telegram command handlers.

Design choice: the brief's `/subscribe <symbol> <price|pct> <value>` syntax
has no asset-type argument, so asset type is inferred by trying the crypto
price source first and falling back to the stock price source if the
symbol isn't a known CoinGecko id. This keeps the command simple at the
cost of an extra lookup call on subscribe; documented as a trade-off in the
report rather than adding a fourth required argument.
"""

from __future__ import annotations

import html
import logging

from telegram import Update
from telegram.constants import ParseMode
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

# Rendered with ParseMode.HTML. Placeholders are written in caps rather
# than angle brackets (<symbol>) because Telegram would either strip them
# as markup or display them as literal tags, neither of which reads well.
USAGE = (
    "<b>Commands</b>\n\n"
    "<code>/subscribe SYMBOL price VALUE</code>\n"
    "Alert me when the price crosses VALUE.\n"
    "<i>Example:</i> <code>/subscribe bitcoin price 70000</code>\n\n"
    "<code>/subscribe SYMBOL pct VALUE</code>\n"
    "Alert me on a VALUE% move from the current price.\n"
    "<i>Example:</i> <code>/subscribe ethereum pct 5</code>\n\n"
    "<code>/list</code> — show your subscriptions\n"
    "<code>/unsubscribe ID</code> — remove one\n\n"
    "<i>Crypto uses CoinGecko ids (bitcoin, ethereum); "
    "stocks use tickers (AAPL, TSLA).</i>"
)

WELCOME = (
    "📈 <b>Crypto &amp; Stock Alerts</b>\n\n"
    "I watch prices for you and send a message the moment your "
    "target is reached.\n\n"
) + USAGE


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
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(USAGE, parse_mode=ParseMode.HTML)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) != 3:
        await update.message.reply_text(USAGE, parse_mode=ParseMode.HTML)
        return

    symbol, condition_str, value_str = args
    condition_str = condition_str.lower()
    if condition_str not in ("price", "pct"):
        await update.message.reply_text(
            f"⚠️ Unknown condition type <b>{html.escape(condition_str)}</b>.\n\n" + USAGE,
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        target_value = float(value_str)
    except ValueError:
        await update.message.reply_text(
            f"⚠️ <b>{html.escape(value_str)}</b> is not a number.\n\n" + USAGE,
            parse_mode=ParseMode.HTML,
        )
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
        await update.message.reply_text(
            "Usage: <code>/unsubscribe ID</code>", parse_mode=ParseMode.HTML
        )
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