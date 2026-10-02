"""Print file / raw-LOC / curated-LOC / test counts so AGENTS.md stays in sync.

Re-measure instead of trusting stale doc numbers (prevents count drift).
Designed for Windows PowerShell invocation but runs anywhere:

    uv run python scripts/stats.py
"""

from __future__ import annotations

import pathlib

APP = pathlib.Path("app")
TESTS = pathlib.Path("tests")
LOCALES = pathlib.Path("locales")


def py_files(base: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in base.rglob("*.py") if "__pycache__" not in p.parts]


def raw_loc(path: pathlib.Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def curated_loc(path: pathlib.Path) -> int:
    n = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        n += 1
    return n


def summarize(label: str, base: pathlib.Path) -> None:
    files = py_files(base)
    raw = sum(raw_loc(p) for p in files)
    curated = sum(curated_loc(p) for p in files)
    print(
        f"{label}: {len(files)} .py files | raw LOC {raw:,} | curated LOC {curated:,}"
    )


def sizes(base: pathlib.Path, limit: int = 10) -> None:
    files = sorted(py_files(base), key=raw_loc, reverse=True)[:limit]
    print(f"\nLargest files in {base}/ (raw / curated LOC):")
    for p in files:
        print(f"  {raw_loc(p):6d} / {curated_loc(p):6d}  {p}")


def main() -> None:
    summarize("app", APP)
    summarize("tests", TESTS)
    sizes(APP)
    ts = sorted(LOCALES.glob("*.ts")) if LOCALES.exists() else []
    qm = sorted(LOCALES.glob("*.qm")) if LOCALES.exists() else []
    print(
        f"\nlocales/*.ts: {len(ts)} | locales/*.qm: {len(qm)} (.qm are git-ignored build artifacts)"
    )


if __name__ == "__main__":
    main()
