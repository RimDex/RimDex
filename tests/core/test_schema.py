from app.core.schema import (
    generate_rimworld_mods_list,
    validate_rimworld_mods_list,
)


def test_generate_mods_list() -> None:
    data = generate_rimworld_mods_list("1.5", ["mod.a", "mod.b"])
    assert data["ModsConfigData"]["version"] == "1.5"
    assert data["ModsConfigData"]["activeMods"]["li"] == ["mod.a", "mod.b"]


def test_generate_mods_list_excludes_base_game_from_dlc() -> None:
    data = generate_rimworld_mods_list("1.5", [])
    known = data["ModsConfigData"]["knownExpansions"]["li"]
    assert isinstance(known, list)
    assert "ludeon.rimworld" not in known


def test_validate_mods_config_list() -> None:
    assert validate_rimworld_mods_list(
        {"ModsConfigData": {"activeMods": {"li": ["a", "b"]}}}
    ) == ["a", "b"]


def test_validate_mods_config_single_str() -> None:
    assert validate_rimworld_mods_list(
        {"ModsConfigData": {"activeMods": {"li": "solo"}}}
    ) == ["solo"]


def test_validate_rws_savegame() -> None:
    assert validate_rimworld_mods_list(
        {"savegame": {"meta": {"modIds": {"li": ["x"]}}}}
    ) == ["x"]


def test_validate_rml_modlist() -> None:
    assert validate_rimworld_mods_list(
        {"savedModList": {"meta": {"modIds": {"li": ["y"]}}}}
    ) == ["y"]
