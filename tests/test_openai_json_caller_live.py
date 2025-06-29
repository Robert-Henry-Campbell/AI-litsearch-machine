import pytest
from agent1.openai_client import OpenAIJSONCaller
from utils.secrets import get_openai_api_key
from schemas.metadata import PaperMetadata


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
    result = caller.call(snippet)
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
    }
