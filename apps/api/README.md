# Transaction Classifier API

FastAPI backend for transaction classification.

## Setup

```bash
cd apps/api
uv sync
```

## Running

```bash
uv run api
```

## Logging

Robust logging is implemented using the standard Python `logging` library.
- **Console:** Logs are sent to stdout.
- **File:** Logs are stored in `apps/api/logs/app.log` with a rolling window (5MB per file, 5 backups).
- **Config:** Use the `LOG_LEVEL` environment variable to change the verbosity (DEBUG, INFO, WARNING, ERROR). Defaults to `INFO`.
