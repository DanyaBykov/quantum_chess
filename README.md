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
