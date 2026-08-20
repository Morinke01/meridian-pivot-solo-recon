"""Send a correctly signed inventory webhook for local demonstration."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a warehouse inventory event.")
    parser.add_argument("--url", default="http://127.0.0.1:8080/webhooks/inventory")
    parser.add_argument("--event-id", default=None)
    parser.add_argument("--sku", default="NS-JACKET-M-BLK")
    parser.add_argument("--name", default="Northstar Jacket")
    parser.add_argument("--quantity", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    secret = os.environ.get("NORTHSTAR_WEBHOOK_SECRET")
    if not secret:
        raise SystemExit("NORTHSTAR_WEBHOOK_SECRET environment variable is required")

    event = {
        "event_id": args.event_id or str(uuid.uuid4()),
        "event_type": "inventory.updated",
        "product": {
            "sku": args.sku,
            "name": args.name,
            "quantity": args.quantity,
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode("utf-8")
    signature = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    request = Request(
        args.url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )

    try:
        with urlopen(request) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as error:
        response_body = error.read().decode("utf-8")
        raise SystemExit(f"Webhook rejected with HTTP {error.code}: {response_body}") from error


if __name__ == "__main__":
    main()
