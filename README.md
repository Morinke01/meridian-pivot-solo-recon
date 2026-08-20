# Meridian Pivot Inventory Service

Morinke Julius's Week 2 Solo Recon and inventory synchronization deliverable.

## Day 4 architecture

```text
Warehouse inventory event
        |
        | signed HTTP POST
        v
Signature and payload verification
        |
        v
Duplicate-event check
        |
        v
Thread-safe inventory cache
        |
        v
Stock query HTTP endpoint
```

The Day 3 poller, warehouse client, and mock polling API were removed from the
active branch. Their code and evidence remain available on
`day3/polling-inventory-service` and in `DAY3_BUILD_LOG.md`.

## Run the Day 4 service

Open two terminals in the repository.

Terminal 1 configures a demonstration secret and starts the receiver:

```bash
export NORTHSTAR_WEBHOOK_SECRET=demo-secret
python3 run_service.py
```

Terminal 2 uses the same secret to send a signed warehouse event:

```bash
export NORTHSTAR_WEBHOOK_SECRET=demo-secret
python3 send_webhook.py --event-id demo-001 --quantity 11
```

Send the same command again to demonstrate duplicate-event protection. The
first delivery returns `processed: true`; the repeated delivery returns
`duplicate: true`.

Query the updated stock:

```bash
curl "http://127.0.0.1:8080/inventory?sku=NS-JACKET-M-BLK"
```

Check that the active synchronization mode is webhook:

```bash
curl "http://127.0.0.1:8080/health"
```

Send an event using a different secret to demonstrate signature rejection:

```bash
NORTHSTAR_WEBHOOK_SECRET=wrong-secret \
  python3 send_webhook.py --event-id forged-001 --quantity 99
```

The forged event receives HTTP `401` and does not change the cache. Stop the
service with `Ctrl+C`.

## Run all tests

```bash
python3 -m unittest -v
```

The test suite covers signed events, invalid signatures, payload validation,
duplicate protection, cache updates, stock-query regressions, and the original
Solo Recon retry behavior.

## Day 4 files

- `inventory_service/cache.py` stores the latest inventory snapshot safely.
- `inventory_service/webhook.py` verifies signatures, validates events, and
  blocks duplicate processing.
- `inventory_service/api.py` exposes the webhook, health, and stock-query
  endpoints.
- `send_webhook.py` creates signed demonstration events.
- `run_service.py` starts the webhook and stock-query service.
- `test_inventory_service.py` verifies the pivot and regression behavior.
- `DAY4_PIVOT_LOG.md` records the forced change and its immediate impact.
- `DAY3_BUILD_LOG.md` preserves evidence of the superseded polling design.

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
