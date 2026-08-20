"""Verification and processing for warehouse inventory webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
import threading

from .cache import InventoryCache


class InvalidSignatureError(ValueError):
    """Raised when the webhook signature cannot be verified."""


class InvalidEventError(ValueError):
    """Raised when a webhook payload does not match the expected contract."""


class WebhookProcessor:
    def __init__(self, cache: InventoryCache, secret: str) -> None:
        if not secret:
            raise ValueError("webhook secret cannot be empty")

        self.cache = cache
        self._secret = secret.encode("utf-8")
        self._processed_event_ids: set[str] = set()
        self._lock = threading.Lock()

    def expected_signature(self, body: bytes) -> str:
        digest = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def process(self, body: bytes, provided_signature: str) -> dict:
        expected = self.expected_signature(body)
        if not provided_signature or not hmac.compare_digest(
            provided_signature, expected
        ):
            raise InvalidSignatureError("webhook signature is invalid")

        try:
            event = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InvalidEventError("webhook body must be valid JSON") from error

        event_id, product = self._validate_event(event)

        with self._lock:
            if event_id in self._processed_event_ids:
                return {"event_id": event_id, "processed": False, "duplicate": True}

            self.cache.upsert(product)
            self._processed_event_ids.add(event_id)

        return {"event_id": event_id, "processed": True, "duplicate": False}

    @staticmethod
    def _validate_event(event: object) -> tuple[str, dict]:
        if not isinstance(event, dict):
            raise InvalidEventError("webhook event must be a JSON object")

        event_id = event.get("event_id")
        event_type = event.get("event_type")
        product = event.get("product")

        if not isinstance(event_id, str) or not event_id.strip():
            raise InvalidEventError("event_id must be a non-empty string")
        if event_type != "inventory.updated":
            raise InvalidEventError("event_type must be inventory.updated")
        if not isinstance(product, dict):
            raise InvalidEventError("product must be an object")

        sku = product.get("sku")
        name = product.get("name")
        quantity = product.get("quantity")

        if not isinstance(sku, str) or not sku.strip():
            raise InvalidEventError("product.sku must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise InvalidEventError("product.name must be a non-empty string")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
            raise InvalidEventError("product.quantity must be a non-negative integer")

        return event_id, {"sku": sku, "name": name, "quantity": quantity}
