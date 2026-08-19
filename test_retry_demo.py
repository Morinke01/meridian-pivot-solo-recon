"""Tests for the retry and backoff mini-prototype."""

import unittest

from retry_demo import (
    TemporaryInventoryError,
    make_inventory_operation,
    retry_with_backoff,
)


class RetryWithBackoffTests(unittest.TestCase):
    def setUp(self):
        self.recorded_delays: list[float] = []

    def record_sleep(self, delay: float) -> None:
        """Record a delay instead of making the test really wait."""

        self.recorded_delays.append(delay)

    def test_operation_eventually_succeeds(self):
        operation = make_inventory_operation(failures_before_success=2)

        result = retry_with_backoff(
            operation,
            max_attempts=4,
            base_delay=1,
            jitter=0,
            sleep=self.record_sleep,
        )

        self.assertIn("8 units", result)
        self.assertEqual(self.recorded_delays, [1, 2])

    def test_operation_stops_after_maximum_attempts(self):
        operation = make_inventory_operation(failures_before_success=10)

        with self.assertRaises(TemporaryInventoryError):
            retry_with_backoff(
                operation,
                max_attempts=3,
                base_delay=1,
                jitter=0,
                sleep=self.record_sleep,
            )

        self.assertEqual(self.recorded_delays, [1, 2])

    def test_permanent_error_is_not_retried(self):
        def invalid_operation():
            raise ValueError("invalid inventory request")

        with self.assertRaises(ValueError):
            retry_with_backoff(invalid_operation, sleep=self.record_sleep)

        self.assertEqual(self.recorded_delays, [])

    def test_jitter_is_added_to_the_delay(self):
        operation = make_inventory_operation(failures_before_success=1)

        retry_with_backoff(
            operation,
            base_delay=1,
            jitter=0.5,
            sleep=self.record_sleep,
            random_jitter=lambda _start, _end: 0.25,
        )

        self.assertEqual(self.recorded_delays, [1.25])


if __name__ == "__main__":
    unittest.main()
