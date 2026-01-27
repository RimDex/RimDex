from pathlib import Path

import pytest

from app.models.instance import Instance
from app.services.mod_path_service import get_mod_paths, resolve_data_source


@pytest.fixture
def instance() -> Instance:
    return Instance(
        name="test",
        game_folder=str(Path("C:/game")),
        local_folder=str(Path("C:/game/Mods")),
        workshop_folder=str(Path("C:/workshop")),
    )


def test_get_mod_paths(instance: Instance) -> None:
    paths = get_mod_paths(instance)
    assert paths == [
        str(Path("C:/game") / "Data"),
        str(Path("C:/game/Mods")),
        str(Path("C:/workshop")),
    ]


def test_resolve_data_source_expansion(instance: Instance) -> None:
    path = str(Path("C:/game") / "Data" / "Core")
    assert resolve_data_source(instance, path) == "expansion"


def test_resolve_data_source_local(instance: Instance) -> None:
    path = str(Path("C:/game/Mods") / "SomeMod")
    assert resolve_data_source(instance, path) == "local"


def test_resolve_data_source_workshop(instance: Instance) -> None:
    path = str(Path("C:/workshop") / "12345")
    assert resolve_data_source(instance, path) == "workshop"


def test_resolve_data_source_unknown(instance: Instance) -> None:
    assert resolve_data_source(instance, str(Path("C:/elsewhere/file"))) is None
