from __future__ import annotations

import json

from neo_ange.services.bronze_storage import BronzeStorage


def test_save_json_creates_file_with_metadata_and_data(tmp_path) -> None:
    storage = BronzeStorage(tmp_path)

    path = storage.save_json(
        source="sbdb_query",
        payload={"signature": {"source": "NASA/JPL"}, "data": [{"spkid": "1"}]},
        query_params={"limit": 1},
    )

    assert path.exists()
    assert "sbdb_query" in str(path)
    assert "ingest_date=" in str(path)

    wrapper = json.loads(path.read_text(encoding="utf-8"))
    assert wrapper["metadata"]["source"] == "sbdb_query"
    assert wrapper["metadata"]["query_params"] == {"limit": 1}
    assert wrapper["metadata"]["api_signature"] == {"source": "NASA/JPL"}
    assert wrapper["data"]["data"] == [{"spkid": "1"}]


def test_latest_file_returns_most_recent_path(tmp_path) -> None:
    storage = BronzeStorage(tmp_path)

    first = storage.save_json("cad", {"signature": {}, "data": []}, object_id="first")
    second = storage.save_json("cad", {"signature": {}, "data": []}, object_id="second")

    assert storage.latest_file("cad") == max([first, second], key=lambda path: str(path))


def test_list_files_can_filter_by_source(tmp_path) -> None:
    storage = BronzeStorage(tmp_path)
    storage.save_json("cad", {"signature": {}, "data": []})
    storage.save_json("sentry", {"signature": {}, "data": []})

    files = storage.list_files("cad")

    assert len(files) == 1
    assert "cad" in str(files[0])
