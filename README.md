# Meridian Pivot Solo Recon

Morinke Julius's Week 2 mini-prototype and learning evidence for the
**retry and backoff** concept.

## Prototype goal

Demonstrate an unreliable operation that retries failures with increasing
delays, stops after a defined limit, and reports whether it eventually
succeeded or permanently failed.

## Run the prototype

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

## Files

- `retry_demo.py` contains the retry function and demonstration scenarios.
- `test_retry_demo.py` verifies success, maximum attempts, non-retryable
  errors, and jitter without making the tests wait.
- `LEARNING_JOURNAL.md` contains the assessment evidence.

See [LEARNING_JOURNAL.md](LEARNING_JOURNAL.md) for the baseline diagnostic,
scope, time record, blockers, and learning evidence.
