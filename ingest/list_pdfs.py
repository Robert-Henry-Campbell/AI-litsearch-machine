from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "pdfs"


def list_pdfs() -> list[str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return [p.name for p in DATA_DIR.glob("*.pdf")]


if __name__ == "__main__":
    for name in list_pdfs():
        print(name)
