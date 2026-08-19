"""Start the Day 3 polling inventory service."""

from __future__ import annotations

import argparse

from inventory_service.api import create_server
from inventory_service.cache import InventoryCache
from inventory_service.poller import InventoryPoller
from inventory_service.warehouse import WarehouseClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Northstar inventory service.")
    parser.add_argument(
        "--warehouse-url",
        default="http://127.0.0.1:9000/inventory",
        help="Warehouse inventory endpoint.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=300,
        help="Seconds between polls; production default is 300 seconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cache = InventoryCache()
    client = WarehouseClient(args.warehouse_url)
    poller = InventoryPoller(
        client,
        cache,
        interval_seconds=args.poll_interval,
    )
    server = create_server(cache, args.host, args.port)

    poller.start()
    print(f"Stock query API listening at http://{args.host}:{args.port}")
    print(f"Polling {args.warehouse_url} every {args.poll_interval:g} seconds")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping inventory service")
    finally:
        server.shutdown()
        poller.stop()
        server.server_close()


if __name__ == "__main__":
    main()
