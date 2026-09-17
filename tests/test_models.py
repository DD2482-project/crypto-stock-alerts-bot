import pytest

from app.models import (
    AssetType,
    ConditionType,
    SubscriptionStatus,
    create_subscription,
    delete_subscription,
    get_active_subscriptions,
    init_db,
    list_subscriptions,
    mark_triggered,
)


@pytest.fixture
def session_factory(tmp_path):
    return init_db(str(tmp_path / "test.db"))


def _make(session_factory, chat_id=1, symbol="bitcoin"):
    with session_factory() as session:
        return create_subscription(
            session,
            chat_id=chat_id,
            symbol=symbol,
            asset_type=AssetType.CRYPTO,
            condition_type=ConditionType.PRICE,
            target_value=100.0,
            base_price=90.0,
        )


def test_create_and_list_subscription(session_factory):
    created = _make(session_factory, chat_id=42)

    with session_factory() as session:
        subs = list_subscriptions(session, chat_id=42)

    assert len(subs) == 1
    assert subs[0].id == created.id
    assert subs[0].symbol == "BITCOIN"
    assert subs[0].status == SubscriptionStatus.ACTIVE


def test_list_subscriptions_scoped_to_chat_id(session_factory):
    _make(session_factory, chat_id=1)
    _make(session_factory, chat_id=2)

    with session_factory() as session:
        assert len(list_subscriptions(session, chat_id=1)) == 1
        assert len(list_subscriptions(session, chat_id=2)) == 1


def test_get_active_subscriptions_excludes_triggered(session_factory):
    sub = _make(session_factory)

    with session_factory() as session:
        assert len(get_active_subscriptions(session)) == 1
        fresh = session.get(type(sub), sub.id)
        mark_triggered(session, fresh)

    with session_factory() as session:
        assert get_active_subscriptions(session) == []
        subs = list_subscriptions(session, chat_id=1)
        assert subs[0].status == SubscriptionStatus.TRIGGERED
        assert subs[0].triggered_at is not None


def test_delete_subscription_only_removes_owning_chat(session_factory):
    sub = _make(session_factory, chat_id=1)

    with session_factory() as session:
        assert delete_subscription(session, chat_id=2, subscription_id=sub.id) is False
        assert delete_subscription(session, chat_id=1, subscription_id=sub.id) is True

    with session_factory() as session:
        assert list_subscriptions(session, chat_id=1) == []


def test_delete_subscription_returns_false_for_unknown_id(session_factory):
    with session_factory() as session:
        assert delete_subscription(session, chat_id=1, subscription_id=999) is False
