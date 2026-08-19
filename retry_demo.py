"""A small demonstration of retry, exponential backoff, and jitter."""

from __future__ import annotations

import argparse
import random
import time
from collections.abc import Callable
from typing import TypeVar


Result = TypeVar("Result")


class TemporaryInventoryError(Exception):
    """Represent a temporary failure that is safe to retry."""


def retry_with_backoff(
    operation: Callable[[], Result],
    *,
    max_attempts: int = 4,
    base_delay: float = 0.25,
    max_delay: float = 2.0,
    jitter: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    random_jitter: Callable[[float, float], float] = random.uniform,
) -> Result:
    """Run an operation again after temporary failures.

    The delay doubles after each failed attempt, is capped at ``max_delay``,
    and receives a small random jitter. Only ``TemporaryInventoryError`` is
    retried; other errors are allowed to fail immediately.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay < 0 or max_delay < 0 or jitter < 0:
        raise ValueError("delay values cannot be negative")

    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt} of {max_attempts}")

        try:
            result = operation()
        except TemporaryInventoryError as error:
            if attempt == max_attempts:
                print(f"Permanent failure after {attempt} attempts: {error}")
                raise

            exponential_delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            actual_delay = exponential_delay + random_jitter(0, jitter)
            print(f"Temporary failure: {error}")
            print(f"Waiting {actual_delay:.2f} seconds before retrying")
            sleep(actual_delay)
        else:
            print(f"Operation succeeded on attempt {attempt}")
            return result

    raise RuntimeError("retry loop ended unexpectedly")


def make_inventory_operation(failures_before_success: int) -> Callable[[], str]:
    """Create a predictable fake inventory operation for the demonstration."""

    attempts = 0

    def check_inventory() -> str:
        nonlocal attempts
        attempts += 1

        if attempts <= failures_before_success:
            raise TemporaryInventoryError("warehouse service is temporarily unavailable")

        return "Inventory update received: Northstar Jacket has 8 units"

    return check_inventory


def run_demo(scenario: str) -> int:
    """Run either the eventual-success or permanent-failure demonstration."""

    failures_before_success = 2 if scenario == "success" else 10
    operation = make_inventory_operation(failures_before_success)

    try:
        result = retry_with_backoff(operation)
    except TemporaryInventoryError:
        print("Final result: inventory update could not be completed")
        return 1

    print(f"Final result: {result}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demonstrate retry with exponential backoff and jitter."
    )
    parser.add_argument(
        "scenario",
        choices=("success", "failure"),
        help="Choose whether the fake operation eventually succeeds or keeps failing.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(run_demo(arguments.scenario))
