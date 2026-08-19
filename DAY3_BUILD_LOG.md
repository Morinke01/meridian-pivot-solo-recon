# Day 3: Original Polling Build

**Learner:** Morinke Julius  
**Date:** 19/08/2026  
**Branch:** `day3/polling-inventory-service`

## Original specification

Poll a warehouse API every five minutes, cache the latest stock information,
and expose an endpoint that answers stock-availability questions.

## Task breakdown

| Task | Priority | Estimate | Definition of Done | Status |
|---|---|---:|---|---|
| Define warehouse inventory payload | High | 30 min | Mock API returns products with SKU, name, and quantity | Done |
| Build warehouse API client | High | 45 min | Client retrieves and validates a warehouse snapshot | Done |
| Integrate retry/backoff | High | 30 min | Temporary connection and server failures are retried | Done |
| Implement inventory cache | High | 30 min | Latest snapshot and synchronization time can be queried safely | Done |
| Add five-minute scheduler | High | 45 min | Poller runs immediately and then every 300 seconds by default | Done |
| Expose stock query endpoint | High | 45 min | A SKU request returns quantity and `in_stock` status | Done |
| Add health endpoint | Medium | 20 min | Endpoint reports cached product count and last sync time | Done |
| Add automated tests | High | 45 min | Polling, caching, API queries, retries, and errors are tested | Done |
| Document setup and demo | Medium | 30 min | Another user can start and query both services | Done |
| Run end-to-end check | High | 20 min | Live warehouse data reaches both stock-query responses | Done |

No task exceeds four hours, and every Definition of Done is one checkable
outcome.

## Architecture decisions

- Python's standard library keeps setup small and reproducible.
- The warehouse client, poller, cache, and query API are separate modules.
- The cache is protected by a lock because polling and HTTP requests run in
  different threads.
- The default interval is 300 seconds, while a configurable shorter interval
  supports demonstrations and tests.
- Retry/backoff wraps only the warehouse request. Invalid data and other
  permanent failures are not retried.
- The complete warehouse snapshot replaces the cache atomically so consumers
  do not see a partially updated state.

## Verification evidence

### Automated checks

**Time:** 19/08/2026, 2:22 PM  
**Command:** `python3 -W error::ResourceWarning -m unittest -v`  
**Result:** All 9 tests passed in 2.107 seconds with resource warnings treated
as errors.

### Live end-to-end check

The mock warehouse and inventory service were started as separate processes.
The service used a one-second demonstration interval while retaining the
five-minute production default.

Observed responses:

```json
{"status": "ok", "product_count": 3, "last_synced_at": "2026-08-19T11:22:28.607679+00:00"}
```

```json
{"sku": "NS-JACKET-M-BLK", "name": "Northstar Jacket", "quantity": 8, "in_stock": true}
```

```json
{"sku": "NS-TEE-L-WHT", "name": "Northstar Tee", "quantity": 0, "in_stock": false}
```

## Day 3 completion check

- [x] Warehouse API is polled.
- [x] Production polling interval defaults to five minutes.
- [x] Latest stock is cached with a synchronization timestamp.
- [x] Query endpoint reports in-stock and out-of-stock products.
- [x] Retry/backoff is integrated around temporary warehouse failures.
- [x] Errors and invalid input return clear results.
- [x] Automated and live regression checks pass.

## Known limitations before the Day 4 pivot

- The cache is in memory and resets when the service restarts.
- The mock warehouse is for demonstration rather than production use.
- The HTTP endpoints do not yet use authentication or TLS.
- Polling can return data up to five minutes behind the warehouse.
- Multiple service instances would maintain separate caches.

These limitations are recorded now so the Day 4 Scope Delta Analysis can show
what the webhook pivot changes, removes, and leaves unresolved.
