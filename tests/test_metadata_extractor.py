import sys
import types
from pathlib import Path

import orjson


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def call(self, text, *, max_retries=2):
        self.calls += 1
        return self.responses.pop(0)


def setup_module(module):
    sys.modules["openai"] = types.ModuleType("openai")


def teardown_module(module):
    for mod in ("agent1.metadata_extractor", "agent1.openai_client", "openai"):
        sys.modules.pop(mod, None)


def create_text_file(tmp_path: Path, name: str) -> Path:
    path = tmp_path / f"{name}.json"
    data = {"pages": [{"page": 1, "text": "dummy text"}]}
    path.write_bytes(orjson.dumps(data))
    return path


def valid_data() -> dict:
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


def test_extract_success(tmp_path, monkeypatch):
    from agent1.metadata_extractor import MetadataExtractor

    text_path = create_text_file(tmp_path, "test")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    client = FakeClient([valid_data()])
    extractor = MetadataExtractor(client=client)
    result = extractor.extract(text_path, "Drug")
    assert result is not None
    out_file = tmp_path / "meta" / "10.1_abc.json"
    assert out_file.exists()
    assert client.calls == 1


def test_extract_retry(tmp_path, monkeypatch):
    from agent1.metadata_extractor import MetadataExtractor

    text_path = create_text_file(tmp_path, "test")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    client = FakeClient([{"title": 1}, valid_data()])
    extractor = MetadataExtractor(client=client)
    result = extractor.extract(text_path, "Drug")
    assert result is not None
    assert client.calls == 2


def test_extract_fail(tmp_path, monkeypatch):
    from agent1.metadata_extractor import MetadataExtractor

    text_path = create_text_file(tmp_path, "test")
    monkeypatch.setattr("agent1.metadata_extractor.META_DIR", tmp_path / "meta")
    client = FakeClient([{"title": 1}, {"title": 2}])
    extractor = MetadataExtractor(client=client)
    result = extractor.extract(text_path, "Drug")
    assert result is None
    assert client.calls == 2
    assert not list((tmp_path / "meta").glob("*.json"))
