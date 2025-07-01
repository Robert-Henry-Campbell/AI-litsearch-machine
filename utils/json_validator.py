from __future__ import annotations

from pathlib import Path
import orjson

BASE_DIR = Path("data")
META_DIR = BASE_DIR / "meta"
MASTER_PATH = BASE_DIR / "master.json"


def set_base_dir(base_dir: Path) -> None:
    """Update path constants based on ``base_dir``."""
    global BASE_DIR, META_DIR, MASTER_PATH
    BASE_DIR = Path(base_dir)
    META_DIR = BASE_DIR / "meta"
    MASTER_PATH = BASE_DIR / "master.json"


def validate_file(path: Path) -> bool:
    try:
        raw = path.read_bytes()
        raw.decode("utf-8")
        orjson.loads(raw)
    except Exception as exc:
        print(f"Invalid JSON in {path}: {exc}")
        return False
    return True


def main() -> int:
    paths = list(META_DIR.glob("*.json"))
    if MASTER_PATH.exists():
        paths.append(MASTER_PATH)
    if not paths:
        print("No JSON files found.")
        return 0
    all_valid = True
    for path in paths:
        if not validate_file(path):
            all_valid = False
    if all_valid:
        print("All JSON files are valid UTF-8 and well-formed.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
