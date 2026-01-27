"""Colors / tags mixin for ModListWidget.

Holds the mod-color pickers, the warning-toggle + aux-DB sync, and the
tag (user tag) read/refresh/visibility logic.
"""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog

from app.controllers.metadata_db_controller import AuxMetadataController
from app.mods.aux_db_utils import (
    auxdb_get_mod_tags,
    auxdb_update_all_mod_colors,
    auxdb_update_mod_color,
)
from app.views.mixins._shared import ModListWidgetMixinBase
from app.views.mod_list_item_inner import ModListItemInner


class ColorsTagsMixin(ModListWidgetMixinBase):
    """Mod colors, warning toggle, and user-tag handling."""

    def SetUserCustomColors(self, color_dlg: QColorDialog) -> None:  # noqa: N802
        """
        Sets the user's custom colors in the QColorDialog from settings.json.
        """
        settings = self.settings
        colors = settings.color_picker_custom_colors
        if len(colors) != 16:
            return
        for i in range(16):
            color_dlg.setCustomColor(i, colors[i])

    def SaveUserCustomColors(self, color_dlg: QColorDialog) -> None:  # noqa: N802
        """
        Saves the user's custom colors from the QColorDialog to settings.json as list of hex strings.
        """
        settings = self.settings
        colors = []
        for i in range(16):
            color = color_dlg.customColor(i)
            colors.append(color.name())  # Store as hex string
        settings.color_picker_custom_colors = colors
        settings.save()

    def toggle_warning(self, packageid: str, uuid: str) -> None:
        logger.debug(f"Toggled warning icon for: {packageid}")
        current_mod_index = self.paths.index(uuid)
        item = self.item(current_mod_index)
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if packageid not in self.ignore_warning_list:
            self.ignore_warning_list.append(packageid)
            item_data["warning_toggled"] = True
        else:
            self.ignore_warning_list.remove(packageid)
            item_data["warning_toggled"] = False
        # Update Aux DB
        aux_metadata_controller = AuxMetadataController.get_or_create_cached_instance(
            self.settings.aux_db_path
        )
        mod_path = item_data["path"]
        if not mod_path:
            logger.error(
                "Unable to retrieve uuid when saving toggle_warning to Aux DB."
            )
            return
        with aux_metadata_controller.Session() as aux_metadata_session:
            aux_metadata_controller.update(
                aux_metadata_session,
                mod_path,
                ignore_warnings=item_data["warning_toggled"],
            )
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        self.recalculate_warnings_signal.emit()

    def change_mod_color(self, uuid: str, new_color: QColor) -> None:
        current_mod_index = self.paths.index(uuid)
        item = self.item(current_mod_index)
        item_data = item.data(Qt.ItemDataRole.UserRole)
        item_data["mod_color"] = new_color
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        auxdb_update_mod_color(self.settings, uuid, new_color)

    def change_all_mod_colors(self, uuids: list[str], new_color: QColor) -> None:
        self._set_all_mod_colors(uuids, new_color)

    def reset_mod_color(self, uuid: str) -> None:
        current_mod_index = self.paths.index(uuid)
        item = self.item(current_mod_index)
        item_data = item.data(Qt.ItemDataRole.UserRole)
        item_data["mod_color"] = None
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        auxdb_update_mod_color(self.settings, uuid, None)

    def reset_all_mod_colors(self, uuids: list[str]) -> None:
        self._set_all_mod_colors(uuids, None)

    def _set_all_mod_colors(self, uuids: list[str], new_color: QColor | None) -> None:
        uuid_to_color: dict[str, QColor | None] = {}
        for uuid in uuids:
            current_mod_index = self.paths.index(uuid)
            item = self.item(current_mod_index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            item_data["mod_color"] = new_color
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            uuid_to_color[uuid] = new_color
        auxdb_update_all_mod_colors(self.settings, uuid_to_color)

    def get_common_selected_tags(self, uuids: list[str]) -> set[str]:
        common_tags: set[str] | None = None

        for uuid in uuids:
            tags = set(auxdb_get_mod_tags(self.settings, uuid))
            if common_tags is None:
                common_tags = tags
            else:
                common_tags &= tags

        return common_tags or set()

    def refresh_mod_tags_for_uuid(self, uuid: str) -> None:
        if uuid not in self.paths:
            return

        current_mod_index = self.paths.index(uuid)
        item = self.item(current_mod_index)
        item_data = item.data(Qt.ItemDataRole.UserRole)
        item_data["mod_tags"] = auxdb_get_mod_tags(self.settings, uuid)
        item_data.__dict__["show_tags"] = bool(
            item_data.__dict__.get("show_tags", False)
        )
        item.setData(Qt.ItemDataRole.UserRole, item_data)

        widget = self.itemWidget(item)
        if isinstance(widget, ModListItemInner):
            widget.set_tags_visible(
                item_data.__dict__["show_tags"], item_data["mod_tags"]
            )
            widget.setToolTip(widget.get_tool_tip_text())
            widget._resize_text_after_icon_toggle()

        if self.currentItem() == item:
            self.mod_info_signal.emit(uuid, item)

    def set_tags_visible(self, visible: bool) -> None:
        self.show_tags = visible

        for index in range(self.count()):
            item = self.item(index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if item_data is None:
                continue

            item_data.__dict__["show_tags"] = visible
            item.setData(Qt.ItemDataRole.UserRole, item_data)

            widget = self.itemWidget(item)
            if isinstance(widget, ModListItemInner):
                widget.set_tags_visible(visible, item_data["mod_tags"])
