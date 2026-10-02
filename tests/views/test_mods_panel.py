from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.models.metadata.metadata_structure import (
    AboutXmlMod,
    CaseInsensitiveSet,
    CaseInsensitiveStr,
)
from app.models.settings import Settings
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.custom_list_widget_item_metadata import CustomListWidgetItemMetadata
from app.views.mod_list_widget import ModListWidget
from app.views.tag_edit_dialog import TagEditDialog


def _make_active_mod_list(
    qtbot: Any,
    mods: dict[str, AboutXmlMod],
    paths: list[str],
) -> ModListWidget:
    """
    Build a bare Active mod list populated with the given mods.

    :param qtbot: Pytest-Qt bot for widget testing.
    :param mods: Metadata keyed by mod path.
    :param paths: Mod paths in the order they should appear.
    :return: A ready-to-query mod list widget.
    """
    settings = MagicMock(spec=Settings)
    settings.external_use_this_instead_metadata_source = "None"
    settings.show_save_comparison_indicators = False
    settings.mod_list_updated_indicator = False
    settings.mod_list_startup_impact = False
    settings.use_alternative_package_ids_as_satisfying_dependencies = False

    metadata_controller = MagicMock()
    metadata_controller.mods_metadata = mods
    metadata_controller.settings = settings
    metadata_controller.is_version_mismatch.return_value = False
    metadata_controller.steamdb_packageid_to_name = {}

    widget = ModListWidget.__new__(ModListWidget)
    QListWidget.__init__(widget)
    qtbot.addWidget(widget)
    widget.list_type = "Active"
    widget.settings = settings
    widget.metadata_controller = metadata_controller
    widget.paths = paths
    widget.ignore_warning_list = []

    for path in paths:
        item_data = object.__new__(CustomListWidgetItemMetadata)
        item_data.path = path
        item_data.warning_toggled = False
        item_data.alternative = None
        item_data.errors = ""
        item_data.warnings = ""
        item_data.errors_warnings = ""
        item_data.updated_timestamp = 0

        item = CustomListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, item_data, avoid_emit=True)
        widget.addItem(item)

    return widget


