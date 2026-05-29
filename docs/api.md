# API

Run the local API with:

```bash
uvicorn neo_ange.api.main:app --reload
```

or:

```bash
python -m neo_ange.cli api run --host 127.0.0.1 --port 8000 --reload
```

The app import path is `neo_ange.api.main:app`. Local OpenAPI docs are available at `http://127.0.0.1:8000/docs`.

## Main endpoints

- `GET /health`
- `GET /status`
- `GET /objects`
- `GET /objects/{object_key}`
- `GET /rankings/top`
- `GET /rankings/summary`
- `GET /rankings/category/{category}`
- `POST /risk/build`
- `GET /risk/status`
- `GET /risk/explain/{object_key}`
- `GET /risk/methodology`
- `POST /simulations/object`
- `POST /simulations/batch`
- `GET /simulations/status`
- `GET /simulations/object/{object_key}/latest`

## Examples

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/rankings/top?limit=5
curl http://127.0.0.1:8000/risk/status
curl -X POST http://127.0.0.1:8000/simulations/batch \
  -H "Content-Type: application/json" \
  -d "{\"limit\": 10, \"n_simulations\": 500, \"random_state\": 42}"
```

## Data dependency

Risk endpoints expect `data/gold/neo_risk_features/` for score builds and `data/gold/risk_scores/risk_scores.parquet` for ranking/explanation reads. Simulation endpoints expect risk scores. When data is missing, endpoints return a clear message with the CLI command to run.
