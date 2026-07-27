from pathlib import Path

from app.services import mod_list_parser as mlp
from app.services.dependency_resolver import parse_workshop_id_from_url

MODS_CONFIG_XML = """<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
  <version>1.5</version>
  <activeMods>
    <li>Core</li>
    <li>Vanilla.Expanded</li>
  </activeMods>
  <knownExpansions>
    <li>Ludeon.RimWorld</li>
  </knownExpansions>
</ModsConfigData>
"""

RIMDEX_JSON = """{
  "version": "1.5",
  "activeMods": ["Core", "Vanilla.Expanded"],
  "knownExpansions": ["Ludeon.RimWorld"]
}"""


def test_parse_xml_mods_config(tmp_path: Path) -> None:
    f = tmp_path / "ModsConfig.xml"
    f.write_text(MODS_CONFIG_XML, encoding="utf-8")
    parsed = mlp.parse_mod_list_file(f)
    assert parsed.package_ids == ["Core", "Vanilla.Expanded"]
    assert parsed.game_version == "1.5"
    assert parsed.known_expansions == ["Ludeon.RimWorld"]
    assert parsed.source_format == "mods_config_xml"


def test_parse_rimdex_json(tmp_path: Path) -> None:
    f = tmp_path / "list.rml"
    f.write_text(RIMDEX_JSON, encoding="utf-8")
    parsed = mlp.parse_mod_list_file(f)
    assert parsed.package_ids == ["Core", "Vanilla.Expanded"]
    assert parsed.game_version == "1.5"
    assert parsed.known_expansions == ["Ludeon.RimWorld"]
    assert parsed.source_format == "rimdex_json"


def test_parse_missing_file_raises(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(mlp.ModListFormatError):
        mlp.parse_mod_list_file(tmp_path / "nope.xml")


def test_parse_unknown_format_raises(tmp_path: Path) -> None:
    import pytest

    f = tmp_path / "weird.txt"
    f.write_text("just some text", encoding="utf-8")
    with pytest.raises(mlp.ModListFormatError):
        mlp.parse_mod_list_file(f)


def test_parsed_to_mods_config_dict_roundtrip(tmp_path: Path) -> None:
    f = tmp_path / "ModsConfig.xml"
    f.write_text(MODS_CONFIG_XML, encoding="utf-8")
    parsed = mlp.parse_mod_list_file(f)
    d = mlp.parsed_to_mods_config_dict(parsed)
    assert d["ModsConfigData"]["version"] == "1.5"
    assert d["ModsConfigData"]["activeMods"]["li"] == ["Core", "Vanilla.Expanded"]


def test_parse_workshop_id_from_url_variants() -> None:
    assert (
        parse_workshop_id_from_url(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=12345"
        )
        == "12345"
    )
    assert (
        parse_workshop_id_from_url(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=999&foo=bar"
        )
        == "999"
    )
    assert (
        parse_workshop_id_from_url(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=42/extra"
        )
        == "42"
    )
    assert parse_workshop_id_from_url("https://example.com/other") is None
