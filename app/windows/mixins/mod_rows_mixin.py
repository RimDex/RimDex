"""Mod row population mixin for BaseModsPanel.

Holds row-level construction from ModInfo / metadata, group headers,
metadata extraction, and the mod-selection metadata accessor used
by the deletion menu.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QComboBox, QPushButton

from app.models.metadata.metadata_structure import AboutXmlMod, ListedMod, ModType
from app.mods.mod_info import ModInfo
from app.mods.mod_utils import resolve_aux_timestamps


class ModRowsMixin:
    """Mod row population for BaseModsPanel."""

    metadata_controller: Any
    editor_model: Any
    editor_table_view: Any

    def _add_mod_row(
        self,
        mod_info: "ModInfo",
        additional_items: list[QStandardItem] | None = None,
        default_checkbox_state: bool = False,
    ) -> None:
        """
        Standardized method to add a mod row to the table.

        Args:
            mod_info: ModInfo object containing mod data
            additional_items: Optional additional QStandardItem objects for extra columns
            default_checkbox_state: Default state for the checkbox
        """
        # Base columns that all panels use
        base_items = [
            QStandardItem(mod_info.name),
            QStandardItem(mod_info.authors),
            QStandardItem(mod_info.packageid),
            QStandardItem(mod_info.published_file_id),
            QStandardItem(mod_info.supported_versions),
            QStandardItem(mod_info.downloaded_time),
            QStandardItem(mod_info.updated_on_workshop),
            QStandardItem(mod_info.source),
            QStandardItem(""),  # Path will be displayed via widget
        ]

        # Add workshop page column
        workshop_item = QStandardItem()
        base_items.append(workshop_item)

        # Add any additional columns specific to the panel
        if additional_items:
            base_items.extend(additional_items)

        # Set path key on name item for metadata lookup
        if mod_info.key:
            base_items[0].setData(mod_info.key, Qt.ItemDataRole.UserRole)

        self._add_row(base_items, default_checkbox_state)  # type: ignore[attr-defined]

        # Add path link to the path column (index 9) only if path exists and row is not blank
        if mod_info.path and mod_info.path.strip():
            path_link = self._create_path_link(mod_info.path, "pathLink")  # type: ignore[attr-defined]
            self.editor_table_view.setIndexWidget(base_items[8].index(), path_link)

        # Add workshop button to the workshop column only if published_file_id exists
        if mod_info.published_file_id and mod_info.published_file_id.strip():
            workshop_button = self._create_workshop_button(  # type: ignore[attr-defined]
                mod_info.workshop_url, "workshopButton"
            )
            self.editor_table_view.setIndexWidget(
                workshop_item.index(), workshop_button
            )

    def _add_group_header_row(self, header_text: str) -> None:
        """
        Add a group header row to the table.

        Args:
            header_text: Text for the header row
        """
        header_item = QStandardItem(header_text)
        header_item.setData(None, Qt.ItemDataRole.UserRole)

        # Create empty items for other columns
        empty_items = [
            QStandardItem("") for _ in range(self.editor_model.columnCount() - 1)
        ]
        items = [header_item] + empty_items

        self.editor_model.appendRow(items)

    def _extract_mod_info_from_metadata(
        self, key: str | None, metadata: dict[str, Any] | ListedMod
    ) -> ModInfo:
        """
        Extract ModInfo from metadata dictionary or ListedMod object.

        Args:
            key: Path key of the mod in metadata
            metadata: Metadata dictionary or ListedMod instance

        Returns:
            ModInfo object
        """
        if isinstance(metadata, ListedMod):
            # Look up aux timestamps so the mod list can show accurate
            # download / workshop-update times even when the metadata dict
            # path wasn't built from filter_eligible_mods_for_update.
            acf_touched: int | None = None
            ext_updated: int | None = None
            if key is not None:
                _, aux_entry = self.metadata_controller.get_metadata_with_path(key)
                acf_touched, ext_updated = resolve_aux_timestamps(aux_entry)
            mod_info = ModInfo.from_listed_mod(
                metadata,
                acf_time_touched=acf_touched,
                external_time_updated=ext_updated,
            )
            mod_info.key = key
            return mod_info
        return ModInfo.from_metadata(key, metadata)

    def _resolve_path_key(self, path: str) -> str | None:
        """
        Verify a mod path exists in metadata and return it as a key.

        Args:
            path: Mod path to verify

        Returns:
            The path if found in metadata, None otherwise
        """
        if self.metadata_controller.has_mod(path):
            return path
        return None

    def _populate_from_metadata(self) -> None:
        """Populate the table from metadata. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _populate_from_metadata")

    def _populate_mods(
        self,
        groups: dict[str, list[tuple[str, dict[str, Any] | ListedMod]]],
        add_group_headers: bool = False,
    ) -> None:
        """
        Populate the table with mod groups.

        Args:
            groups: Dictionary of groups, where key is group name, value is list of (path_key, metadata) tuples.
            add_group_headers: Whether to add header rows for each group.
        """
        self._clear_table_model()  # type: ignore[attr-defined]

        for group_key, mod_list in groups.items():
            if add_group_headers and group_key:
                self._add_group_header_row(group_key)

            for path_key, metadata in mod_list:
                try:
                    mod_info = self._extract_mod_info_from_metadata(path_key, metadata)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Skipping mod {path_key}: failed to extract metadata ({e})"
                    )
                    continue
                self._add_mod_row(mod_info)

    def _get_key_from_row(self, row: int, name_column: int = 1) -> str | None:
        """
        Extract the mod path key from a table row's name column.

        Args:
            row: Row index to extract key from
            name_column: Column index containing the name item with key data

        Returns:
            Path key string if found, None otherwise
        """
        try:
            if row >= self.editor_model.rowCount():
                return None

            name_item = self.editor_model.item(row, name_column)
            if name_item is None:
                return None

            return name_item.data(Qt.ItemDataRole.UserRole)
        except Exception as e:
            logger.warning(f"Error accessing key from row {row}: {e}")
            return None

    def _get_selected_mod_metadata(self) -> list[dict[str, Any]]:
        """
        Get metadata for selected mods in the table.

        Returns a list of compat dicts with keys expected by ModDeletionMenu.
        Note: the "uuid" key is a legacy name; the value is the mod path key.

        Returns:
            List of ModMetadata compat dicts for selected mods
        """
        selected_mods: list[dict[str, Any]] = []
        try:
            for row in range(self.editor_model.rowCount()):
                if self._row_is_checked(row):  # type: ignore[attr-defined]
                    path = self._get_key_from_row(row)
                    if path:
                        mod = self.metadata_controller.get_mod(path)
                        if mod is not None:
                            compat: dict[str, Any] = {
                                "path": str(mod.mod_path) if mod.mod_path else "",
                                "uuid": path,
                                "name": mod.name or "",
                                "publishedfileid": mod.published_file_id or "",
                                "steamcmd": mod.mod_type == ModType.STEAM_CMD,
                            }
                            if mod.mod_type == ModType.LUDEON:
                                compat["data_source"] = "expansion"
                            elif mod.mod_type == ModType.STEAM_WORKSHOP:
                                compat["data_source"] = "workshop"
                            elif mod.mod_type == ModType.LOCAL:
                                compat["data_source"] = "local"
                            else:
                                compat["data_source"] = str(mod.mod_type.value)
                            if isinstance(mod, AboutXmlMod):
                                compat["packageid"] = str(mod.package_id)
                            selected_mods.append(compat)
        except Exception as e:
            logger.warning(f"Error getting selected mod metadata: {e}")
        return selected_mods

    def _add_workshop_button_to_row(
        self, row_items: list[QStandardItem], pfid: str, workshop_column: int
    ) -> QPushButton:
        """
        Add a workshop button to a specific column in a row.

        Args:
            row_items: List of QStandardItem for the row
            pfid: Published file ID for the workshop URL
            workshop_column: Column index for the workshop button

        Returns:
            The created workshop button
        """
        workshop_item = row_items[workshop_column]
        workshop_button = self._create_workshop_button(  # type: ignore[attr-defined]
            f"https://steamcommunity.com/sharedfiles/filedetails/?id={pfid}",
            "workshopButton",
        )
        self.editor_table_view.setIndexWidget(workshop_item.index(), workshop_button)
        return workshop_button

    def _add_combo_box_to_row(
        self,
        row_items: list[QStandardItem],
        combo_column: int,
        items: list[str] | None = None,
    ) -> QComboBox:
        """
        Add a combo box to a specific column in a row.

        Args:
            row_items: List of QStandardItem for the row
            combo_column: Column index for the combo box
            items: Optional list of items to add to the combo box

        Returns:
            The created combo box
        """
        combo_item = row_items[combo_column]
        combo_box = QComboBox()
        combo_box.setEditable(True)
        combo_box.setObjectName("variantComboBox")
        if items:
            combo_box.addItems(items)
        self.editor_table_view.setIndexWidget(combo_item.index(), combo_box)
        return combo_box
