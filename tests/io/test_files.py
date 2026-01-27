import os
import time
from pathlib import Path

from app.io.files import cleanup_old_backups, subfolder_contains_candidate_path


def _make_backup(d: Path, name: str, age_seconds: int) -> Path:
    p = d / name
    p.write_text("backup")
    new_time = time.time() - age_seconds
    os.utime(p, (new_time, new_time))
    return p


def test_subfolder_contains_candidate_path_match(tmp_path: Path) -> None:
    sub = tmp_path / "Game"
    (sub / "Mods").mkdir(parents=True)
    (sub / "Mods" / "asset.dll").write_text("x")
    assert subfolder_contains_candidate_path(sub, "Mods", "*.dll") is True


def test_subfolder_contains_candidate_path_no_match(tmp_path: Path) -> None:
    sub = tmp_path / "Game"
    (sub / "Mods").mkdir(parents=True)
    (sub / "Mods" / "asset.txt").write_text("x")
    assert subfolder_contains_candidate_path(sub, "Mods", "*.dll") is False


def test_subfolder_contains_candidate_path_none_subfolder() -> None:
    assert subfolder_contains_candidate_path(None, "Mods", "*.dll") is False


def test_subfolder_contains_candidate_path_checks_immediate_subdirs(
    tmp_path: Path,
) -> None:
    sub = tmp_path / "Game"
    sub.mkdir()
    nested = sub / "Workshop" / "1234567890"
    nested.mkdir(parents=True)
    (nested / "mod.dll").write_text("x")
    # candidate lives in an immediate subdir of `sub`, not directly under `sub`.
    assert subfolder_contains_candidate_path(sub, "1234567890", "*.dll") is True


def test_cleanup_old_backups_keeps_most_recent(tmp_path: Path) -> None:
    d = tmp_path / "backups"
    d.mkdir()
    for i in range(5):
        _make_backup(d, f"Saves_{i}.zip", age_seconds=100 - i)
    cleanup_old_backups(d, keep=2)
    remaining = sorted(p.name for p in d.glob("Saves_*.zip"))
    assert remaining == ["Saves_3.zip", "Saves_4.zip"]


def test_cleanup_old_backups_keep_zero_deletes_all(tmp_path: Path) -> None:
    d = tmp_path / "backups"
    d.mkdir()
    for i in range(3):
        _make_backup(d, f"Saves_{i}.zip", age_seconds=10 - i)
    cleanup_old_backups(d, keep=0)
    assert list(d.glob("Saves_*.zip")) == []


def test_cleanup_old_backups_keep_minus_one_keeps_all(tmp_path: Path) -> None:
    d = tmp_path / "backups"
    d.mkdir()
    for i in range(3):
        _make_backup(d, f"Saves_{i}.zip", age_seconds=10 - i)
    cleanup_old_backups(d, keep=-1)
    assert len(list(d.glob("Saves_*.zip"))) == 3
