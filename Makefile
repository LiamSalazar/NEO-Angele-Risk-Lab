.PHONY: install test lint format ingest-sample etl etl-status build-gold expand-curated expand-all expand-max coverage rebuild-all ml-status ml leakage-audit risk risk-status risk-top api-info api app-dev simulate simulate-status gnn-status gnn-graph gnn gnn-compare frontend-install frontend-dev frontend-build frontend-test frontend-lint clean

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	python -m ruff check .
	python -m black --check .

format:
	python -m ruff check . --fix
	python -m black .

ingest-sample:
	python -m neo_ange.cli ingest sample

etl:
	python -m neo_ange.cli etl run-all

etl-status:
	python -m neo_ange.cli etl status

build-gold:
	python -m neo_ange.cli etl build-gold

expand-curated:
	python -m neo_ange.cli expand ingest-objects --strategy curated --limit 10

expand-all:
	python -m neo_ange.cli expand ingest-objects --strategy all --limit 100 --skip-existing

expand-max:
	python -m neo_ange.cli expand max --target 1000 --skip-existing --resume

coverage:
	python -m neo_ange.cli expand coverage

rebuild-all:
	python -m neo_ange.cli expand rebuild-all --target 1000

ml-status:
	python -m neo_ange.cli ml status

ml:
	python -m neo_ange.cli ml run-all

leakage-audit:
	python -m neo_ange.cli ml leakage-audit

risk:
	python -m neo_ange.cli risk build

risk-status:
	python -m neo_ange.cli risk status

risk-top:
	python -m neo_ange.cli risk top --limit 20

api-info:
	python -m neo_ange.cli api info

api:
	python -m neo_ange.cli api run

app-dev:
	python -m neo_ange.cli api run --host 127.0.0.1 --port 8000 --reload

simulate:
	python -m neo_ange.cli simulate batch --limit 50 --n-simulations 500

simulate-status:
	python -m neo_ange.cli simulate status

gnn-status:
	python -m neo_ange.cli gnn status

gnn-graph:
	python -m neo_ange.cli gnn build-graph --k 10 --min-nodes 100

gnn:
	python -m neo_ange.cli gnn run --target pha --k 10 --min-nodes 100

gnn-compare:
	python -m neo_ange.cli gnn compare

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run test

frontend-lint:
	cd frontend && npm run lint

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True); shutil.rmtree('htmlcov', ignore_errors=True); pathlib.Path('.coverage').unlink(missing_ok=True)"
