"""Market-data provider interface.

Each provider implements `get_price(symbol) -> float`. `get_price_source`
picks the implementation for an asset type so the rest of the app (the
scheduler) never depends on a specific provider directly, and a provider
can be swapped by adding a new module here without touching call sites.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import AssetType


class PriceSource(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> float:
        """Return the current price of `symbol` in USD."""


def get_price_source(
    asset_type: AssetType,
    *,
    crypto_api_key: str | None = None,
    stock_api_key: str | None = None,
) -> PriceSource:
    if asset_type == AssetType.CRYPTO:
        from app.price_sources.coingecko import CoinGeckoPriceSource

        return CoinGeckoPriceSource(api_key=crypto_api_key)
    if asset_type == AssetType.STOCK:
        from app.price_sources.stock import AlphaVantagePriceSource

        return AlphaVantagePriceSource(api_key=stock_api_key)
    raise ValueError(f"Unknown asset type: {asset_type}")
