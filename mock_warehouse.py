"""Local warehouse API used to demonstrate Day 3 polling."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PRODUCTS = [
    {"sku": "NS-JACKET-M-BLK", "name": "Northstar Jacket", "quantity": 8},
    {"sku": "NS-TEE-L-WHT", "name": "Northstar Tee", "quantity": 0},
    {"sku": "NS-BAG-STD-GRN", "name": "Northstar Trail Bag", "quantity": 14},
]


class WarehouseHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/inventory":
            self.send_error(404)
            return

        body = json.dumps({"products": PRODUCTS}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(f"Warehouse: {format % args}")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 9000), WarehouseHandler)
    print("Mock warehouse listening at http://127.0.0.1:9000/inventory")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping mock warehouse")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
