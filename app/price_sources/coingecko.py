"""CoinGecko price source (crypto).

Note: CoinGecko's `simple/price` endpoint keys prices by CoinGecko coin id
(e.g. "bitcoin"), not ticker symbol (e.g. "BTC"). Users must subscribe with
the CoinGecko id -- documented as a limitation in the report rather than
worked around, to keep this provider simple.
"""

from __future__ import annotations

import requests

from app.price_sources import PriceSource

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"


class CoinGeckoPriceSource(PriceSource):
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()

    def get_price(self, symbol: str) -> float:
        coin_id = symbol.lower()
        headers = {"x-cg-demo-api-key": self._api_key} if self._api_key else {}
        response = self._session.get(
            COINGECKO_API_URL,
            params={"ids": coin_id, "vs_currencies": "usd"},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if coin_id not in data or "usd" not in data[coin_id]:
            raise ValueError(f"No price data for symbol '{symbol}'")
        return float(data[coin_id]["usd"])
