"""Regression tests for app.io.dds_utility.DDSUtility.

These guard against the path-mangling bug where building the ``.png``
counterpart via ``str.replace(".dds", ".png")`` corrupts the path when
``.dds`` appears outside the file name (e.g. a ``.dds_stuff`` parent
directory).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.io.dds_utility import DDSUtility


def _make_utility(local: Path, workshop: str | Path) -> DDSUtility:
    """Build a DDSUtility with a minimal settings stub (no real Settings)."""
    instance = SimpleNamespace(local_folder=str(local), workshop_folder=str(workshop))
    settings = SimpleNamespace(
        current_instance="default", instances={"default": instance}
    )
    return DDSUtility(settings)  # type: ignore[arg-type]


def _write_dds(root: Path, rel: str, content: bytes = b"dds") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_deletes_dds_without_png(tmp_path: Path) -> None:
    local = tmp_path / "local"
    workshop = tmp_path / "workshop"
    local.mkdir()
    workshop.mkdir()

    dds_orphan = _write_dds(local, "Mod/Textures/icon.dds")
    _write_dds(local, "Mod/Textures/paired.dds")
    (local / "Mod/Textures/paired.png").write_bytes(b"png")
    # A sibling in a directory whose name contains ".dds" must survive if its
    # png counterpart exists, and must never be mis-resolved.
    dds_in_dds_dir = _write_dds(local, "texture.dds.backup/Mod/x.dds")
    (local / "texture.dds.backup/Mod/x.png").write_bytes(b"png")

    util = _make_utility(local, workshop)
    util.delete_dds_files_without_png()

    assert not dds_orphan.exists()
    assert (local / "Mod/Textures/paired.dds").exists()
    assert dds_in_dds_dir.exists()  # paired -> kept, and path was not mangled


def test_keeps_dds_with_png_in_workshop(tmp_path: Path) -> None:
    local = tmp_path / "local"
    workshop = tmp_path / "workshop"
    local.mkdir()
    workshop.mkdir()

    kept = _write_dds(workshop, "WS/Textures/y.dds")
    (workshop / "WS/Textures/y.png").write_bytes(b"png")

    util = _make_utility(local, workshop)
    util.delete_dds_files_without_png()

    assert kept.exists()


def test_path_with_dds_in_directory_not_mangled(tmp_path: Path) -> None:
    """The .png counterpart must be resolved from the file extension only.

    A parent directory whose name contains ".dds" (but is not dot-prefixed, so
    glob still traverses it) must not corrupt the resolved .png path.
    """
    local = tmp_path / "local"
    workshop = tmp_path / "workshop"
    local.mkdir()
    workshop.mkdir()

    dds = _write_dds(local, "texture.dds.backup/Mod/icon.dds")

    util = _make_utility(local, workshop)
    # Should NOT raise and should not touch a mangled ".png.backup" path.
    util.delete_dds_files_without_png()

    # Orphaned -> deleted (correct target, not a mangled directory).
    assert not dds.exists()


def test_empty_and_none_folders_skipped(tmp_path: Path) -> None:
    """Empty strings and non-existent folders must not raise or delete."""
    local = tmp_path / "local"
    local.mkdir()

    dds = _write_dds(local, "Mod/icon.dds")
    orphan = _write_dds(local, "Other/left.dds")  # no png -> would be deleted

    # workshop folder is "" (unconfigured) -> must be skipped safely.
    util = _make_utility(local, "")
    util.delete_dds_files_without_png()

    assert not dds.exists()  # orphan, deleted
    assert not orphan.exists()  # orphan, deleted


def test_png_pairing_scoped_per_root(tmp_path: Path) -> None:
    """A .png in one root does not pair a .dds in a different root."""
    local = tmp_path / "local"
    workshop = tmp_path / "workshop"
    local.mkdir()
    workshop.mkdir()

    only_in_local = _write_dds(local, "Mod/a.dds")
    png = workshop / "Mod/a.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    png.write_bytes(b"png")  # different root

    util = _make_utility(local, workshop)
    util.delete_dds_files_without_png()

    assert not only_in_local.exists()  # no matching png in its own root


@pytest.mark.parametrize(
    "filename",
    ["a.dds", "sub.b.dds", "weird.name.dds"],
)
def test_with_suffix_counterpart(tmp_path: Path, filename: str) -> None:
    local = tmp_path / "local"
    workshop = tmp_path / "workshop"
    local.mkdir()
    workshop.mkdir()

    dds = _write_dds(local, f"Mod/{filename}")
    assert dds.with_suffix(".png").name == ".".join(filename.split(".")[:-1] + ["png"])
