"""Tests for ``app.mods.db_builder`` (leaf layer, pure orchestration logic).

The ``DatabaseBuilder`` singleton's ``__init__`` wires a ``MetadataController``
and Qt objects, so these tests construct the instance via ``__new__`` and set
only the attributes the pure helper methods need (``metadata_controller`` for
``_filter_existing_mods``, ``settings`` where relevant). The tested methods are
the side-effect-free data transforms: JSON loading, existing-mod filtering,
dependency extraction/comparison, and report building.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

from app.models.metadata.metadata_structure import (
    AboutXmlMod,
    CaseInsensitiveStr,
    ModType,
)
from app.mods.db_builder import DatabaseBuilder


def _make_builder(mods_metadata: dict[str, Any]) -> DatabaseBuilder:
    # Bypass __init__ (which requires a Qt MetadataController singleton).
    builder = DatabaseBuilder.__new__(DatabaseBuilder)
    builder.metadata_controller = cast(
        Any, SimpleNamespace(mods_metadata=mods_metadata)
    )
    builder.settings = MagicMock()
    return builder


def _make_mod(package_id: str, pfid: str, mod_type: ModType) -> AboutXmlMod:
    mod = AboutXmlMod(
        name=package_id,
        package_id=CaseInsensitiveStr(package_id),
        _uuid=package_id,
        _mod_type=mod_type,
    )
    if pfid:
        mod.published_file_id = pfid
    return mod


# ---------------------------------------------------------------------------
# _load_json_database
# ---------------------------------------------------------------------------


def test_load_json_database_missing_file(tmp_path: Path) -> None:
    builder = _make_builder({})
    assert builder._load_json_database(str(tmp_path / "nope.json")) is None


def test_load_json_database_valid(tmp_path: Path) -> None:
    path = tmp_path / "db.json"
    path.write_text('{"database": {"1": {"name": "Mod"}}}', encoding="utf-8")
    builder = _make_builder({})
    assert builder._load_json_database(str(path)) == {
        "database": {"1": {"name": "Mod"}}
    }


def test_load_json_database_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "db.json"
    path.write_text("{not valid json", encoding="utf-8")
    builder = _make_builder({})
    assert builder._load_json_database(str(path)) is None


# ---------------------------------------------------------------------------
# _filter_existing_mods
# ---------------------------------------------------------------------------


def test_filter_existing_mods_steamcmd() -> None:
    mods = {
        "a": _make_mod("mod.a", "111", ModType.STEAM_CMD),
        "b": _make_mod("mod.b", "222", ModType.STEAM_WORKSHOP),
        "c": _make_mod("mod.c", "333", ModType.STEAM_CMD),
    }
    builder = _make_builder(mods)

    result = builder._filter_existing_mods(["111", "222", "333"], "steamcmd")

    # SteamCMD mods (111, 333) filtered out; workshop (222) kept.
    assert result == ["222"]


def test_filter_existing_mods_steamworks() -> None:
    mods = {
        "a": _make_mod("mod.a", "111", ModType.STEAM_CMD),
        "b": _make_mod("mod.b", "222", ModType.STEAM_WORKSHOP),
    }
    builder = _make_builder(mods)

    result = builder._filter_existing_mods(["111", "222"], "steamworks")

    # Workshop mod (222) filtered out; steamcmd (111) kept.
    assert result == ["111"]


def test_filter_existing_mods_ignores_mods_without_pfid() -> None:
    mods = {"a": _make_mod("mod.a", "", ModType.STEAM_CMD)}
    builder = _make_builder(mods)

    result = builder._filter_existing_mods(["999"], "steamcmd")

    assert result == ["999"]


# ---------------------------------------------------------------------------
# _extract_dependencies
# ---------------------------------------------------------------------------


def test_extract_dependencies() -> None:
    builder = _make_builder({})
    db = {
        "database": {
            "111": {"dependencies": ["222", "333"]},
            "222": {"dependencies": []},
        }
    }

    deps = builder._extract_dependencies(db)

    assert deps == {"111": {"222", "333"}, "222": set()}


# ---------------------------------------------------------------------------
# _compare_dependencies
# ---------------------------------------------------------------------------


def test_compare_dependencies_finds_discrepancy() -> None:
    builder = _make_builder({})
    db_a = {"database": {"111": {"dependencies": ["222"]}}}
    db_b = {"database": {"111": {"dependencies": ["222", "333"]}}}
    deps_a = {"111": {"222"}}
    deps_b = {"111": {"222", "333"}}

    discrepancies, details = builder._compare_dependencies(db_a, db_b, deps_a, deps_b)

    assert discrepancies == ["111"]
    assert details["111"] == ({"222"}, {"222", "333"})


def test_compare_dependencies_no_discrepancy_when_equal() -> None:
    builder = _make_builder({})
    db_a = {"database": {"111": {"dependencies": ["222"]}}}
    db_b = {"database": {"111": {"dependencies": ["222"]}}}
    deps_a = {"111": {"222"}}
    deps_b = {"111": {"222"}}

    discrepancies, details = builder._compare_dependencies(db_a, db_b, deps_a, deps_b)

    assert discrepancies == []
    assert details == {}


def test_compare_dependencies_skips_unpublished() -> None:
    builder = _make_builder({})
    db_a = {"database": {"111": {"unpublished": True, "dependencies": ["222"]}}}
    db_b = {"database": {"111": {"dependencies": ["999"]}}}
    deps_a = {"111": {"222"}}
    deps_b = {"111": {"999"}}

    discrepancies, _ = builder._compare_dependencies(db_a, db_b, deps_a, deps_b)

    assert discrepancies == []


# ---------------------------------------------------------------------------
# _build_comparison_report
# ---------------------------------------------------------------------------


def test_build_comparison_report() -> None:
    builder = _make_builder({})
    db_a = {"database": {"111": {"name": "Mod One"}}}
    db_b = {"database": {"111": {"name": "Mod One"}}}
    details = {"111": ({"222"}, {"222", "333"})}

    report = builder._build_comparison_report(db_a, db_b, details, 1, 2)

    assert "Steam DB comparison report" in report
    assert "Total # of discrepancies" in report
    assert "DISCREPANCY FOUND for 111" in report
    assert "Mod name: Mod One" in report
