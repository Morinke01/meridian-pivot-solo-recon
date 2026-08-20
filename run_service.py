"""Start the Day 3 polling inventory service."""

from __future__ import annotations

import argparse
import os

from inventory_service.api import create_server
from inventory_service.cache import InventoryCache
from inventory_service.webhook import WebhookProcessor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Northstar inventory service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    webhook_secret = os.environ.get("NORTHSTAR_WEBHOOK_SECRET")
    if not webhook_secret:
        raise SystemExit("NORTHSTAR_WEBHOOK_SECRET environment variable is required")

    cache = InventoryCache()
    webhook_processor = WebhookProcessor(cache, webhook_secret)
    server = create_server(cache, webhook_processor, args.host, args.port)

    print(f"Stock query API listening at http://{args.host}:{args.port}")
    print(f"Inventory webhook listening at http://{args.host}:{args.port}/webhooks/inventory")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping inventory service")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
