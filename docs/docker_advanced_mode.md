# Docker Advanced Mode

Docker Compose now exposes both the API and frontend:

- FastAPI: `http://127.0.0.1:8000`
- Vite frontend: `http://127.0.0.1:5174`

## Run

```bash
docker compose up --build
```

## API Commands

```bash
docker compose run --rm app python -m neo_ange.cli final build-all --target 4000
docker compose run --rm app python -m neo_ange.cli findings build
docker compose run --rm app python -m neo_ange.cli orbital-sim batch --limit 50 --n-clones 300
docker compose run --rm app python -m neo_ange.cli benchmark run
```

The backend image installs the GNN extra so advanced graph dependencies can be available in container mode. The frontend service uses Vite on port 5174 and points to the API on port 8000.
