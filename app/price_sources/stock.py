"""Alpha Vantage price source (stocks).

Alpha Vantage was chosen over Yahoo Finance because it has an official,
documented, key-based API -- Yahoo's public endpoints are unofficial and
prone to breaking without notice. Trade-off: Alpha Vantage's free tier is
rate-limited (5 requests/minute, 25/day), which constrains how many stock
subscriptions and how short a poll interval this deployment can support.
"""

from __future__ import annotations

import requests

from app.price_sources import PriceSource

ALPHA_VANTAGE_API_URL = "https://www.alphavantage.co/query"


class AlphaVantagePriceSource(PriceSource):
    def __init__(self, api_key: str | None, session: requests.Session | None = None):
        if not api_key:
            raise ValueError("Alpha Vantage requires an API key (STOCK_API_KEY)")
        self._api_key = api_key
        self._session = session or requests.Session()

    def get_price(self, symbol: str) -> float:
        response = self._session.get(
            ALPHA_VANTAGE_API_URL,
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol.upper(),
                "apikey": self._api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        quote = data.get("Global Quote") or {}
        price_str = quote.get("05. price")
        if not price_str:
            raise ValueError(f"No price data for symbol '{symbol}'")
        return float(price_str)
