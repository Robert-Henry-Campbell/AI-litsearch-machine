import pytest
from agent1.openai_client import OpenAIJSONCaller
from utils.secrets import get_openai_api_key
from tests.openai_test_utils import handle_openai_exception
from schemas.metadata import PaperMetadata


@pytest.mark.skip(reason="Live API call too expensive to run every time")
def test_openai_json_caller_live():
    try:
        get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    caller = OpenAIJSONCaller(model="gpt-3.5-turbo")
    snippet = (
        "Title: Example Study\n"
        "Authors: Doe et al. (2024)\n"
        "DOI: 10.1234/example\n"
        "Published: 2024-01-01\n"
        "Data Source: INTERVAL"
    )
    try:
        result = caller.call(snippet)
    except Exception as exc:  # pragma: no cover - live network error handling
        handle_openai_exception(exc)
        return
    PaperMetadata.model_validate(result)
    assert set(result) >= {
        "title",
        "authors",
        "doi",
        "pub_date",
        "data_sources",
        "omics_modalities",
        "targets",
        "p_threshold",
        "ld_r2",
        "outcome",
        "additional_QC",
    }


def test_openai_json_caller_offline(monkeypatch):
    """Offline version that bypasses the real API."""

    monkeypatch.setattr(
        OpenAIJSONCaller,
        "call",
        lambda self, _text, max_retries=2: {
            "title": "T",
            "doi": "10.1/example",
        },
    )

    caller = OpenAIJSONCaller(model="test")
    result = caller.call("hello")
    PaperMetadata.model_validate(result)
    assert result["title"] == "T"
