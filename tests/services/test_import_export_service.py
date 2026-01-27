"""Tests for ``app.services.import_export_service`` (leaf layer).

Covers the pure data-transformation logic of ``ImportExportService``:
``collect_active_mods``, ``build_clipboard_report``, ``build_rentry_report``,
``calculate_rentry_max_mods``, and the file-writing ``export_to_xml`` /
``save_to_mods_config``. Network/UI paths (``fetch_steam_preview_urls``,
``upload_rentry_report``) are exercised with mocked collaborators.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.metadata.metadata_structure import (
    AboutXmlMod,
    CaseInsensitiveStr,
    ModType,
)
from app.services.import_export_service import (
    ImportExportService,
)


def _make_mod(
    name: str,
    package_id: str,
    uuid: str,
    mod_type: ModType = ModType.LOCAL,
    pfid: str = "",
    url: str = "",
) -> AboutXmlMod:
    mod = AboutXmlMod(
        name=name,
        package_id=CaseInsensitiveStr(package_id),
        _uuid=uuid,
        _mod_type=mod_type,
        url=url,
    )
    if pfid:
        mod.published_file_id = pfid
    return mod


@pytest.fixture
def provider() -> MagicMock:
    mods: dict[str, AboutXmlMod] = {}
    mock = MagicMock()
    mock.game_version = "1.5"
    mock.get_mod.side_effect = lambda uuid: mods.get(uuid)
    mock._mods = mods
    return mock


@pytest.fixture
def service(provider: MagicMock) -> ImportExportService:
    settings = MagicMock()
    settings.current_instance = "Default"
    settings.instances = {"Default": MagicMock(config_folder=str(Path("C:/cfg")))}
    return ImportExportService(metadata_controller=provider, settings=settings)


def test_collect_active_mods_basic(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")
    provider._mods["u2"] = _make_mod("Mod B", "c.d", "u2")

    data = service.collect_active_mods(["u1", "u2"])

    assert data.active_mods == ["a.b", "c.d"]
    assert data.packageid_to_uuid == {"a.b": "u1", "c.d": "u2"}


def test_collect_active_mods_skips_dividers_and_unknown(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")

    data = service.collect_active_mods(["__divider__x", "u1", "missing"])

    assert data.active_mods == ["a.b"]


def test_collect_active_mods_skips_duplicate_package_ids(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")
    provider._mods["u2"] = _make_mod("Mod A dup", "a.b", "u2")

    data = service.collect_active_mods(["u1", "u2"])

    assert data.active_mods == ["a.b"]
    assert data.packageid_to_uuid == {"a.b": "u1"}


def test_collect_active_mods_steam_workshop_suffix(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod(
        "Mod A", "a.b", "u1", mod_type=ModType.STEAM_WORKSHOP
    )
    duplicate_mods = {"a.b": ["u1"]}

    data = service.collect_active_mods(["u1"], duplicate_mods=duplicate_mods)

    assert data.active_mods == ["a.b_steam"]


def test_collect_active_mods_records_steam_pfids(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod(
        "Mod A", "a.b", "u1", mod_type=ModType.STEAM_CMD, pfid="12345"
    )

    data = service.collect_active_mods(["u1"])

    assert data.steam_packageid_to_pfid == {"a.b": "12345"}
    assert data.pfids == ["12345"]


def test_build_clipboard_report(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1", url="http://x")
    data = service.collect_active_mods(["u1"])

    report = service.build_clipboard_report(data.active_mods, data.packageid_to_uuid)

    assert "Created with RimDex" in report
    assert "Mod A [a.b]" in report


def test_build_rentry_report_local_mod(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1", url="http://x")
    data = service.collect_active_mods(["u1"])

    report = service.build_rentry_report(
        data.active_mods,
        data.packageid_to_uuid,
        data.steam_packageid_to_pfid,
        data.pfid_to_preview_url,
    )

    assert "Mod list length: `1`" in report
    assert "Mod A" in report


def test_build_rentry_report_steam_mod_with_preview(
    service: ImportExportService, provider: MagicMock
) -> None:
    provider._mods["u1"] = _make_mod(
        "Mod A",
        "a.b",
        "u1",
        mod_type=ModType.STEAM_WORKSHOP,
        pfid="12345",
        url="http://x",
    )
    data = service.collect_active_mods(["u1"])
    data.pfid_to_preview_url["12345"] = "http://preview"

    report = service.build_rentry_report(
        data.active_mods,
        data.packageid_to_uuid,
        data.steam_packageid_to_pfid,
        data.pfid_to_preview_url,
    )

    assert "http://preview" in report
    assert "packageid: a.b" in report


def _max_rentry_mods(
    service: ImportExportService, provider: MagicMock, max_chars: int = 200000
) -> int:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")
    data = service.collect_active_mods(["u1"])
    return service.calculate_rentry_max_mods(
        data.active_mods,
        data.packageid_to_uuid,
        data.steam_packageid_to_pfid,
        data.pfid_to_preview_url,
        max_chars=max_chars,
    )


def test_calculate_rentry_max_mods_all_fit(
    service: ImportExportService, provider: MagicMock
) -> None:
    assert _max_rentry_mods(service, provider) == 1


def test_calculate_rentry_max_mods_zero_when_too_big(
    service: ImportExportService, provider: MagicMock
) -> None:
    assert _max_rentry_mods(service, provider, max_chars=1) == 0


def test_export_to_xml_writes_file(
    service: ImportExportService, provider: MagicMock, tmp_path: Path
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")
    data = service.collect_active_mods(["u1"])
    target = tmp_path / "ModsConfig"

    service.export_to_xml(data.active_mods, str(target))

    assert target.with_suffix(".xml").exists()


def test_save_to_mods_config_writes_file(
    service: ImportExportService, provider: MagicMock, tmp_path: Path
) -> None:
    provider._mods["u1"] = _make_mod("Mod A", "a.b", "u1")
    data = service.collect_active_mods(["u1"])
    service.settings.instances["Default"].config_folder = str(tmp_path)

    path = service.save_to_mods_config(data.active_mods)

    assert Path(path).exists()
    assert Path(path).name == "ModsConfig.xml"


def test_fetch_steam_preview_urls_empty() -> None:
    provider = MagicMock()
    provider.game_version = "1.5"
    service = ImportExportService(metadata_controller=provider, settings=MagicMock())

    assert service.fetch_steam_preview_urls([]) == {}


def test_fetch_steam_preview_urls_maps_pfids() -> None:
    provider = MagicMock()
    provider.game_version = "1.5"
    service = ImportExportService(metadata_controller=provider, settings=MagicMock())

    response = [
        {"publishedfileid": "123", "result": 1, "preview_url": "http://p"},
        {"publishedfileid": "456", "result": 9, "preview_url": ""},
    ]
    with patch(
        "app.services.import_export_service.ISteamRemoteStorage_GetPublishedFileDetails",
        return_value=(response, None, None),
    ):
        result = service.fetch_steam_preview_urls(["123", "456"])

    assert result == {"123": "http://p"}


def test_upload_rentry_report_success() -> None:
    provider = MagicMock()
    provider.game_version = "1.5"
    service = ImportExportService(metadata_controller=provider, settings=MagicMock())

    fake_uploader = MagicMock(upload_success=True, url="https://rentry.co/abc")
    with patch(
        "app.services.import_export_service.RentryUpload", return_value=fake_uploader
    ):
        ok, url = service.upload_rentry_report("report")

    assert ok is True
    assert url == "https://rentry.co/abc"


def test_upload_rentry_report_rejects_non_rentry_host() -> None:
    provider = MagicMock()
    provider.game_version = "1.5"
    service = ImportExportService(metadata_controller=provider, settings=MagicMock())

    fake_uploader = MagicMock(upload_success=True, url="https://evil.example/x")
    with patch(
        "app.services.import_export_service.RentryUpload", return_value=fake_uploader
    ):
        ok, url = service.upload_rentry_report("report")

    assert ok is False
    assert url is None
