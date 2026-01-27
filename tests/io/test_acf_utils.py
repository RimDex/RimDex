from pathlib import Path

from app.core.constants import RIMWORLD_STEAM_APP_ID
from app.io.acf_utils import (
    _extract_manifest_ids_and_remove_pfid,
    _merge_workshop_items_from_sources,
    get_workshop_items_from_acf,
    is_rimworld_workshop_folder,
    load_acf_from_path,
    parse_timeupdated,
    validate_acf_file_exists,
)


def test_parse_timeupdated_none() -> None:
    assert parse_timeupdated(None) is None


def test_parse_timeupdated_valid_string() -> None:
    assert parse_timeupdated("1640995200") == 1640995200


def test_parse_timeupdated_valid_int() -> None:
    assert parse_timeupdated(1640995200) == 1640995200


def test_parse_timeupdated_invalid_string() -> None:
    assert parse_timeupdated("invalid") is None


def test_parse_timeupdated_non_string_invalid() -> None:
    assert parse_timeupdated(object()) is None


def test_get_workshop_items_from_acf_present() -> None:
    acf = {"AppWorkshop": {"WorkshopItemsInstalled": {"123": {"timeupdated": "1"}}}}
    assert get_workshop_items_from_acf(acf) == {"123": {"timeupdated": "1"}}


def test_get_workshop_items_from_acf_missing() -> None:
    assert get_workshop_items_from_acf({}) == {}
    assert get_workshop_items_from_acf({"AppWorkshop": {}}) == {}


def test_is_rimworld_workshop_folder_true() -> None:
    assert (
        is_rimworld_workshop_folder(
            f"steamapps/workshop/content/{RIMWORLD_STEAM_APP_ID}"
        )
        is True
    )


def test_is_rimworld_workshop_folder_false() -> None:
    assert is_rimworld_workshop_folder("steamapps/workshop/content/123456") is False


def test_load_acf_from_path_missing_returns_empty(tmp_path: Path) -> None:
    assert load_acf_from_path(tmp_path / "does_not_exist.acf") == {}


def test_validate_acf_file_exists_true(tmp_path: Path) -> None:
    # The ACF lives at <location>.parent.parent/appworkshop_294100.acf
    # (i.e. steamapps/workshop/appworkshop_294100.acf for a content/294100 location).
    content = tmp_path / "steamapps" / "workshop" / "content" / RIMWORLD_STEAM_APP_ID
    content.mkdir(parents=True)
    (tmp_path / "steamapps" / "workshop" / "appworkshop_294100.acf").write_text("x")
    assert validate_acf_file_exists(str(content)) is True


def test_validate_acf_file_exists_missing(tmp_path: Path) -> None:
    content = tmp_path / "steamapps" / "workshop" / "content" / RIMWORLD_STEAM_APP_ID
    content.mkdir(parents=True)
    assert validate_acf_file_exists(str(content)) is False


def test_validate_acf_file_exists_empty_location() -> None:
    assert validate_acf_file_exists("") is False
    assert validate_acf_file_exists("   ") is False


def test_extract_manifest_ids_and_remove_pfid() -> None:
    section = {"123": {"manifest": "abc"}, "456": {}}
    manifests = _extract_manifest_ids_and_remove_pfid(section, "123")
    assert manifests == {"abc"}
    assert "123" not in section
    assert "456" in section


def test_extract_manifest_ids_none_section() -> None:
    assert _extract_manifest_ids_and_remove_pfid(None, "123") == set()


def test_merge_workshop_items_sources_dedup_and_precedence() -> None:
    steamcmd = {"1": {"timeupdated": "100"}, "2": {"timeupdated": "bad"}}
    steam = {"2": {"timeupdated": "200"}, "3": {"timeupdated": "300"}}
    entries = _merge_workshop_items_from_sources(steamcmd, steam, "SteamCMD", "Steam")
    # pfid 1 only in steamcmd, pfid 2 deduped to SteamCMD source, pfid 3 from Steam.
    assert entries == [
        ("1", "SteamCMD", 100),
        ("2", "SteamCMD", None),
        ("3", "Steam", 300),
    ]


def test_merge_workshop_items_skips_non_dict() -> None:
    steamcmd = {"1": "not-a-dict"}
    entries = _merge_workshop_items_from_sources(steamcmd, {}, "SteamCMD", "Steam")
    assert entries == []
