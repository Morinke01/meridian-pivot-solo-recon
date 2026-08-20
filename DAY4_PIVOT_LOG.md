# Day 4: Mandatory Webhook Pivot

**Learner:** Morinke Julius  
**Date:** 20/08/2026  
**Pivot branch:** `day4/webhook-inventory-pivot`  
**Pivot branch created:** 20/08/2026, 9:30 AM EAT

## Client change

The client announced that warehouse polling would be discontinued within 48
hours. The delivery date did not change, and retaining polling as the active
integration method was not allowed.

## Architecture before the pivot

```text
Warehouse API <- request every five minutes <- poller -> cache -> query API
```

## Architecture after the pivot

```text
Warehouse -> signed webhook -> verification -> duplicate check -> cache -> query API
```

## Immediate scope delta

### Dropped

- Five-minute polling scheduler
- Outbound warehouse inventory client
- Mock warehouse polling endpoint
- Polling interval configuration

The obsolete files were deleted from the active Day 4 branch. They remain
visible in Git history and on the Day 3 branch as audit evidence.

### Modified

- Inventory cache now updates one affected product per event rather than
  replacing a complete warehouse snapshot.
- Service startup now requires a webhook secret instead of a warehouse URL and
  polling interval.
- Health response now reports `sync_mode: webhook`.
- Inventory tests now exercise pushed events while retaining stock-query
  regression checks.

### Added

- `POST /webhooks/inventory`
- HMAC-SHA256 signature verification
- Inventory-event schema validation
- Duplicate-event protection using `event_id`
- Payload-size limit
- Demonstration webhook sender
- Tests for valid, forged, duplicate, and invalid events

## Reprioritized backlog

| Priority | Task | Definition of Done | Status |
|---|---|---|---|
| P0 | Remove polling runtime | No polling process or scheduler runs on Day 4 | Done |
| P0 | Verify webhook signatures | Incorrect shared secrets receive HTTP 401 | Done |
| P0 | Process inventory events | Valid event updates the cached product | Done |
| P0 | Preserve stock queries | Existing GET query returns webhook-updated stock | Done |
| P1 | Prevent duplicates | Repeated event ID is acknowledged without reprocessing | Done |
| P1 | Validate payloads | Invalid events receive HTTP 422 | Done |
| P1 | Run regression tests | Pivot and Solo Recon tests pass together | Done |
| P2 | Document final trade-offs | Day 5 Scope Delta records cost and remaining risk | Pending |

## Integrity and security decisions

- Signatures are calculated from the exact request bytes before JSON parsing.
- `hmac.compare_digest` is used for constant-time signature comparison.
- The shared secret comes from `NORTHSTAR_WEBHOOK_SECRET` and is never stored
  in Git.
- Only `inventory.updated` events with valid product data are accepted.
- Event IDs make delivery idempotent because webhook senders commonly retry.
- Invalid signatures cannot update or create cached inventory.

## Day 4 verification

### Automated result

All 11 tests passed. The suite includes seven webhook/inventory tests and four
Solo Recon retry/backoff tests.

### Live result

1. Signed event `demo-001` set Jacket quantity to 11 and returned
   `processed: true`.
2. Repeating `demo-001` returned `duplicate: true` and did not process again.
3. The unchanged stock-query endpoint returned quantity 11 and
   `in_stock: true`.
4. Health reported `sync_mode: webhook`.
5. An event signed with a different secret received HTTP 401.

### Learner manual verification

**Completed:** 20/08/2026, 9:47 AM EAT

Morinke independently repeated the complete Day 4 demonstration in the VS
Code terminal:

1. Health initially returned `sync_mode: webhook`, zero cached products, and
   no synchronization timestamp.
2. Signed event `demo-001` was processed and set the Jacket quantity to 11.
3. The stock-query endpoint returned `in_stock: true` and quantity 11.
4. Repeating `demo-001` returned `processed: false` and `duplicate: true`.
5. New event `demo-002` changed the same product to quantity 0, after which
   the query returned `in_stock: false`.
6. Event `forged-001`, signed with the wrong secret, received HTTP 401 and was
   rejected.
7. The full regression suite ran 11 tests in 3.582 seconds and returned `OK`.

## Immediate pivot cost

- Three polling-specific files were removed from the active branch.
- The startup flow and inventory tests required substantial replacement.
- Work already completed for polling remains useful only as audit evidence and
  as a comparison point for the Scope Delta Analysis.
- Persistence, distributed duplicate storage, TLS termination, and secret
  rotation remain outside the MVP scope.

The final elapsed-time cost and complete trade-off analysis will be recorded
on Day 5 after the refactor is packaged and reviewed.
