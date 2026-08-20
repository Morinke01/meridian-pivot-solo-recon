"""Tests for the Day 4 webhook inventory service."""

from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from inventory_service.api import create_server
from inventory_service.cache import InventoryCache
from inventory_service.webhook import WebhookProcessor


class WebhookInventoryServiceTests(unittest.TestCase):
    secret = "test-secret"

    def setUp(self) -> None:
        self.cache = InventoryCache()
        self.processor = WebhookProcessor(self.cache, self.secret)
        self.server = create_server(self.cache, self.processor, "127.0.0.1", 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def test_valid_webhook_updates_inventory_cache(self):
        body = self._event_body(event_id="evt-001", quantity=12)

        status, result = self._post_webhook(body, self.processor.expected_signature(body))

        self.assertEqual(status, 202)
        self.assertTrue(result["processed"])
        self.assertFalse(result["duplicate"])
        self.assertEqual(self.cache.get("NS-JACKET-M-BLK")["quantity"], 12)

    def test_invalid_signature_is_rejected_without_cache_update(self):
        body = self._event_body(event_id="evt-002", quantity=5)

        with self.assertRaises(HTTPError) as context:
            self._post_webhook(body, "sha256=invalid")

        self.assertEqual(context.exception.code, 401)
        context.exception.close()
        self.assertIsNone(self.cache.get("NS-JACKET-M-BLK"))

    def test_duplicate_event_is_acknowledged_but_not_processed_twice(self):
        body = self._event_body(event_id="evt-003", quantity=7)
        signature = self.processor.expected_signature(body)

        first_status, first = self._post_webhook(body, signature)
        second_status, second = self._post_webhook(body, signature)

        self.assertEqual(first_status, 202)
        self.assertTrue(first["processed"])
        self.assertEqual(second_status, 200)
        self.assertFalse(second["processed"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(self.cache.get("NS-JACKET-M-BLK")["quantity"], 7)

    def test_invalid_payload_is_rejected(self):
        body = json.dumps(
            {
                "event_id": "evt-004",
                "event_type": "inventory.updated",
                "product": {
                    "sku": "NS-JACKET-M-BLK",
                    "name": "Jacket",
                    "quantity": -1,
                },
            }
        ).encode("utf-8")

        with self.assertRaises(HTTPError) as context:
            self._post_webhook(body, self.processor.expected_signature(body))

        self.assertEqual(context.exception.code, 422)
        context.exception.close()

    def test_stock_query_still_reports_in_stock_after_pivot(self):
        body = self._event_body(event_id="evt-005", quantity=8)
        self._post_webhook(body, self.processor.expected_signature(body))

        with urlopen(f"{self.base_url}/inventory?sku=NS-JACKET-M-BLK") as response:
            payload = json.load(response)

        self.assertEqual(payload["quantity"], 8)
        self.assertTrue(payload["in_stock"])
        self.assertIsNotNone(payload["last_synced_at"])

    def test_stock_query_still_reports_out_of_stock_after_pivot(self):
        body = self._event_body(event_id="evt-006", quantity=0)
        self._post_webhook(body, self.processor.expected_signature(body))

        with urlopen(f"{self.base_url}/inventory?sku=NS-JACKET-M-BLK") as response:
            payload = json.load(response)

        self.assertEqual(payload["quantity"], 0)
        self.assertFalse(payload["in_stock"])

    def test_health_endpoint_reports_webhook_mode(self):
        with urlopen(f"{self.base_url}/health") as response:
            payload = json.load(response)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["sync_mode"], "webhook")
        self.assertEqual(payload["product_count"], 0)

    def _event_body(self, *, event_id: str, quantity: int) -> bytes:
        return json.dumps(
            {
                "event_id": event_id,
                "event_type": "inventory.updated",
                "product": {
                    "sku": "NS-JACKET-M-BLK",
                    "name": "Northstar Jacket",
                    "quantity": quantity,
                },
            },
            separators=(",", ":"),
        ).encode("utf-8")

    def _post_webhook(self, body: bytes, signature: str) -> tuple[int, dict]:
        request = Request(
            f"{self.base_url}/webhooks/inventory",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )
        with urlopen(request) as response:
            return response.status, json.load(response)


if __name__ == "__main__":
    unittest.main()
