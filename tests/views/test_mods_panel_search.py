from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from app.models.metadata.metadata_structure import (
    AboutXmlMod,
    CaseInsensitiveStr,
    ListedMod,
)
from app.models.settings import Settings
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.custom_list_widget_item_metadata import CustomListWidgetItemMetadata
from app.views.mods_panel import ModsPanel


def _add_mod_item(panel: ModsPanel, list_type: str, path: str) -> CustomListWidgetItem:
    """
    Add a bare mod row to the requested list so filtering can be exercised.

    :param panel: The mods panel under test.
    :param list_type: Either "Active" or "Inactive".
    :param path: Metadata key identifying the mod.
    :return: The item that was added to the list.
    """
    mod_list = (
        panel.active_mods_list if list_type == "Active" else panel.inactive_mods_list
    )
    data = object.__new__(CustomListWidgetItemMetadata)
    data.path = path
    data.filtered = False
    data.invalid = False
    data.mod_tags = []
    item = CustomListWidgetItem()
    item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
    mod_list.addItem(item)
    return item


@pytest.mark.parametrize("list_type", ["Active", "Inactive"])
def test_author_search_filters_mods_case_insensitively(
    qtbot: Any, monkeypatch: pytest.MonkeyPatch, list_type: str
) -> None:
    """
    An author query keeps only mods whose authors match, ignoring case.

    :param qtbot: Pytest-Qt bot for widget testing.
    :param monkeypatch: Pytest fixture for patching the list visibility refresh.
    :param list_type: Either "Active" or "Inactive".
    """
    settings = Settings()
    matching_path = "/mods/matching"
    other_path = "/mods/other"
    matching_mod = AboutXmlMod(
        name="Matching Mod",
        package_id=CaseInsensitiveStr("example.matching"),
        authors=["Jane Doe", "Second Author"],
    )
    other_mod = AboutXmlMod(
        name="Other Mod",
        package_id=CaseInsensitiveStr("example.other"),
        authors=["Someone Else"],
    )
    metadata = MagicMock()
    metadata.mods_metadata = {
        matching_path: matching_mod,
        other_path: other_mod,
    }
    metadata.get_mod.side_effect = metadata.mods_metadata.get

    panel = ModsPanel(settings, metadata)
    qtbot.addWidget(panel)
    mod_list = (
        panel.active_mods_list if list_type == "Active" else panel.inactive_mods_list
    )
    search_filter = (
        panel.active_mods_search_filter
        if list_type == "Active"
        else panel.inactive_mods_search_filter
    )
    matching_item = _add_mod_item(panel, list_type, matching_path)
    other_item = _add_mod_item(panel, list_type, other_path)
    mod_list.paths = [matching_path, other_path]
    monkeypatch.setattr(mod_list, "check_widgets_visible", MagicMock())
    search_filter.setCurrentText(panel.tr("Author(s)"))

    panel.signal_search_and_filters(list_type, "jAnE")

    assert not matching_item.isHidden()
    assert other_item.isHidden()


@pytest.mark.parametrize(
    "mod",
    [
        AboutXmlMod(
            name="No Author Mod",
            package_id=CaseInsensitiveStr("example.noauthor"),
        ),
        ListedMod(name="Invalid Mod"),
    ],
)
def test_author_search_filters_mods_without_authors(
    qtbot: Any, monkeypatch: pytest.MonkeyPatch, mod: AboutXmlMod | ListedMod
) -> None:
    """
    An author query hides mods that carry no author metadata at all.

    :param qtbot: Pytest-Qt bot for widget testing.
    :param monkeypatch: Pytest fixture for patching the list visibility refresh.
    :param mod: A mod lacking usable author metadata.
    """
    settings = Settings()
    path = "/mods/no-author"
    metadata = MagicMock()
    metadata.mods_metadata = {path: mod}
    metadata.get_mod.side_effect = metadata.mods_metadata.get

    panel = ModsPanel(settings, metadata)
    qtbot.addWidget(panel)
    item = _add_mod_item(panel, "Active", path)
    panel.active_mods_list.paths = [path]
    monkeypatch.setattr(panel.active_mods_list, "check_widgets_visible", MagicMock())
    panel.active_mods_search_filter.setCurrentText(panel.tr("Author(s)"))

    panel.signal_search_and_filters("Active", "author")

    assert item.isHidden()
