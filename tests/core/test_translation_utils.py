"""Unit tests for the in-app translation utilities (``app.core.translation_utils``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import lxml.etree as ET
import pytest

from app.core import translation_utils as tu


def _make_ts(path: Path, messages: list[tuple[str, str, str | None]]) -> Path:
    """Write a .ts file. ``messages`` = list of (source, translation, type)."""
    root = ET.Element("TS", language="de_DE")
    ctx = ET.SubElement(root, "context")
    name = ET.SubElement(ctx, "name")
    name.text = "MyContext"
    for src, tr, typ in messages:
        msg = ET.SubElement(ctx, "message")
        s = ET.SubElement(msg, "source")
        s.text = src
        t = ET.SubElement(msg, "translation")
        if typ:
            t.set("type", typ)
        t.text = tr
    tu.save_ts_file(ET.ElementTree(root), path)
    return path


# ---------------------------------------------------------------------------
# should_skip_translation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", True),
        ("a", True),
        ("1", True),
        ("!@#", True),
        ("Hello", False),
        ("Hello World", False),
    ],
)
def test_should_skip_translation(text: str, expected: bool) -> None:
    assert tu.should_skip_translation(text) is expected


# ---------------------------------------------------------------------------
# find_unfinished_translations
# ---------------------------------------------------------------------------


def test_find_unfinished(locales_tmp: Path) -> None:
    ts = _make_ts(
        locales_tmp / "de_DE.ts",
        [("Hello", "", "unfinished"), ("World", "World", None), ("Skip", "", "")],
    )
    tree: Any = ET.parse(str(ts))
    items = tu.find_unfinished_translations(tree)
    sources = [i.source for i in items]
    assert "Hello" in sources
    assert "Skip" in sources  # empty translation counts as unfinished
    assert "World" not in sources  # translated, no type


def test_find_unfinished_empty_tree() -> None:
    root = ET.Element("TS", language="de_DE")
    tree = ET.ElementTree(root)
    assert tu.find_unfinished_translations(tree) == []


# ---------------------------------------------------------------------------
# translate_one_async
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_one_async_success() -> None:
    item = tu.UnfinishedItem(context="c", source="Hello", element=object())
    svc = AsyncMock()
    svc.translate.return_value = "Hallo"
    result = await tu.translate_one_async(item, "de_DE", "en_US", svc, 10.0)
    assert result == "Hallo"
    svc.translate.assert_awaited_once_with("Hello", "de_DE", "en_US")


@pytest.mark.asyncio
async def test_translate_one_async_skips_trivial() -> None:
    item = tu.UnfinishedItem(context="c", source="a", element=object())
    svc = AsyncMock()
    result = await tu.translate_one_async(item, "de_DE", "en_US", svc, 10.0)
    assert result == ""
    svc.translate.assert_not_called()


@pytest.mark.asyncio
async def test_translate_one_async_handles_failure() -> None:
    item = tu.UnfinishedItem(context="c", source="Hello", element=object())
    svc = AsyncMock()
    svc.translate.side_effect = RuntimeError("boom")
    result = await tu.translate_one_async(item, "de_DE", "en_US", svc, 10.0)
    assert result == ""  # failures are swallowed and reported as empty


# ---------------------------------------------------------------------------
# translate_language_batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_language_batch_success(locales_tmp: Path) -> None:
    ts = _make_ts(
        locales_tmp / "de_DE.ts",
        [("Hello", "", "unfinished"), ("World", "", "unfinished")],
    )
    svc = AsyncMock()
    svc.translate.side_effect = ["Hallo", "Welt"]
    done: list[tuple[str, str]] = []
    translated, failed = await tu.translate_language_batch(
        "de_DE", svc, on_item_done=lambda i, s, t: done.append((s, t))
    )
    assert (translated, failed) == (2, 0)
    assert done == [("Hello", "Hallo"), ("World", "Welt")]
    # The .ts file on disk was actually updated
    tree: Any = ET.parse(str(ts))
    texts = [
        m.find("translation").text
        for m in tree.getroot().find("context").findall("message")
    ]
    assert texts == ["Hallo", "Welt"]


@pytest.mark.asyncio
async def test_translate_language_batch_no_unfinished(locales_tmp: Path) -> None:
    _make_ts(locales_tmp / "de_DE.ts", [("Hello", "Hallo", None)])
    svc = AsyncMock()
    translated, failed = await tu.translate_language_batch("de_DE", svc)
    assert (translated, failed) == (0, 0)
    svc.translate.assert_not_called()


@pytest.mark.asyncio
async def test_translate_language_batch_missing_file(locales_tmp: Path) -> None:
    errors: list[str] = []
    translated, failed = await tu.translate_language_batch(
        "fr_FR", AsyncMock(), on_error=lambda m: errors.append(m)
    )
    assert (translated, failed) == (0, 0)
    assert errors and "File not found" in errors[0]


@pytest.mark.asyncio
async def test_translate_language_batch_counts_real_failure(
    locales_tmp: Path,
) -> None:
    # 'a' is skipped (single char -> no API call, not a failure);
    # 'Hello' calls the service which returns "" -> a real failure.
    _make_ts(
        locales_tmp / "de_DE.ts",
        [("a", "", "unfinished"), ("Hello", "", "unfinished")],
    )
    svc = AsyncMock()
    svc.translate.side_effect = [""]  # only 'Hello' is actually translated
    translated, failed = await tu.translate_language_batch("de_DE", svc)
    assert (translated, failed) == (0, 1)


# ---------------------------------------------------------------------------
# save_ts_file
# ---------------------------------------------------------------------------


def test_save_ts_file_preserves_doctype(tmp_path: Path) -> None:
    root = ET.Element("TS", language="de_DE")
    out = tmp_path / "out.ts"
    tu.save_ts_file(ET.ElementTree(root), out)
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE TS>" in content
    assert 'language="de_DE"' in content


# ---------------------------------------------------------------------------
# get_translation_languages
# ---------------------------------------------------------------------------


def test_get_translation_languages_excludes_source(locales_tmp: Path) -> None:
    (locales_tmp / "en_US.ts").write_text("<TS></TS>")
    (locales_tmp / "de_DE.ts").write_text("<TS></TS>")
    (locales_tmp / "fr_FR.ts").write_text("<TS></TS>")
    assert tu.get_translation_languages() == ["de_DE", "fr_FR"]


# ---------------------------------------------------------------------------
# validate_translation
# ---------------------------------------------------------------------------


def test_validate_fixes_placeholder_mismatch(locales_tmp: Path) -> None:
    _make_ts(locales_tmp / "de_DE.ts", [("Hello {name}", "Hallo", "")])
    issues, fixed = tu.validate_translation("de_DE")
    assert fixed >= 1
    tree: Any = ET.parse(str(locales_tmp / "de_DE.ts"))
    tr = tree.getroot().find("context").find("message").find("translation")
    assert "{name}" in (tr.text or "")


def test_validate_adds_missing_language_attr(locales_tmp: Path) -> None:
    root = ET.Element("TS")  # no language attribute
    ctx = ET.SubElement(root, "context")
    nm = ET.SubElement(ctx, "name")
    nm.text = "C"
    msg = ET.SubElement(ctx, "message")
    s = ET.SubElement(msg, "source")
    s.text = "Hi"
    t = ET.SubElement(msg, "translation")
    t.text = "Hallo"
    tu.save_ts_file(ET.ElementTree(root), locales_tmp / "de_DE.ts")

    issues, fixed = tu.validate_translation("de_DE")
    assert fixed >= 1
    tree: Any = ET.parse(str(locales_tmp / "de_DE.ts"))
    assert tree.getroot().get("language") == "de_DE"
