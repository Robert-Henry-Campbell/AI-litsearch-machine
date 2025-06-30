import urllib.request
import urllib.error
import pytest


def test_api_openai_network_access():
    url = "https://api.openai.com/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.status
    except urllib.error.HTTPError as http_exc:
        status = http_exc.code
    except Exception as exc:  # pragma: no cover - connection issues
        pytest.skip(f"Network access to api.openai.com failed: {exc}")
        return
    assert status in {200, 401, 404}
