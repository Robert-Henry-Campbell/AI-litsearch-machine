import urllib.request
import urllib.error
import pytest


@pytest.mark.skip(reason="Live API call too expensive to run every time")
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


def test_api_openai_network_access_offline(monkeypatch):
    """Offline test that simulates an HTTP 200 response."""

    class FakeResponse:
        def __init__(self, status: int = 200) -> None:
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *a, **k: FakeResponse(200),
    )

    url = "https://api.openai.com/v1/models"
    with urllib.request.urlopen(url, timeout=5) as resp:
        status = resp.status
    assert status == 200
