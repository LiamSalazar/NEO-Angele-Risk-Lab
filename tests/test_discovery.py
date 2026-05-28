from __future__ import annotations

import json

import pandas as pd

from neo_ange.expansion.discovery import ObjectDiscoveryService


def test_discover_from_silver_cad(tmp_path) -> None:
    table = tmp_path / "silver" / "close_approaches"
    table.mkdir(parents=True)
    pd.DataFrame({"des": ["2026 AA", "2026 AA", " 433 "]}).to_parquet(table / "part.parquet")

    service = ObjectDiscoveryService(silver_root=tmp_path / "silver", bronze_root=tmp_path)

    assert service.discover_from_silver_cad() == ["2026 AA", "433"]


def test_discover_from_silver_sentry(tmp_path) -> None:
    sentry = tmp_path / "silver" / "sentry_objects"
    sentry.mkdir(parents=True)
    vi = tmp_path / "silver" / "sentry_virtual_impactors"
    vi.mkdir(parents=True)
    pd.DataFrame({"des": ["2026 AB"], "spk": ["1001"]}).to_parquet(sentry / "part.parquet")
    pd.DataFrame({"des": ["2026 AC"]}).to_parquet(vi / "part.parquet")

    service = ObjectDiscoveryService(silver_root=tmp_path / "silver", bronze_root=tmp_path)

    assert service.discover_from_silver_sentry() == ["2026 AB", "1001", "2026 AC"]


def test_discover_all_uses_bronze_and_curated_without_duplicates(tmp_path) -> None:
    cad_dir = tmp_path / "bronze" / "cad" / "ingest_date=2026-05-28"
    cad_dir.mkdir(parents=True)
    payload = {"fields": ["des", "dist"], "data": [["2026 AA", "0.1"], ["99942", "0.2"]]}
    (cad_dir / "cad.json").write_text(json.dumps({"data": payload}), encoding="utf-8")

    service = ObjectDiscoveryService(
        silver_root=tmp_path / "silver",
        bronze_root=tmp_path / "bronze",
    )

    assert service.curated_seed_objects(limit=2) == ["99942", "433"]
    assert service.discover_all(limit=5) == ["2026 AA", "99942", "433", "101955", "162173"]
    assert service.discover_from_silver_cad() == []
    assert service.warnings
