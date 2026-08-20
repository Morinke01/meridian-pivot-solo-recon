"""Thread-safe in-memory inventory cache."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock


class InventoryCache:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}
        self._last_synced_at: str | None = None
        self._lock = Lock()

    def replace(self, products: list[dict]) -> None:
        """Replace the cache with one complete warehouse snapshot."""

        normalized = {product["sku"]: deepcopy(product) for product in products}
        synced_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._items = normalized
            self._last_synced_at = synced_at

    def upsert(self, product: dict) -> None:
        """Insert or replace one product received through a webhook event."""

        synced_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._items[product["sku"]] = deepcopy(product)
            self._last_synced_at = synced_at

    def get(self, sku: str) -> dict | None:
        with self._lock:
            product = self._items.get(sku)
            return deepcopy(product) if product else None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "products": deepcopy(list(self._items.values())),
                "last_synced_at": self._last_synced_at,
                "product_count": len(self._items),
            }
