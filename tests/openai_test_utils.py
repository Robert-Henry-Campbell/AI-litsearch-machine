import openai
import pytest


def handle_openai_exception(exc: Exception) -> None:
    """Skip the current test based on the OpenAI exception ``exc``."""
    message = str(exc).lower()
    if isinstance(exc, openai.RateLimitError):
        if "quota" in message or "insufficient" in message:
            pytest.skip(f"OpenAI quota exceeded: {exc}")
        else:
            pytest.skip(f"OpenAI rate limit reached: {exc}")
    elif isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
        pytest.skip(f"OpenAI authentication failed: {exc}")
    elif isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        pytest.skip(f"Network error contacting OpenAI: {exc}")
    elif isinstance(exc, openai.APIStatusError):
        status = getattr(exc, "status_code", None)
        pytest.skip(f"OpenAI API status {status}: {exc}")
    elif isinstance(exc, openai.OpenAIError):
        pytest.skip(f"OpenAI error: {exc}")
    else:
        raise exc


def ensure_openai_working() -> None:
    """Perform a trivial OpenAI call to verify API availability."""
    client = openai.OpenAI()
    try:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
    except Exception as exc:  # pragma: no cover - live network errors
        handle_openai_exception(exc)
