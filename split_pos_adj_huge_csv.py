from __future__ import annotations

from pathlib import Path


INPUT_FILE = Path(
    "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/PoS_adj_HUGE.csv"
)
OUTPUT_DIR = Path(
    "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv"
)
LINES_PER_FILE = 100
OUTPUT_PREFIX = "PoS_adj_"


def chunk_lines(lines: list[str], chunk_size: int) -> list[list[str]]:
    return [lines[index : index + chunk_size] for index in range(0, len(lines), chunk_size)]


def write_chunks() -> int:
    lines = [line for line in INPUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    chunks = chunk_lines(lines, LINES_PER_FILE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for index, chunk in enumerate(chunks, start=1):
        output_file = OUTPUT_DIR / f"{OUTPUT_PREFIX}{index:02d}.csv"
        output_file.write_text("\n".join(chunk) + "\n", encoding="utf-8")

    return len(chunks)


def main() -> int:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    chunk_count = write_chunks()
    print(f"Created {chunk_count} files in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())