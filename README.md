# quantum_chess

## Deployment

This repository ships as a single container:
- FastAPI serves both the engine API and the built UI
- the frontend bundle is built into the Docker image
- the engine runs in the same container as the API

### Prerequisites

- Docker
- Docker Compose

### Run locally

Build and start the app:

```bash
docker compose up --build
```

Then open:
- UI: `http://localhost:8000`
- API: `http://localhost:8000/game`

### Run in background

```bash
docker compose up -d --build
```

### Stop the app

```bash
docker compose down
```

### Rebuild after code changes

```bash
docker compose down
docker compose up --build
```

### Notes

- Game state is stored in memory only. Restarting the container resets the game.
- The UI and API are served from the same FastAPI process, so there is no separate Nginx or frontend container.

## Selenium E2E testing (local macOS + Safari)

### Prerequisites

1. Install Python dependencies:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

2. Enable Safari WebDriver once on your machine:

```bash
safaridriver --enable
```

3. Ensure the app is reachable on `http://127.0.0.1:8000`.
   - The Selenium harness can auto-start the app via:
     `./.venv/bin/python -m uvicorn api.app:app --host 127.0.0.1 --port 8000`

### E2E profiles

Run Selenium smoke/full suites:

```bash
RUN_SELENIUM_E2E=1 ./.venv/bin/python -m unittest discover -s tests/e2e
```

### Stress profiles

Run both UI and backend stress tests:

```bash
RUN_SELENIUM_E2E=1 RUN_STRESS_TESTS=1 ./.venv/bin/python -m unittest discover -s tests/stress
```

Short stress example:

```bash
RUN_SELENIUM_E2E=1 RUN_STRESS_TESTS=1 UI_STRESS_ITERATIONS=10 BACKEND_STRESS_OPERATIONS=120 ./.venv/bin/python -m unittest discover -s tests/stress
```

Long stress example:

```bash
RUN_SELENIUM_E2E=1 RUN_STRESS_TESTS=1 UI_STRESS_ITERATIONS=120 BACKEND_STRESS_OPERATIONS=1200 BACKEND_STRESS_CONCURRENCY=12 ./.venv/bin/python -m unittest discover -s tests/stress
```

### Optional environment overrides

- `E2E_BASE_URL`: target app URL (default `http://127.0.0.1:8000`)
- `E2E_APP_SERVER_CMD`: command used by tests to start app if not already running
- `UI_STRESS_MAX_MEDIAN_SECONDS`: median loop latency threshold for UI stress
- `BACKEND_STRESS_P95_SECONDS`: p95 latency threshold for backend load profile
- `BACKEND_STRESS_MAX_4XX_RATE`: allowed client error rate under concurrent mixed load
