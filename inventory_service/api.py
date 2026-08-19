"""HTTP query API backed by the inventory cache."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .cache import InventoryCache


def create_handler(cache: InventoryCache):
    class InventoryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)

            if parsed.path == "/health":
                snapshot = cache.snapshot()
                self._send_json(
                    200,
                    {
                        "status": "ok",
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


def create_server(cache: InventoryCache, host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), create_handler(cache))
