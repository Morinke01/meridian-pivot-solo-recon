# Meridian Pivot Inventory Service

Morinke Julius's Week 2 Solo Recon and inventory synchronization deliverable.

## Day 3 architecture

```text
Mock warehouse API
        |
        | polled every 300 seconds
        v
Warehouse client with retry/backoff
        |
        v
Thread-safe inventory cache
        |
        v
Stock query HTTP endpoint
```

The production polling interval defaults to five minutes. A shorter interval
can be supplied while demonstrating the service.

## Run the Day 3 service

Open two terminals in the repository.

Terminal 1 starts the simulated warehouse:

```bash
python3 mock_warehouse.py
```

Terminal 2 starts the inventory service:

```bash
python3 run_service.py
```

For a faster demonstration that polls every second:

```bash
python3 run_service.py --poll-interval 1
```

Query an in-stock product:

```bash
curl "http://127.0.0.1:8080/inventory?sku=NS-JACKET-M-BLK"
```

Query an out-of-stock product:

```bash
curl "http://127.0.0.1:8080/inventory?sku=NS-TEE-L-WHT"
```

Check synchronization health:

```bash
curl "http://127.0.0.1:8080/health"
```

Stop each service with `Ctrl+C`.

## Run all tests

```bash
python3 -m unittest -v
```

The test suite covers warehouse retrieval, polling, cache updates, stock
queries, missing input, retry limits, non-retryable errors, and jitter.

## Day 3 files

- `inventory_service/warehouse.py` retrieves and validates warehouse data.
- `inventory_service/poller.py` schedules synchronization every five minutes.
- `inventory_service/cache.py` stores the latest inventory snapshot safely.
- `inventory_service/api.py` exposes health and stock-query endpoints.
- `mock_warehouse.py` provides a reproducible local warehouse API.
- `run_service.py` starts the poller and public query service.
- `test_inventory_service.py` tests the complete Day 3 design.
- `DAY3_BUILD_LOG.md` records requirements, tasks, decisions and evidence.

## Prototype goal

Demonstrate an unreliable operation that retries failures with increasing
delays, stops after a defined limit, and reports whether it eventually
succeeded or permanently failed.

## Run the Solo Recon prototype

Python 3 is the only requirement.

```bash
python3 retry_demo.py success
python3 retry_demo.py failure
```

The failure demonstration intentionally exits with status code `1` after the
maximum number of attempts.

Run the automated tests with:

```bash
python3 -m unittest -v
```

## Solo Recon files

- `retry_demo.py` contains the retry function and demonstration scenarios.
- `test_retry_demo.py` verifies success, maximum attempts, non-retryable
  errors, and jitter without making the tests wait.
- `LEARNING_JOURNAL.md` contains the assessment evidence.

See [LEARNING_JOURNAL.md](LEARNING_JOURNAL.md) for the baseline diagnostic,
scope, time record, blockers, and learning evidence.
