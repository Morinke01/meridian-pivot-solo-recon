"""Tests for the Day 3 polling inventory service."""

from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from inventory_service.api import create_server
from inventory_service.cache import InventoryCache
from inventory_service.poller import InventoryPoller
from inventory_service.warehouse import WarehouseClient
from mock_warehouse import WarehouseHandler


class FakeWarehouseClient:
    def __init__(self, products: list[dict]) -> None:
        self.products = products
        self.calls = 0

    def fetch_inventory(self) -> list[dict]:
        self.calls += 1
        return self.products


class InventoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.products = [
            {"sku": "NS-JACKET-M-BLK", "name": "Northstar Jacket", "quantity": 8},
            {"sku": "NS-TEE-L-WHT", "name": "Northstar Tee", "quantity": 0},
        ]

    def test_poller_updates_cache_from_warehouse(self):
        cache = InventoryCache()
        client = FakeWarehouseClient(self.products)
        retry_calls = []

        def immediate_retry(operation):
            retry_calls.append("called")
            return operation()

        poller = InventoryPoller(client, cache, retry_operation=immediate_retry)

        product_count = poller.sync_once()

        self.assertEqual(product_count, 2)
        self.assertEqual(client.calls, 1)
        self.assertEqual(retry_calls, ["called"])
        self.assertEqual(cache.get("NS-JACKET-M-BLK")["quantity"], 8)
        self.assertIsNotNone(cache.snapshot()["last_synced_at"])

    def test_warehouse_client_reads_mock_api(self):
        server = self._start_server(WarehouseHandler)

        try:
            client = WarehouseClient(
                f"http://127.0.0.1:{server.server_port}/inventory"
            )
            products = client.fetch_inventory()
        finally:
            self._stop_server(server)

        self.assertEqual(len(products), 3)
        self.assertEqual(products[0]["sku"], "NS-JACKET-M-BLK")

    def test_query_endpoint_returns_stock_status(self):
        cache = InventoryCache()
        cache.replace(self.products)
        server = create_server(cache, "127.0.0.1", 0)
        self._serve_in_background(server)

        try:
            url = (
                f"http://127.0.0.1:{server.server_port}"
                "/inventory?sku=NS-JACKET-M-BLK"
            )
            with urlopen(url) as response:
                payload = json.load(response)
        finally:
            self._stop_server(server)

        self.assertEqual(payload["quantity"], 8)
        self.assertTrue(payload["in_stock"])

    def test_query_endpoint_reports_out_of_stock(self):
        cache = InventoryCache()
        cache.replace(self.products)
        server = create_server(cache, "127.0.0.1", 0)
        self._serve_in_background(server)

        try:
            url = (
                f"http://127.0.0.1:{server.server_port}"
                "/inventory?sku=NS-TEE-L-WHT"
            )
            with urlopen(url) as response:
                payload = json.load(response)
        finally:
            self._stop_server(server)

        self.assertEqual(payload["quantity"], 0)
        self.assertFalse(payload["in_stock"])

    def test_query_endpoint_requires_sku(self):
        cache = InventoryCache()
        server = create_server(cache, "127.0.0.1", 0)
        self._serve_in_background(server)

        try:
            with self.assertRaises(HTTPError) as context:
                urlopen(f"http://127.0.0.1:{server.server_port}/inventory")
        finally:
            self._stop_server(server)

        self.assertEqual(context.exception.code, 400)
        context.exception.close()

    def _start_server(self, handler):
        from http.server import ThreadingHTTPServer

        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._serve_in_background(server)
        return server

    @staticmethod
    def _serve_in_background(server) -> None:
        threading.Thread(target=server.serve_forever, daemon=True).start()

    @staticmethod
    def _stop_server(server) -> None:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    unittest.main()
