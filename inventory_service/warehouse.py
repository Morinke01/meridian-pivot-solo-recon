"""HTTP client for retrieving inventory from the warehouse service."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from retry_demo import TemporaryInventoryError


class WarehouseClient:
    def __init__(self, inventory_url: str, timeout: float = 5.0) -> None:
        self.inventory_url = inventory_url
        self.timeout = timeout

    def fetch_inventory(self) -> list[dict]:
        try:
            with urlopen(self.inventory_url, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            if error.code == 429 or error.code >= 500:
                raise TemporaryInventoryError(
                    f"warehouse returned HTTP {error.code}"
                ) from error
            raise ValueError(f"warehouse request was rejected: HTTP {error.code}") from error
        except (TimeoutError, URLError) as error:
            raise TemporaryInventoryError("warehouse could not be reached") from error
        except json.JSONDecodeError as error:
            raise ValueError("warehouse returned invalid JSON") from error

        products = payload.get("products") if isinstance(payload, dict) else None
        if not isinstance(products, list):
            raise ValueError("warehouse response must contain a products list")

        for product in products:
            if not isinstance(product, dict) or not isinstance(product.get("sku"), str):
                raise ValueError("every warehouse product must have a string SKU")
            quantity = product.get("quantity")
            if not isinstance(quantity, int) or quantity < 0:
                raise ValueError("every warehouse product must have a non-negative quantity")

        return products
