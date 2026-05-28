from __future__ import annotations

from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    list_manifests,
    load_latest_manifest,
    save_manifest,
)


def test_create_run_id_includes_run_type() -> None:
    run_id = create_run_id("ingestion")

    assert run_id.startswith("ingestion_")
    assert run_id.endswith("Z")


def test_save_load_and_list_manifests(tmp_path) -> None:
    first = RunManifest(
        run_id="etl_20260528T000000000001Z",
        run_type="etl",
        started_at_utc="2026-05-28T00:00:00Z",
        ended_at_utc="2026-05-28T00:00:01Z",
        status="success",
        metrics={"rows": 1},
    )
    second = RunManifest(
        run_id="etl_20260528T000000000002Z",
        run_type="etl",
        started_at_utc="2026-05-28T00:00:02Z",
        ended_at_utc="2026-05-28T00:00:03Z",
        status="partial_success",
    )

    first_path = save_manifest(first, output_dir=tmp_path)
    second_path = save_manifest(second, output_dir=tmp_path)

    assert first_path.exists()
    assert second_path.exists()
    assert list_manifests("etl", output_dir=tmp_path) == [first_path, second_path]
    latest = load_latest_manifest("etl", output_dir=tmp_path)
    assert latest is not None
    assert latest["status"] == "partial_success"
    assert list_manifests("ml", output_dir=tmp_path) == []
