import openai
import pytest
from utils.secrets import get_openai_api_key


def test_openai_api_connection():
    try:
        api_key = get_openai_api_key()
    except RuntimeError:
        pytest.skip("OPENAI_API_KEY not found")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=1,
    )
    assert response.choices[0].message.content
