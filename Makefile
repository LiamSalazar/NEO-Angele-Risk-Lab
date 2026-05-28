.PHONY: install test lint format ingest-sample etl etl-status build-gold clean

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

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True); shutil.rmtree('htmlcov', ignore_errors=True); pathlib.Path('.coverage').unlink(missing_ok=True)"
