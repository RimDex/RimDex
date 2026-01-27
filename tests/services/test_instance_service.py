"""Tests for ``app.services.instance_service`` (leaf layer).

Focuses on the pure, side-effect-free filesystem helpers exposed as static
methods on ``InstanceService`` (``copy_game_folder``, ``copy_config_folder``,
``copy_local_folder``, ``copy_workshop_mods_to_local``,
``clone_essential_paths``). These run headless with no Qt/EventBus.
"""

from pathlib import Path

from app.services.instance_service import InstanceService


def _make_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_copy_game_folder_creates_copy(tmp_path: Path) -> None:
    src = tmp_path / "src_game"
    _make_tree(src, {"RimWorld.exe": "binary", "Data/core": "data"})
    dst = tmp_path / "dst_game"

    InstanceService.copy_game_folder(str(src), str(dst))

    assert (dst / "RimWorld.exe").read_text(encoding="utf-8") == "binary"
    assert (dst / "Data" / "core").read_text(encoding="utf-8") == "data"


def test_copy_game_folder_replaces_existing(tmp_path: Path) -> None:
    src = tmp_path / "src_game"
    _make_tree(src, {"new.txt": "fresh"})
    dst = tmp_path / "dst_game"
    _make_tree(dst, {"old.txt": "stale"})

    InstanceService.copy_game_folder(str(src), str(dst))

    assert (dst / "new.txt").exists()
    assert not (dst / "old.txt").exists()


def test_copy_config_folder_creates_copy(tmp_path: Path) -> None:
    src = tmp_path / "src_cfg"
    _make_tree(src, {"ModsConfig.xml": "<config/>"})
    dst = tmp_path / "dst_cfg"

    InstanceService.copy_config_folder(str(src), str(dst))

    assert (dst / "ModsConfig.xml").read_text(encoding="utf-8") == "<config/>"


def test_copy_local_folder_creates_copy(tmp_path: Path) -> None:
    src = tmp_path / "src_local"
    _make_tree(src, {"SomeMod/About/About.xml": "about"})
    dst = tmp_path / "dst_local"

    InstanceService.copy_local_folder(str(src), str(dst))

    assert (dst / "SomeMod" / "About" / "About.xml").read_text(
        encoding="utf-8"
    ) == "about"


def test_copy_workshop_mods_to_local_copies_subdirs(tmp_path: Path) -> None:
    src = tmp_path / "workshop"
    (src / "111").mkdir(parents=True)
    (src / "111" / "mod").write_text("m", encoding="utf-8")
    (src / "222").mkdir(parents=True)
    dst = tmp_path / "dst_local"

    InstanceService.copy_workshop_mods_to_local(str(src), str(dst))

    assert (dst / "111" / "mod").read_text(encoding="utf-8") == "m"
    assert (dst / "222").is_dir()


def test_copy_workshop_mods_to_local_creates_target(tmp_path: Path) -> None:
    src = tmp_path / "workshop"
    (src / "111").mkdir(parents=True)
    dst = tmp_path / "dst_local"

    InstanceService.copy_workshop_mods_to_local(str(src), str(dst))

    assert dst.is_dir()


def test_clone_essential_paths_only_copies_existing(tmp_path: Path) -> None:
    src_game = tmp_path / "src_game"
    _make_tree(src_game, {"a": "1"})
    dst_game = tmp_path / "dst_game"
    src_cfg = tmp_path / "src_cfg"
    _make_tree(src_cfg, {"b": "2"})
    # config target exists but source config missing -> should NOT error
    dst_cfg = tmp_path / "dst_cfg"

    InstanceService.clone_essential_paths(
        str(src_game),
        str(dst_game),
        str(src_cfg),
        str(dst_cfg),
    )

    assert (dst_game / "a").read_text(encoding="utf-8") == "1"
    assert (dst_cfg / "b").read_text(encoding="utf-8") == "2"


def test_copy_helpers_skip_when_source_missing(tmp_path: Path) -> None:
    # Missing source must not raise and must not create the target.
    dst = tmp_path / "dst"
    InstanceService.copy_game_folder(str(tmp_path / "nope"), str(dst))
    assert not dst.exists()
