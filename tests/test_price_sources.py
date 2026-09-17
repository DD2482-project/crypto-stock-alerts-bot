import pytest

from app.price_sources.coingecko import COINGECKO_API_URL, CoinGeckoPriceSource
from app.price_sources.stock import ALPHA_VANTAGE_API_URL, AlphaVantagePriceSource


def test_coingecko_parses_price(requests_mock):
    requests_mock.get(COINGECKO_API_URL, json={"bitcoin": {"usd": 65000.5}})

    price = CoinGeckoPriceSource().get_price("bitcoin")

    assert price == 65000.5


def test_coingecko_raises_for_unknown_symbol(requests_mock):
    requests_mock.get(COINGECKO_API_URL, json={})

    with pytest.raises(ValueError):
        CoinGeckoPriceSource().get_price("not-a-coin")


def test_alpha_vantage_parses_price(requests_mock):
    requests_mock.get(ALPHA_VANTAGE_API_URL, json={"Global Quote": {"05. price": "189.32"}})

    price = AlphaVantagePriceSource(api_key="test-key").get_price("AAPL")

    assert price == 189.32


def test_alpha_vantage_raises_for_missing_quote(requests_mock):
    requests_mock.get(ALPHA_VANTAGE_API_URL, json={})

    with pytest.raises(ValueError):
        AlphaVantagePriceSource(api_key="test-key").get_price("NOPE")


def test_alpha_vantage_requires_api_key():
    with pytest.raises(ValueError):
        AlphaVantagePriceSource(api_key=None)