class TestTagEditDialog:
    """Test suite for the TagEditDialog dialog."""

    @pytest.fixture
    def dialog(self, qtbot: Any) -> TagEditDialog:
        """
        Create a TagEditDialog instance for testing.

        :param qtbot: Pytest-Qt bot for widget testing.
        :return: A mock TagEditDialog instance for testing.
        """
        with patch(
            "app.views.tag_edit_dialog.auxdb_get_all_tags",
            return_value={"a", "aa", "b", "bb", "c", "cc"},
        ):
            dialog = TagEditDialog(
                title="Test Dialog",
                settings=MagicMock(spec=Settings),
                existing_selected_tags={"a", "aa", "b", "bb"},
            )
            qtbot.addWidget(dialog)
            assert dialog.tags_list.count() == 6
            assert len(dialog.tags_list.selectedItems()) == 4
            return dialog

    @staticmethod
    def _get_tags(widget: QListWidget) -> list[QListWidgetItem]:
        """
        Get tags from the widget as a list to iterate over.

        :return: A list of tag items.
        """
        return [widget.item(i) for i in range(widget.count())]

    def test_insert_new_tag(self, dialog: TagEditDialog) -> None:
        """
        Test inserting a new tag.
        """
        dialog.tags_text_input.setText("dd,")

        # jscpd:ignore-start
        found_items = dialog.tags_list.findItems("dd", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "dd"
        assert item.isSelected() is True
        assert item.isHidden() is False

        found_items = dialog.tags_list.findItems("a", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "a"
        assert item.isSelected() is True
        assert item.isHidden() is False

        found_items = dialog.tags_list.findItems("c", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "c"
        assert item.isSelected() is False
        assert item.isHidden() is False
        # jscpd:ignore-end

    def test_update_existing_tag_already_selected(self, dialog: TagEditDialog) -> None:
        """Test updating an existing tag that is already selected."""
        dialog.tags_text_input.setText("a,")

        # jscpd:ignore-start
        found_items = dialog.tags_list.findItems("a", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "a"
        assert item.isSelected() is False
        assert item.isHidden() is False

        found_items = dialog.tags_list.findItems("aa", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "aa"
        assert item.isSelected() is True
        assert item.isHidden() is False

        found_items = dialog.tags_list.findItems("c", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "c"
        assert item.isSelected() is False
        assert item.isHidden() is False
        # jscpd:ignore-end

    def test_update_existing_tag_not_already_selected(
        self, dialog: TagEditDialog
    ) -> None:
        """Test updating an existing tag that is not already selected."""
        dialog.tags_text_input.setText("cc,")

        # jscpd:ignore-start
        found_items = dialog.tags_list.findItems("cc", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "cc"
        assert item.isSelected() is True
        assert item.isHidden() is False

        found_items = dialog.tags_list.findItems("a", Qt.MatchFlag.MatchExactly)
        assert len(found_items) == 1
        item = found_items[0]
        assert item.text() == "a"
        assert item.isSelected() is True
        assert item.isHidden() is False
        # jscpd:ignore-end

    def test_select_all_and_none(self, dialog: TagEditDialog) -> None:
        """
        Test selecting all tags and selecting none of the tags.
        """
        dialog.select_all()
        assert all(tag.isSelected() is True for tag in self._get_tags(dialog.tags_list))

        dialog.select_none()
        assert all(
            tag.isSelected() is False for tag in self._get_tags(dialog.tags_list)
        )

    def test_filter_tags(self, dialog: TagEditDialog) -> None:
        """Test filtering tags based on user input."""
        dialog.tags_text_input.setText("a")
        assert all(
            tag.isHidden() is ("a" not in tag.text())
            for tag in self._get_tags(dialog.tags_list)
        )

        dialog.tags_text_input.setText("aa")
        assert all(
            tag.isHidden() is ("aa" not in tag.text())
            for tag in self._get_tags(dialog.tags_list)
        )

        dialog.tags_text_input.clear()
        assert all(tag.isHidden() is False for tag in self._get_tags(dialog.tags_list))

        dialog.tags_text_input.setText("d")
        assert all(tag.isHidden() is True for tag in self._get_tags(dialog.tags_list))


@pytest.mark.parametrize(
    ("rule_name", "paths", "expected_header", "unexpected_header"),
    [
        (
            "load_before",
            ["/mods/b", "/mods/a"],
            "Should be Loaded Before:",
            "Should be Loaded After:",
        ),
        (
            "load_after",
            ["/mods/a", "/mods/b"],
            "Should be Loaded After:",
            "Should be Loaded Before:",
        ),
    ],
)
def test_load_order_warning_header_matches_rule_direction(
    qtbot: Any,
    rule_name: str,
    paths: list[str],
    expected_header: str,
    unexpected_header: str,
) -> None:
    """
    The tooltip header must name the direction of the violated rule.

    :param qtbot: Pytest-Qt bot for widget testing.
    :param rule_name: The violated rule, either load_before or load_after.
    :param paths: Mod paths in the order they should appear.
    :param expected_header: The header that should be displayed.
    :param unexpected_header: The header that must not be displayed.
    """
    mod_a = AboutXmlMod(
        name="Alpha",
        _mod_path=Path("/mods/a"),
        package_id=CaseInsensitiveStr("mod.a"),
    )
    mod_b = AboutXmlMod(
        name="Beta",
        _mod_path=Path("/mods/b"),
        package_id=CaseInsensitiveStr("mod.b"),
    )
    setattr(mod_a.about_rules, rule_name, CaseInsensitiveSet(["mod.b"]))
    widget = _make_active_mod_list(
        qtbot,
        {"/mods/a": mod_a, "/mods/b": mod_b},
        paths,
    )

    widget.recalculate_internal_errors_warnings()

    item = widget.item(paths.index("/mods/a"))
    assert item is not None
    warning = item.data(Qt.ItemDataRole.UserRole).warnings
    assert expected_header in warning
    assert "* Beta" in warning
    assert unexpected_header not in warning
