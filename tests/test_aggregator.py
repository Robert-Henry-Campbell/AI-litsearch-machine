import orjson
from aggregator import aggregate_metadata


def valid_data():
    return {
        "title": "T",
        "authors": "A",
        "doi": "10.1/abc",
        "pub_date": None,
        "data_sources": None,
        "omics_modalities": None,
        "targets": None,
        "p_threshold": None,
        "ld_r2": None,
    }


def test_aggregate_with_invalid_json(tmp_path, monkeypatch):
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    master = tmp_path / "master.json"
    error_log = tmp_path / "aggregation_errors.log"

    monkeypatch.setattr("aggregator.META_DIR", meta_dir)
    monkeypatch.setattr("aggregator.MASTER_PATH", master)
    monkeypatch.setattr("aggregator.ERROR_LOG", error_log)

    # valid file
    (meta_dir / "valid.json").write_bytes(orjson.dumps(valid_data()))
    # invalid file (wrong type)
    (meta_dir / "invalid.json").write_bytes(orjson.dumps({"title": 1}))

    results = aggregate_metadata()

    assert len(results) == 1
    assert master.exists()
    data = orjson.loads(master.read_bytes())
    assert len(data) == 1
    assert error_log.exists()
    log_content = error_log.read_text()
    assert "invalid.json" in log_content
