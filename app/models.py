"""Persistence layer for subscriptions.

Uses SQLAlchemy's ORM so the backing database can be swapped from SQLite to
Postgres by changing the connection URL alone -- no query code depends on
SQLite-specific behaviour.
"""

from __future__ import annotations

import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class AssetType(str, enum.Enum):
    CRYPTO = "crypto"
    STOCK = "stock"


class ConditionType(str, enum.Enum):
    PRICE = "price"
    PERCENT = "pct"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"


class Base(DeclarativeBase):
    pass


class Subscription(Base):
    """A user's request to be notified when a symbol meets a condition.

    On trigger, the row is kept and flipped to TRIGGERED (rather than
    deleted) so /list can show history and the scheduler never re-notifies
    for the same crossing.
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    condition_type: Mapped[ConditionType] = mapped_column(Enum(ConditionType), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    triggered_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


def init_db(database_path: str) -> sessionmaker[Session]:
    """Create the schema (if needed) and return a session factory."""
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def create_subscription(
    session: Session,
    *,
    chat_id: int,
    symbol: str,
    asset_type: AssetType,
    condition_type: ConditionType,
    target_value: float,
    base_price: float,
) -> Subscription:
    subscription = Subscription(
        chat_id=chat_id,
        symbol=symbol.upper(),
        asset_type=asset_type,
        condition_type=condition_type,
        target_value=target_value,
        base_price=base_price,
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def list_subscriptions(session: Session, *, chat_id: int) -> list[Subscription]:
    stmt = select(Subscription).where(Subscription.chat_id == chat_id).order_by(Subscription.id)
    return list(session.scalars(stmt))


def get_active_subscriptions(session: Session) -> list[Subscription]:
    stmt = select(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE)
    return list(session.scalars(stmt))


def delete_subscription(session: Session, *, chat_id: int, subscription_id: int) -> bool:
    subscription = session.get(Subscription, subscription_id)
    if subscription is None or subscription.chat_id != chat_id:
        return False
    session.delete(subscription)
    session.commit()
    return True


def mark_triggered(session: Session, subscription: Subscription) -> None:
    subscription.status = SubscriptionStatus.TRIGGERED
    subscription.triggered_at = datetime.datetime.utcnow()
    session.add(subscription)
    session.commit()
