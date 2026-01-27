from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.mods.file_search import FileSearch


@pytest.fixture
def fs() -> FileSearch:
    return FileSearch(metadata_controller=MagicMock())


@pytest.mark.parametrize(
    "content,search_text,case_sensitive,use_regex,expected",
    [
        ("hello world", "world", False, False, True),
        ("hello world", "WORLD", False, False, True),
        ("hello world", "WORLD", True, False, False),
        ("abc123", r"\d+", False, True, True),
        ("abcdef", r"\d+", False, True, False),
        ("abc123", r"\D+", True, True, True),
        ("", "anything", False, False, False),
    ],
)
def test_matches(
    fs: FileSearch,
    content: str,
    search_text: str,
    case_sensitive: bool,
    use_regex: bool,
    expected: bool,
) -> None:
    assert fs._matches(content, search_text, case_sensitive, use_regex) is expected


def test_get_preview_returns_context(fs: FileSearch) -> None:
    content = "\n".join(f"line{i}" for i in range(10))
    preview = fs._get_preview(content, "line5", False)
    assert "line5" in preview
    assert "line3" in preview
    assert "line7" in preview


def test_get_preview_no_match(fs: FileSearch) -> None:
    assert fs._get_preview("nothing here", "missing", False) == ""


def test_search_finds_matching_file(fs: FileSearch, tmp_path: Path) -> None:
    target = tmp_path / "sub"
    target.mkdir()
    (target / "note.txt").write_text("the quick brown fox", encoding="utf-8")
    (target / "other.txt").write_text("unrelated content", encoding="utf-8")
    results = list(
        fs.search(
            "brown",
            [str(target)],
            {"case_sensitive": False, "ignore_extensions": []},
        )
    )
    assert len(results) == 1
    assert results[0]["file_path"].endswith("note.txt")
    assert "brown" in results[0]["preview"]


def test_search_respects_ignore_extensions(fs: FileSearch, tmp_path: Path) -> None:
    target = tmp_path / "sub"
    target.mkdir()
    (target / "a.txt").write_text("match here", encoding="utf-8")
    (target / "b.log").write_text("match here", encoding="utf-8")
    results = list(
        fs.search(
            "match",
            [str(target)],
            {"case_sensitive": False, "ignore_extensions": [".log"]},
        )
    )
    paths = [r["file_path"] for r in results]
    assert any(p.endswith("a.txt") for p in paths)
    assert not any(p.endswith("b.log") for p in paths)


def test_search_only_included_extensions(fs: FileSearch, tmp_path: Path) -> None:
    target = tmp_path / "sub"
    target.mkdir()
    (target / "a.txt").write_text("match here", encoding="utf-8")
    (target / "b.xml").write_text("match here", encoding="utf-8")
    results = list(
        fs.search(
            "match",
            [str(target)],
            {"case_sensitive": False, "file_extensions": [".xml"]},
        )
    )
    paths = [r["file_path"] for r in results]
    assert any(p.endswith("b.xml") for p in paths)
    assert not any(p.endswith("a.txt") for p in paths)


def test_callback_invoked(fs: FileSearch, tmp_path: Path) -> None:
    target = tmp_path / "sub"
    target.mkdir()
    (target / "a.txt").write_text("needle in haystack", encoding="utf-8")
    captured: list[Any] = []
    list(
        fs.search(
            "needle",
            [str(target)],
            {"case_sensitive": False, "ignore_extensions": []},
            result_callback=lambda *args: captured.append(args),
        )
    )
    assert len(captured) == 1
    assert captured[0][0].endswith("a.txt")
