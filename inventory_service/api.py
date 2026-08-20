"""HTTP query API backed by the inventory cache."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .cache import InventoryCache
from .webhook import InvalidEventError, InvalidSignatureError, WebhookProcessor


MAX_WEBHOOK_BYTES = 64 * 1024


def create_handler(cache: InventoryCache, webhook_processor: WebhookProcessor):
    class InventoryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/health":
                snapshot = cache.snapshot()
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "sync_mode": "webhook",
                        "product_count": snapshot["product_count"],
                        "last_synced_at": snapshot["last_synced_at"],
                    },
                )
                return

            if parsed.path == "/inventory":
                sku = parse_qs(parsed.query).get("sku", [""])[0].strip()
                if not sku:
                    self._send_json(400, {"error": "sku query parameter is required"})
                    return

                product = cache.get(sku)
                if product is None:
                    self._send_json(404, {"error": f"SKU {sku} was not found"})
                    return

                self._send_json(
                    200,
                    {
                        **product,
                        "in_stock": product["quantity"] > 0,
                        "last_synced_at": cache.snapshot()["last_synced_at"],
                    },
                )
                return

            self._send_json(404, {"error": "endpoint not found"})

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/webhooks/inventory":
                self._send_json(404, {"error": "endpoint not found"})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(400, {"error": "invalid Content-Length header"})
                return

            if content_length < 1:
                self._send_json(400, {"error": "webhook body is required"})
                return
            if content_length > MAX_WEBHOOK_BYTES:
                self._send_json(413, {"error": "webhook body is too large"})
                return

            body = self.rfile.read(content_length)
            signature = self.headers.get("X-Webhook-Signature", "")

            try:
                result = webhook_processor.process(body, signature)
            except InvalidSignatureError as error:
                self._send_json(401, {"error": str(error)})
                return
            except InvalidEventError as error:
                self._send_json(422, {"error": str(error)})
                return

            self._send_json(200 if result["duplicate"] else 202, result)

        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            print(f"API: {format % args}")

    return InventoryHandler


def create_server(
    cache: InventoryCache,
    webhook_processor: WebhookProcessor,
    host: str,
    port: int,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port), create_handler(cache, webhook_processor)
    )
