from pathlib import Path
import pytest

from utils.secrets import get_openai_api_key


def test_env_var_priority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file = tmp_path / "key.txt"
    file.write_text("file-key")
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(file))
    assert get_openai_api_key() == "env-key"


def test_file_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    key_file = tmp_path / "key.txt"
    key_file.write_text("file-key")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(key_file))
    assert get_openai_api_key() == "file-key"


def test_missing_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    missing = tmp_path / "does_not_exist"
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(missing))
    with pytest.raises(RuntimeError):
        get_openai_api_key()
