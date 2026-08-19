"""Scheduled warehouse polling."""

from __future__ import annotations

import threading
from collections.abc import Callable

from retry_demo import retry_with_backoff

from .cache import InventoryCache
from .warehouse import WarehouseClient


class InventoryPoller:
    def __init__(
        self,
        client: WarehouseClient,
        cache: InventoryCache,
        *,
        interval_seconds: float = 300,
        retry_operation: Callable = retry_with_backoff,
    ) -> None:
        self.client = client
        self.cache = cache
        self.interval_seconds = interval_seconds
        self.retry_operation = retry_operation
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def sync_once(self) -> int:
        products = self.retry_operation(self.client.fetch_inventory)
        self.cache.replace(products)
        print(f"Inventory cache synchronized with {len(products)} products")
        return len(products)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval_seconds + 1)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.sync_once()
            except Exception as error:  # Keep future polling cycles alive.
                print(f"Inventory synchronization failed: {error}")

            self._stop_event.wait(self.interval_seconds)
