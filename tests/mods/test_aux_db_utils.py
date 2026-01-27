from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtGui import QColor

from app.controllers.metadata_db_controller import AuxMetadataController
from app.mods.aux_db_utils import (
    auxdb_add_mod_tags,
    auxdb_cleanup_unused_tags,
    auxdb_get_all_tags,
    auxdb_get_aux_db_entry,
    auxdb_get_mod_color,
    auxdb_get_mod_tags,
    auxdb_get_mod_user_notes,
    auxdb_get_mod_warning_toggled,
    auxdb_remove_mod_tags,
    auxdb_update_mod_color,
)


@pytest.fixture
def aux_controller(tmp_path: Path) -> AuxMetadataController:
    return AuxMetadataController(tmp_path / "aux.db")


@pytest.fixture
def settings() -> MagicMock:
    return MagicMock()


def _seed(
    aux_controller: AuxMetadataController,
    path: str,
    color_hex: str | None = None,
    user_notes: str = "",
    ignore_warnings: bool = False,
) -> None:
    with aux_controller.Session() as session:
        entry = aux_controller.get_or_create(session, path)
        if color_hex is not None:
            entry.color_hex = color_hex
        entry.user_notes = user_notes
        entry.ignore_warnings = ignore_warnings
        session.commit()


def test_get_aux_db_entry_none(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    with aux_controller.Session() as session:
        assert auxdb_get_aux_db_entry(settings, "nope", aux_controller, session) is None


def test_get_aux_db_entry(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    _seed(aux_controller, "mod/a", color_hex="#ff0000")
    with aux_controller.Session() as session:
        entry = auxdb_get_aux_db_entry(settings, "mod/a", aux_controller, session)
    assert entry is not None
    assert entry.color_hex == "#ff0000"


def test_mod_color(aux_controller: AuxMetadataController, settings: MagicMock) -> None:

    _seed(aux_controller, "mod/a", color_hex="#00ff00")
    with aux_controller.Session() as session:
        color = auxdb_get_mod_color(settings, "mod/a", aux_controller, session)
    assert color is not None
    assert color.name() == "#00ff00"


def test_mod_color_none(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    with aux_controller.Session() as session:
        assert auxdb_get_mod_color(settings, "mod/x", aux_controller, session) is None


def test_mod_user_notes(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    _seed(aux_controller, "mod/a", user_notes="hello")
    with aux_controller.Session() as session:
        assert (
            auxdb_get_mod_user_notes(settings, "mod/a", aux_controller, session)
            == "hello"
        )


def test_mod_warning_toggled(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    _seed(aux_controller, "mod/a", ignore_warnings=True)
    with aux_controller.Session() as session:
        assert (
            auxdb_get_mod_warning_toggled(settings, "mod/a", aux_controller, session)
            is True
        )


def test_update_mod_color(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    _seed(aux_controller, "mod/a")
    with aux_controller.Session() as session:
        auxdb_update_mod_color(
            settings, "mod/a", QColor("#123456"), aux_controller, session
        )
        color = auxdb_get_mod_color(settings, "mod/a", aux_controller, session)
    assert color is not None
    assert color.name() == "#123456"


def test_update_mod_color_clear(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    _seed(aux_controller, "mod/a", color_hex="#ff0000")
    with aux_controller.Session() as session:
        auxdb_update_mod_color(settings, "mod/a", None, aux_controller, session)
        assert auxdb_get_mod_color(settings, "mod/a", aux_controller, session) is None


def test_tags_add_and_get_normalized(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    with aux_controller.Session() as session:
        auxdb_add_mod_tags(
            settings, "mod/a", ["Alpha", " beta "], aux_controller, session
        )
        tags = auxdb_get_mod_tags(settings, "mod/a", aux_controller, session)
    assert tags == ["alpha", "beta"]


def test_get_all_tags(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    with aux_controller.Session() as session:
        auxdb_add_mod_tags(settings, "mod/a", ["X"], aux_controller, session)
        auxdb_add_mod_tags(settings, "mod/b", ["Y"], aux_controller, session)
        all_tags = auxdb_get_all_tags(settings, aux_controller, session)
    assert set(all_tags) == {"x", "y"}


def test_cleanup_unused_tags(
    aux_controller: AuxMetadataController, settings: MagicMock
) -> None:

    with aux_controller.Session() as session:
        auxdb_add_mod_tags(settings, "mod/a", ["keep", "drop"], aux_controller, session)
        auxdb_add_mod_tags(settings, "mod/b", ["keep"], aux_controller, session)
    with aux_controller.Session() as session:
        auxdb_remove_mod_tags(settings, "mod/a", aux_controller, session)
        auxdb_cleanup_unused_tags(settings, aux_controller, session)
        all_tags = auxdb_get_all_tags(settings, aux_controller, session)
    assert all_tags == ["keep"]
