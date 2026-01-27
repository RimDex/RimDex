from pathlib import Path

from app.services.path_autodetect_service import PathAutodetectService


def test_find_steam_root_prefers_steamapps(tmp_path: Path) -> None:
    (tmp_path / "A" / "steamapps").mkdir(parents=True)
    (tmp_path / "B").mkdir()
    svc = PathAutodetectService()
    assert svc._find_steam_root([tmp_path / "A", tmp_path / "B"]) == tmp_path / "A"


def test_find_steam_root_accepts_library_vdf(tmp_path: Path) -> None:
    vdf = tmp_path / "C" / "config" / "libraryfolders.vdf"
    vdf.parent.mkdir(parents=True)
    vdf.touch()
    svc = PathAutodetectService()
    assert svc._find_steam_root([tmp_path / "C"]) == tmp_path / "C"


def test_find_steam_root_none_when_no_match(tmp_path: Path) -> None:
    svc = PathAutodetectService()
    assert svc._find_steam_root([tmp_path / "missing"]) is None


def test_find_mac_app_bundle_finds_app(tmp_path: Path) -> None:
    (tmp_path / "RimWorldMac.app").mkdir()
    svc = PathAutodetectService()
    assert svc._find_mac_app_bundle(tmp_path) == tmp_path / "RimWorldMac.app"


def test_find_mac_app_bundle_fallback(tmp_path: Path) -> None:
    svc = PathAutodetectService()
    assert svc._find_mac_app_bundle(tmp_path) == tmp_path / "RimWorldMac.app"
