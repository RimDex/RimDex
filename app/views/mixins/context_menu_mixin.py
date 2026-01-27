"""Context-menu / right-click behaviour mixin for ModListWidget.

Holds the per-item context menu construction and dispatch
(``eventFilter``), the divider context menu, the "find translations"
helper, and the legacy ``ListedMod`` → dict bridge used by the context
menu code.
"""

from __future__ import annotations

import os
from difflib import SequenceMatcher
from pathlib import Path
from shutil import copy2, copytree
from traceback import format_exc
from typing import Any, Dict, cast

from loguru import logger
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtGui import QAction, QColor, QCursor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.app_info import AppInfo
from app.core.event_bus import EventBus
from app.core.generic import (
    copy_to_clipboard_safely,
    delete_files_except_extension,
    launch_process,
    open_url_browser,
    platform_specific_open,
    sanitize_filename,
)
from app.io.acf_utils import steamcmd_purge_mods
from app.models.metadata.metadata_structure import AboutXmlMod, ListedMod, ModType
from app.mods.aux_db_utils import (
    auxdb_add_mod_tags,
    auxdb_cleanup_unused_tags,
    auxdb_remove_mod_tags,
    auxdb_replace_mod_tags,
)
from app.mods.mod_utils import MOD_TYPE_TO_FILTER_SOURCE
from app.ui.dialogue import show_dialogue_conditional, show_warning
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.divider import DividerData
from app.views.mixins._shared import ModListWidgetMixinBase
from app.views.tag_edit_dialog import TagEditDialog


class ContextMenuMixin(ModListWidgetMixinBase):
    """Right-click context menu handling for ModListWidget."""

    @staticmethod
    def _mod_to_context_dict(mod: ListedMod) -> dict[str, Any]:
        """
        Build a legacy-style dict from a ListedMod for context menu code.

        This is a bridge to avoid rewriting hundreds of lines of context menu
        dict-access patterns during the MetadataController migration.
        """
        pfid = mod.published_file_id
        d: dict[str, Any] = {
            "name": mod.name,
            "path": str(mod.mod_path) if mod.mod_path is not None else "",
            "folder": mod.mod_folder or "",
            "publishedfileid": pfid,
            "steamcmd": mod.mod_type == ModType.STEAM_CMD,
            "git_repo": mod.mod_type == ModType.GIT,
        }
        # Map mod_type to legacy data_source
        d["data_source"] = MOD_TYPE_TO_FILTER_SOURCE.get(mod.mod_type, "local")
        # AboutXmlMod-specific fields
        if isinstance(mod, AboutXmlMod):
            d["packageid"] = str(mod.package_id)
            d["url"] = mod.url or ""
        else:
            d["packageid"] = ""
            d["url"] = ""
        # Derived Steam URLs
        if pfid:
            d["steam_url"] = (
                f"https://steamcommunity.com/sharedfiles/filedetails/?id={pfid}"
            )
            d["steam_uri"] = f"steam://url/CommunityFilePage/{pfid}"
        else:
            d["steam_url"] = ""
            d["steam_uri"] = ""
        return d

    def _get_selected_metadata(self) -> list[dict[str, Any]]:
        selected_items = self.selectedItems()
        metadata: list[dict[str, Any]] = []
        for source_item in selected_items:
            if type(source_item) is CustomListWidgetItem:
                item_data = source_item.data(Qt.ItemDataRole.UserRole)
                if getattr(item_data, "is_divider", False):
                    continue
                mod = self.metadata_controller.get_mod(item_data["path"])
                if mod is not None:
                    metadata.append(self._mod_to_context_dict(mod))
        return metadata

    def _calculate_translation_similarity(
        self, mod_name: str, trans_name: str
    ) -> float:
        """
        Calculate similarity score between original mod name and translation mod name.

        Uses multiple heuristics:
        1. Direct substring matching (original mod name in translation)
        2. Sequence matching ratio (difflib)
        3. Keyword matching (translation keywords presence)

        :param mod_name: Original mod name
        :param trans_name: Translation mod name
        :return: Similarity score between 0.0 and 1.0
        """
        if not mod_name or not trans_name:
            return 0.0

        # Normalize names for comparison
        mod_lower = mod_name.lower().strip()
        trans_lower = trans_name.lower().strip()

        # Check for common translation keywords
        translation_keywords = [
            "translation",
            "translate",
            "中文",
            "chinese",
            "简体",
            "繁體",
            "한국어",
            "korean",
            "日本語",
            "japanese",
            "русский",
            "russian",
            "français",
            "french",
            "deutsch",
            "german",
            "español",
            "spanish",
            "português",
            "portuguese",
            "italiano",
            "italian",
            "polski",
            "polish",
            "türkçe",
            "turkish",
            "中文翻译",
            "汉化",
            "翻译",
        ]

        has_translation_keyword = any(
            keyword in trans_lower for keyword in translation_keywords
        )

        # Bonus if translation keywords are present
        keyword_bonus = 0.2 if has_translation_keyword else 0.0

        # Check if original mod name is a substring of translation name
        if mod_lower in trans_lower:
            substring_score = 0.8
        else:
            # Try removing common prefixes/suffixes and check again
            cleaned_mod = (
                mod_lower.replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .strip()
            )
            cleaned_trans = (
                trans_lower.replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .strip()
            )

            if cleaned_mod in cleaned_trans:
                substring_score = 0.7
            else:
                # Use sequence matcher for partial matching
                substring_score = (
                    SequenceMatcher(None, mod_lower, trans_lower).ratio() * 0.6
                )

        # Combine scores
        final_score = min(1.0, substring_score + keyword_bonus)

        return final_score

    def _find_and_open_translations(
        self, package_id: str, mod_metadata: dict[str, Any]
    ) -> None:
        """
        Find and open translation mods for the specified mod.

        Searches the Steam Workshop metadata database for mods that:
        1. Depend on the target mod OR have the target mod in their loadAfter
        2. Have a "Translation" tag
        3. Match the same game version tag (e.g., "1.6")
        4. Have sufficient name similarity to the original mod

        Opens found translation mods in the browser.

        :param package_id: The packageId of the mod to find translations for
        :param mod_metadata: The metadata of the mod
        """
        steam_db = self.metadata_controller.steam_db
        steam_db_database = steam_db.database if steam_db else {}
        if not steam_db_database:
            logger.warning("Steam Workshop metadata database is not loaded")
            show_warning(
                title=QCoreApplication.translate(
                    "ModListWidget", "Database not available"
                ),
                text=QCoreApplication.translate(
                    "ModListWidget",
                    "Steam Workshop metadata database is not loaded. "
                    "Please build the database first using the Database Builder.",
                ),
            )
            return

        # Get the mod's version tags from Steam metadata
        mod_pfid = mod_metadata.get("publishedfileid")
        current_pfid = mod_pfid  # Store for dependency checking
        mod_version_tags = set()

        if mod_pfid and mod_pfid in steam_db_database:
            steam_entry = steam_db_database[mod_pfid]
            for tag_item in steam_entry.tags:
                tag = tag_item.get("tag", "")
                # Version tags are typically like "1.6", "1.5", etc.
                if tag and tag.replace(".", "").isdigit():
                    mod_version_tags.add(tag)

        logger.info(
            f"Searching for translations of mod with packageId: {package_id}, version tags: {mod_version_tags}"
        )

        # Search for translation mods
        translation_mods = []

        # Optimized: iterate through Steam metadata only once and extract all needed data
        for pfid, steam_mod_data in steam_db_database.items():
            if not steam_mod_data.tags:
                continue

            # Build tag set once for faster lookups - O(n) instead of O(n*m)
            tag_set = {
                tag_item.get("tag", "").lower() for tag_item in steam_mod_data.tags
            }

            # Fast check: must have "translation" tag
            if "translation" not in tag_set:
                continue

            # Extract version tags in a single pass
            translation_version_tags = set()
            for tag_item in steam_mod_data.tags:
                tag = tag_item.get("tag", "")
                # Cache the string processing result
                if tag and tag.replace(".", "").isdigit():
                    translation_version_tags.add(tag)

            # Check if version tags match (if we have version tags)
            if mod_version_tags and translation_version_tags:
                if not mod_version_tags.intersection(translation_version_tags):
                    continue

            # Check if this mod has the target mod as a dependency
            # Fast check with 'in' operator on dict instead of .get()
            if current_pfid not in steam_mod_data.dependencies:
                continue

            # Calculate name similarity to filter out false positives
            trans_name = steam_mod_data.steamName
            mod_name = mod_metadata.get("name", "")

            # Calculate similarity score
            similarity = self._calculate_translation_similarity(mod_name, trans_name)

            # Only build the result dict if all checks pass
            translation_mods.append(
                {
                    "pfid": pfid,
                    "name": trans_name or f"Unknown ({pfid})",
                    "url": steam_mod_data.url
                    or f"https://steamcommunity.com/sharedfiles/filedetails/?id={pfid}",
                    "similarity": similarity,
                }
            )

        if not translation_mods:
            logger.info(f"No translations found for mod: {package_id}")
            show_warning(
                title=QCoreApplication.translate(
                    "ModListWidget", "No translations found"
                ),
                text=QCoreApplication.translate(
                    "ModListWidget",
                    "No translation mods were found for this mod in the Steam Workshop database.",
                ),
            )
            return

        # Sort by similarity score (highest first) to show most relevant translations first
        translation_mods.sort(key=lambda x: cast(float, x["similarity"]), reverse=True)

        # Filter out translations with very low similarity (likely false positives)
        # Keep at least one result even if similarity is low
        SIMILARITY_THRESHOLD = 0.3
        filtered_mods = [
            m
            for m in translation_mods
            if cast(float, m["similarity"]) >= SIMILARITY_THRESHOLD
        ]
        if not filtered_mods and translation_mods:
            # If all mods filtered out, keep the best match
            filtered_mods = [translation_mods[0]]
        translation_mods = filtered_mods

        # Log found translations
        logger.info(
            f"Found {len(translation_mods)} translation(s) for {package_id} "
            f"(filtered by similarity >= {SIMILARITY_THRESHOLD})"
        )

        # If only one translation, open it directly
        if len(translation_mods) == 1:
            trans_mod = translation_mods[0]
            logger.info(
                f"Opening translation: {trans_mod['name']} - {trans_mod['url']}"
            )
            open_url_browser(cast(str, trans_mod["url"]))
            return

        # If multiple translations, let user choose
        dialog = QDialog(cast(QWidget, self))
        dialog.setWindowTitle(
            QCoreApplication.translate("ModListWidget", "Select Translation")
        )
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()

        # Add label
        label = QLabel(
            QCoreApplication.translate(
                "ModListWidget",
                f"Found {len(translation_mods)} translation(s). Select one to open:",
            )
        )
        layout.addWidget(label)

        # Add list widget
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        for trans_mod in translation_mods:
            item = QListWidgetItem(cast(str, trans_mod["name"]))
            item.setData(Qt.ItemDataRole.UserRole, trans_mod["url"])
            list_widget.addItem(item)

        # Select first item by default
        list_widget.setCurrentRow(0)

        # Enable double-click to open
        def on_double_click(item: QListWidgetItem) -> None:
            url = item.data(Qt.ItemDataRole.UserRole)
            logger.info(f"Opening translation: {item.text()} - {url}")
            open_url_browser(url)
            dialog.accept()

        list_widget.itemDoubleClicked.connect(on_double_click)
        layout.addWidget(list_widget)

        # Add buttons
        button_layout = QHBoxLayout()
        open_button = QPushButton(QCoreApplication.translate("ModListWidget", "Open"))
        cancel_button = QPushButton(
            QCoreApplication.translate("ModListWidget", "Cancel")
        )

        def on_open() -> None:
            current_item = list_widget.currentItem()
            if current_item:
                url = current_item.data(Qt.ItemDataRole.UserRole)
                logger.info(f"Opening translation: {current_item.text()} - {url}")
                open_url_browser(url)
                dialog.accept()

        open_button.clicked.connect(on_open)
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addStretch()
        button_layout.addWidget(open_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        """
        https://doc.qt.io/qtforpython/overviews/eventsandfilters.html

        Takes source object and filters an event at the ListWidget level, executes
        an action based on a per-mod_list_item contextMenu

        :param object: the source object returned from the event
        :param event: the QEvent type
        """
        if event.type() == QEvent.Type.ContextMenu and object is self:
            # Get the position of the right-click event
            pos = QCursor.pos()
            # Convert the global position to the list widget's coordinate system
            pos_local = self.mapFromGlobal(pos)
            # Get the item at the local position
            item = self.itemAt(pos_local)
            if not isinstance(item, CustomListWidgetItem):
                logger.debug("Mod list right-click non-QListWidgetItem")
                return QObject.eventFilter(cast(QObject, self), object, event)

            # Handle divider-specific context menu
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(item_data, "is_divider", False):
                return self._show_divider_context_menu(item, item_data, pos_local)

            # Otherwise, begin calculation
            logger.info("USER ACTION: Open right-click mod_list_item contextMenu")

            # GIT MOD PATHS
            # A list of git mod paths to update
            git_paths = []

            # LOCAL MOD CONVERSIONS
            # A dict to track local mod folder name -> publishedfileid
            local_steamcmd_name_to_publishedfileid = {}

            # STEAMCMD MOD PFIDS
            # A set to track any SteamCMD pfids to purge from acf data
            steamcmd_acf_pfid_purge: set[str] = set()
            # A list to track any SteamCMD mod paths
            steamcmd_mod_paths = []
            # A dict to track any SteamCMD mod publishedfileids -> name
            steamcmd_publishedfileid_to_name = {}

            # STEAM SUBSCRIBE/UNSUBSCRIBE
            # A list to track any workshop mod paths
            steam_mod_paths = []
            # A list to track any workshop mod publishedfileids
            steam_publishedfileid_to_name = {}

            # STEAMDB BLACKLIST
            # A list to track any publishedfileids we want to blacklist / remove from blacklist
            steamdb_add_blacklist = None
            steamdb_remove_blacklist = None

            # Define our QMenu & QActions
            context_menu = QMenu()
            # Open folder action
            open_folder_action = None
            # Open folder in text editor action
            open_folder_text_editor_action = None
            # Open URL in browser action
            open_url_browser_action = None
            # Open URL in Steam
            open_mod_steam_action = None
            # Copy to clipboard actions
            copy_packageid_to_clipboard_action = None
            copy_url_to_clipboard_action = None
            # Edit mod rules
            edit_mod_rules_action = None
            # Toggle warning action
            toggle_warning_action = None
            # Blacklist SteamDB options
            add_to_steamdb_blacklist_action = None
            remove_from_steamdb_blacklist_action = None
            # Convert SteamCMD -> local
            convert_steamcmd_local_action = None
            # Convert local -> SteamCMD
            convert_local_steamcmd_action = None
            # Convert Workshop -> local
            convert_workshop_local_action = None
            # Update/Re-download/re-subscribe git/steamcmd/steam mods
            re_git_action = None
            re_steamcmd_action = None
            re_steam_action = None
            # Unsubscribe mod
            unsubscribe_mod_steam_action = None
            # Change mod color
            change_mod_color_action = None
            # Reset mod color
            reset_mod_color_action = None
            # Tags
            add_mod_tags_action = None
            replace_mod_tags_action = None
            remove_mod_tags_action = None
            # Find translation mods
            find_translation_action = None
            # Disable all warnings by default
            all_warnings_toggled = False
            # Get all selected CustomListWidgetItems
            selected_items = self.selectedItems()
            # Track all paths selected
            all_selected_paths: Dict[int, str] = {}
            # Single item selected
            if len(selected_items) == 1:
                logger.debug(f"{len(selected_items)} items selected")
                source_item = selected_items[0]
                if type(source_item) is CustomListWidgetItem:
                    item_data = source_item.data(Qt.ItemDataRole.UserRole)
                    uuid = item_data["path"]
                    all_selected_paths[0] = uuid
                    # Retrieve metadata
                    mod = self.metadata_controller.get_mod(uuid)
                    if mod is None:
                        return False
                    mod_metadata = self._mod_to_context_dict(mod)
                    mod_data_source = mod_metadata.get("data_source")
                    # Open folder action text
                    open_folder_action = QAction()
                    open_folder_action.setText(
                        QCoreApplication.translate("ModListWidget", "Open folder")
                    )
                    # Open folder in text editor text
                    if self.settings.text_editor_location:
                        open_folder_text_editor_action = QAction()
                        open_folder_text_editor_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Open folder in text editor"
                            )
                        )
                    # Change mod color action
                    change_mod_color_action = QAction()
                    change_mod_color_action.setText(
                        QCoreApplication.translate("ModListWidget", "Change mod color")
                    )
                    reset_mod_color_action = QAction()
                    reset_mod_color_action.setText(
                        QCoreApplication.translate("ModListWidget", "Reset mod color")
                    )

                    add_mod_tags_action = QAction()
                    add_mod_tags_action.setText(
                        QCoreApplication.translate("ModListWidget", "Add new tags...")
                    )
                    replace_mod_tags_action = QAction()
                    replace_mod_tags_action.setText(
                        QCoreApplication.translate(
                            "ModListWidget", "Replace all tags..."
                        )
                    )
                    remove_mod_tags_action = QAction()
                    remove_mod_tags_action.setText(
                        QCoreApplication.translate("ModListWidget", "Remove all tags")
                    )

                    # If we have a "url" or "steam_url"
                    if mod_metadata.get("url") or mod_metadata.get("steam_url"):
                        open_url_browser_action = QAction()
                        open_url_browser_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Open URL in browser"
                            )
                        )
                        copy_url_to_clipboard_action = QAction()
                        copy_url_to_clipboard_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Copy URL to clipboard"
                            )
                        )
                    # If we have a "steam_uri"
                    if (
                        mod_metadata.get("steam_uri")
                        and self.settings.instances[
                            self.settings.current_instance
                        ].steam_client_integration
                    ):
                        open_mod_steam_action = QAction()
                        open_mod_steam_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Open mod in Steam"
                            )
                        )
                    # Conversion options (SteamCMD <-> local) + re-download (local mods found in SteamDB and SteamCMD)
                    if mod_data_source == "local":
                        mod_name = mod_metadata.get("name")
                        mod_folder_name = mod_metadata["folder"]
                        mod_folder_path = mod_metadata["path"]
                        publishedfileid = mod_metadata.get("publishedfileid", "")
                        if not isinstance(publishedfileid, str):
                            logger.error(
                                f"Invalid publishedfileid type: {publishedfileid} for {mod_name}"
                            )
                            publishedfileid = ""

                        _steam_db = self.metadata_controller.steam_db
                        _steam_db_db = _steam_db.database if _steam_db else {}
                        if not mod_metadata.get("steamcmd") and (
                            _steam_db_db
                            and publishedfileid
                            and publishedfileid in _steam_db_db
                        ):
                            local_steamcmd_name_to_publishedfileid[mod_folder_name] = (
                                publishedfileid
                            )
                            # Convert local mods -> steamcmd
                            convert_local_steamcmd_action = QAction()
                            convert_local_steamcmd_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Convert local mod to SteamCMD"
                                )
                            )
                        if mod_metadata.get("steamcmd"):
                            steamcmd_mod_paths.append(mod_folder_path)
                            steamcmd_publishedfileid_to_name[publishedfileid] = mod_name
                            # Convert steamcmd mods -> local
                            convert_steamcmd_local_action = QAction()
                            convert_steamcmd_local_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Convert SteamCMD mod to local"
                                )
                            )
                            # Re-download steamcmd mods
                            re_steamcmd_action = QAction()
                            re_steamcmd_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Re-download mod with SteamCMD"
                                )
                            )
                        # Update local mods that contain git repos that are not steamcmd mods
                        if not mod_metadata.get("steamcmd") and mod_metadata.get(
                            "git_repo"
                        ):
                            git_paths.append(mod_folder_path)
                            re_git_action = QAction()
                            re_git_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Update mod with git"
                                )
                            )
                    # If Workshop, and pfid, allow Steam actions
                    if mod_data_source == "workshop" and mod_metadata.get(
                        "publishedfileid"
                    ):
                        mod_name = mod_metadata.get("name")
                        mod_folder_path = mod_metadata["path"]
                        publishedfileid = mod_metadata["publishedfileid"]
                        steam_mod_paths.append(mod_folder_path)
                        steam_publishedfileid_to_name[publishedfileid] = mod_name
                        # Convert steam mods -> local
                        convert_workshop_local_action = QAction()
                        convert_workshop_local_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Convert Steam mod to local"
                            )
                        )
                        # Only enable subscription actions if user has enabled Steam client integration
                        if self.settings.instances[
                            self.settings.current_instance
                        ].steam_client_integration:
                            # Re-subscribe steam mods
                            re_steam_action = QAction()
                            re_steam_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Re-subscribe mod with Steam"
                                )
                            )
                            # Unsubscribe steam mods
                            unsubscribe_mod_steam_action = QAction()
                            unsubscribe_mod_steam_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Unsubscribe mod with Steam"
                                )
                            )
                    # SteamDB blacklist options
                    steam_db = self.metadata_controller.steam_db
                    steam_db_database = steam_db.database if steam_db else {}
                    if steam_db_database and mod_metadata.get("publishedfileid"):
                        publishedfileid = mod_metadata["publishedfileid"]
                        steam_entry = steam_db_database.get(publishedfileid)
                        if steam_entry and steam_entry.blacklist:
                            steamdb_remove_blacklist = publishedfileid
                            remove_from_steamdb_blacklist_action = QAction()
                            remove_from_steamdb_blacklist_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Remove mod from SteamDB blacklist"
                                )
                            )
                        else:
                            steamdb_add_blacklist = publishedfileid
                            add_to_steamdb_blacklist_action = QAction()
                            add_to_steamdb_blacklist_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Add mod to SteamDB blacklist"
                                )
                            )
                    # Copy packageId to clipboard
                    copy_packageid_to_clipboard_action = QAction()
                    copy_packageid_to_clipboard_action.setText(
                        QCoreApplication.translate(
                            "ModListWidget", "Copy packageId to clipboard"
                        )
                    )
                    # Edit mod rules with Rule Editor (only for individual mods)
                    edit_mod_rules_action = QAction()
                    edit_mod_rules_action.setText(
                        QCoreApplication.translate(
                            "ModListWidget", "Edit mod with Rule Editor"
                        )
                    )
                    # Ignore error action
                    toggle_warning_action = QAction()
                    toggle_warning_action.setText(
                        QCoreApplication.translate("ModListWidget", "Toggle warning")
                    )
                    package_id = mod_metadata.get("packageid")
                    if package_id and package_id in self.ignore_warning_list:
                        toggle_warning_action.setCheckable(True)
                        toggle_warning_action.setChecked(True)
                    # Find translation action (only for single mod selection)
                    if package_id:
                        find_translation_action = QAction()
                        find_translation_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Find translations"
                            )
                        )
            # Multiple items selected
            elif len(selected_items) > 1:  # Multiple items selected
                all_warnings_toggled = True
                for item_idx, source_item in enumerate(selected_items):
                    if type(source_item) is CustomListWidgetItem:
                        item_data = source_item.data(Qt.ItemDataRole.UserRole)
                        if getattr(item_data, "is_divider", False):
                            continue
                        uuid = item_data["path"]
                        all_selected_paths[item_idx] = uuid
                        # Retrieve metadata
                        mod = self.metadata_controller.get_mod(uuid)
                        if mod is None:
                            continue
                        mod_metadata = self._mod_to_context_dict(mod)
                        if all_warnings_toggled:
                            package_id = mod_metadata.get("packageid")
                            if (
                                package_id
                                and package_id not in self.ignore_warning_list
                            ):
                                all_warnings_toggled = False
                        mod_data_source = mod_metadata.get("data_source")
                        # Open folder action text
                        open_folder_action = QAction()
                        open_folder_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Open folder(s)"
                            )
                        )
                        if self.settings.text_editor_location:
                            open_folder_text_editor_action = QAction()
                            open_folder_text_editor_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Open folder(s) in text editor"
                                )
                            )
                        # Change mod color action
                        change_mod_color_action = QAction()
                        change_mod_color_action.setText("Change mod colors")
                        reset_mod_color_action = QAction()
                        reset_mod_color_action.setText("Reset mod colors")

                        add_mod_tags_action = QAction()
                        add_mod_tags_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Add new tags..."
                            )
                        )
                        replace_mod_tags_action = QAction()
                        replace_mod_tags_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Replace all tags..."
                            )
                        )
                        remove_mod_tags_action = QAction()
                        remove_mod_tags_action.setText(
                            QCoreApplication.translate(
                                "ModListWidget", "Remove all tags"
                            )
                        )

                        # If we have a "url" or "steam_url"
                        if mod_metadata.get("url") or mod_metadata.get("steam_url"):
                            open_url_browser_action = QAction()
                            open_url_browser_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Open URL(s) in browser"
                                )
                            )
                        # Conversion options (local <-> SteamCMD)
                        if mod_data_source == "local":
                            mod_name = mod_metadata.get("name")
                            mod_folder_name = mod_metadata["folder"]
                            mod_folder_path = mod_metadata["path"]
                            publishedfileid = mod_metadata.get("publishedfileid")
                            _steam_db_m = self.metadata_controller.steam_db
                            _steam_db_db_m = _steam_db_m.database if _steam_db_m else {}
                            if not mod_metadata.get("steamcmd") and (
                                _steam_db_db_m
                                and publishedfileid
                                and publishedfileid in _steam_db_db_m
                            ):
                                local_steamcmd_name_to_publishedfileid[
                                    mod_folder_name
                                ] = publishedfileid
                                # Convert local mods -> steamcmd
                                if not convert_local_steamcmd_action:
                                    convert_local_steamcmd_action = QAction()
                                    convert_local_steamcmd_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget",
                                            "Convert local mod(s) to SteamCMD",
                                        )
                                    )
                            if mod_metadata.get("steamcmd"):
                                steamcmd_mod_paths.append(mod_folder_path)
                                steamcmd_publishedfileid_to_name[publishedfileid] = (
                                    mod_name
                                )
                                # Convert steamcmd mods -> local
                                if not convert_steamcmd_local_action:
                                    convert_steamcmd_local_action = QAction()
                                    convert_steamcmd_local_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget",
                                            "Convert SteamCMD mod(s) to local",
                                        )
                                    )
                                # Re-download steamcmd mods
                                if not re_steamcmd_action:
                                    re_steamcmd_action = QAction()
                                    re_steamcmd_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget",
                                            "Re-download mod(s) with SteamCMD",
                                        )
                                    )
                            # Update git mods if local mod with git repo, but not steamcmd
                            if not mod_metadata.get("steamcmd") and mod_metadata.get(
                                "git_repo"
                            ):
                                git_paths.append(mod_folder_path)
                                if not re_git_action:
                                    re_git_action = QAction()
                                    re_git_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget", "Update mod(s) with git"
                                        )
                                    )
                        # No "Edit mod rules" when multiple selected
                        # Toggle warning
                        if item_idx == len(selected_items) - 1:
                            toggle_warning_action = QAction()
                            toggle_warning_action.setText(
                                QCoreApplication.translate(
                                    "ModListWidget", "Toggle warning(s)"
                                )
                            )
                            toggle_warning_action.setCheckable(True)
                            toggle_warning_action.setChecked(all_warnings_toggled)
                        # If Workshop, and pfid, allow Steam actions
                        if mod_data_source == "workshop" and mod_metadata.get(
                            "publishedfileid"
                        ):
                            mod_name = mod_metadata.get("name")
                            mod_folder_path = mod_metadata["path"]
                            publishedfileid = mod_metadata["publishedfileid"]
                            steam_mod_paths.append(mod_folder_path)
                            steam_publishedfileid_to_name[publishedfileid] = mod_name
                            # Convert steam mods -> local
                            if not convert_workshop_local_action:
                                convert_workshop_local_action = QAction()
                                convert_workshop_local_action.setText(
                                    QCoreApplication.translate(
                                        "ModListWidget", "Convert Steam mod(s) to local"
                                    )
                                )
                            # Only enable subscription actions if user has enabled Steam client integration
                            if self.settings.instances[
                                self.settings.current_instance
                            ].steam_client_integration:
                                # Re-subscribe steam mods
                                if not re_steam_action:
                                    re_steam_action = QAction()
                                    re_steam_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget",
                                            "Re-subscribe mod(s) with Steam",
                                        )
                                    )
                                # Unsubscribe steam mods
                                if not unsubscribe_mod_steam_action:
                                    unsubscribe_mod_steam_action = QAction()
                                    unsubscribe_mod_steam_action.setText(
                                        QCoreApplication.translate(
                                            "ModListWidget",
                                            "Unsubscribe mod(s) with Steam",
                                        )
                                    )
                        # No SteamDB blacklist options when multiple selected
            # Put together our contextMenu
            if open_folder_action:
                context_menu.addAction(open_folder_action)
            if open_folder_text_editor_action:
                context_menu.addAction(open_folder_text_editor_action)
            if change_mod_color_action:
                context_menu.addAction(change_mod_color_action)
            if reset_mod_color_action:
                context_menu.addAction(reset_mod_color_action)

            if add_mod_tags_action or replace_mod_tags_action or remove_mod_tags_action:
                tags_menu = QMenu(
                    title=QCoreApplication.translate("ModListWidget", "Tags")
                )
                if add_mod_tags_action:
                    tags_menu.addAction(add_mod_tags_action)
                if replace_mod_tags_action:
                    tags_menu.addAction(replace_mod_tags_action)
                if remove_mod_tags_action:
                    tags_menu.addAction(remove_mod_tags_action)
                context_menu.addMenu(tags_menu)

            if open_url_browser_action:
                context_menu.addAction(open_url_browser_action)
            if open_mod_steam_action:
                context_menu.addAction(open_mod_steam_action)
            if find_translation_action:
                context_menu.addAction(find_translation_action)
            if toggle_warning_action:
                context_menu.addAction(toggle_warning_action)

            context_menu.addMenu(self.deletion_sub_menu)
            context_menu.addSeparator()
            if (
                copy_packageid_to_clipboard_action
                or copy_url_to_clipboard_action
                or edit_mod_rules_action
                or re_git_action
            ):
                misc_options_menu = QMenu(
                    title=QCoreApplication.translate(
                        "ModListWidget", "Miscellaneous options"
                    )
                )
                if copy_packageid_to_clipboard_action:
                    clipboard_options_menu = QMenu(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Clipboard options"
                        )
                    )
                    clipboard_options_menu.addAction(copy_packageid_to_clipboard_action)
                    if copy_url_to_clipboard_action:
                        clipboard_options_menu.addAction(copy_url_to_clipboard_action)
                    misc_options_menu.addMenu(clipboard_options_menu)
                if edit_mod_rules_action:
                    misc_options_menu.addAction(edit_mod_rules_action)
                if re_git_action:
                    misc_options_menu.addAction(re_git_action)
                context_menu.addMenu(misc_options_menu)
            if (
                convert_local_steamcmd_action
                or convert_steamcmd_local_action
                or convert_workshop_local_action
                or re_steamcmd_action
                or re_steam_action
                or unsubscribe_mod_steam_action
                or add_to_steamdb_blacklist_action
                or remove_from_steamdb_blacklist_action
            ):
                local_folder = self.settings.instances[
                    self.settings.current_instance
                ].local_folder
                workshop_actions_menu = QMenu(
                    title=QCoreApplication.translate(
                        "ModListWidget", "Workshop mods options"
                    )
                )
                if local_folder and convert_local_steamcmd_action:
                    workshop_actions_menu.addAction(convert_local_steamcmd_action)
                if local_folder and convert_steamcmd_local_action:
                    workshop_actions_menu.addAction(convert_steamcmd_local_action)
                if local_folder and convert_workshop_local_action:
                    workshop_actions_menu.addAction(convert_workshop_local_action)
                if re_steamcmd_action:
                    workshop_actions_menu.addAction(re_steamcmd_action)
                if re_steam_action:
                    workshop_actions_menu.addAction(re_steam_action)
                if unsubscribe_mod_steam_action:
                    workshop_actions_menu.addAction(unsubscribe_mod_steam_action)
                if (
                    add_to_steamdb_blacklist_action
                    or remove_from_steamdb_blacklist_action
                ):
                    workshop_actions_menu.addSeparator()
                if add_to_steamdb_blacklist_action:
                    workshop_actions_menu.addAction(add_to_steamdb_blacklist_action)
                if remove_from_steamdb_blacklist_action:
                    workshop_actions_menu.addAction(
                        remove_from_steamdb_blacklist_action
                    )
                context_menu.addMenu(workshop_actions_menu)
            # Divider option (active list only)
            add_divider_action = None
            if self.list_type == "Active":
                context_menu.addSeparator()
                add_divider_action = QAction()
                add_divider_action.setText(
                    QCoreApplication.translate("ModListWidget", "Add divider here")
                )
                context_menu.addAction(add_divider_action)
            # Execute QMenu and return it's ACTION
            action = context_menu.exec_(self.mapToGlobal(pos_local))
            if action:  # Handle the action for all selected items
                if action == add_divider_action:
                    row = self.row(item)
                    name, ok = QInputDialog.getText(
                        cast(QWidget, self),
                        QCoreApplication.translate("ModListWidget", "Add Divider"),
                        QCoreApplication.translate("ModListWidget", "Divider name:"),
                    )
                    if ok and name.strip():
                        self.add_divider(row, name.strip())
                    return True
                if (  # ACTION: Update git mod(s)
                    action == re_git_action and len(git_paths) > 0
                ):
                    # Prompt user
                    answer = show_dialogue_conditional(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Are you sure?"
                        ),
                        text=QCoreApplication.translate(
                            "ModListWidget",
                            "You have selected {len} git mods to be updated.",
                        ).format(len=len(git_paths)),
                        information=QCoreApplication.translate(
                            "ModListWidget", "Do you want to proceed?"
                        ),
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        logger.debug(f"Updating {len(git_paths)} git mod(s)")
                        self.update_git_mods_signal.emit(git_paths)
                    return True
                elif (  # ACTION: Convert local mod(s) -> SteamCMD
                    action == convert_local_steamcmd_action
                    and len(local_steamcmd_name_to_publishedfileid) > 0
                ):
                    local_folder = self.settings.instances[
                        self.settings.current_instance
                    ].local_folder
                    for (
                        folder_name,
                        publishedfileid,
                    ) in local_steamcmd_name_to_publishedfileid.items():
                        original_mod_path = str((Path(local_folder) / folder_name))
                        renamed_mod_path = str((Path(local_folder) / publishedfileid))
                        if os.path.exists(original_mod_path):
                            if not os.path.exists(renamed_mod_path):
                                try:
                                    os.rename(original_mod_path, renamed_mod_path)
                                    logger.debug(
                                        f'Successfully "converted" local mod -> SteamCMD by renaming from {folder_name} -> {publishedfileid}'
                                    )
                                except Exception as e:
                                    stacktrace = format_exc()
                                    logger.error(
                                        f"Failed to convert mod: {original_mod_path} - {e}"
                                    )
                                    logger.error(stacktrace)
                            else:
                                logger.warning(
                                    f"Failed to convert mod! Destination already exists: {renamed_mod_path}"
                                )
                    self.refresh_signal.emit()
                    return True
                elif (  # ACTION: Convert SteamCMD mod(s) -> local
                    action == convert_steamcmd_local_action
                    and len(steamcmd_publishedfileid_to_name) > 0
                ):
                    local_folder = self.settings.instances[
                        self.settings.current_instance
                    ].local_folder
                    for (
                        publishedfileid,
                        mod_name,
                    ) in steamcmd_publishedfileid_to_name.items():
                        mod_name = (
                            sanitize_filename(mod_name)
                            if mod_name
                            else f"{publishedfileid}_local"
                        )
                        original_mod_path = str((Path(local_folder) / publishedfileid))
                        renamed_mod_path = str((Path(local_folder) / mod_name))
                        if os.path.exists(original_mod_path):
                            if not os.path.exists(renamed_mod_path):
                                try:
                                    os.rename(original_mod_path, renamed_mod_path)
                                    logger.debug(
                                        f'Successfully "converted" SteamCMD mod by renaming from {publishedfileid} -> {mod_name}'
                                    )
                                except Exception as e:
                                    stacktrace = format_exc()
                                    logger.error(
                                        f"Failed to convert mod: {original_mod_path} - {e}"
                                    )
                                    logger.error(stacktrace)
                            else:
                                logger.warning(
                                    f"Failed to convert mod! Destination already exists: {renamed_mod_path}"
                                )
                    self.refresh_signal.emit()
                    return True
                elif (  # ACTION: Re-download SteamCMD mod(s)
                    action == re_steamcmd_action
                    and len(steamcmd_publishedfileid_to_name.keys()) > 0
                ):
                    logger.debug(
                        f"Selected mods for deleting + redownloading: {steamcmd_publishedfileid_to_name}"
                    )
                    steamcmd_publishedfileid_to_redownload = (
                        steamcmd_publishedfileid_to_name.keys()
                    )
                    logger.debug(
                        f"Selected publishedfileid for deleting + redownloading: {steamcmd_publishedfileid_to_redownload}"
                    )
                    # Prompt user
                    answer = show_dialogue_conditional(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Are you sure?"
                        ),
                        text=QCoreApplication.translate(
                            "ModListWidget",
                            "You have selected {len} mods for deletion + re-download.",
                        ).format(len=len(steamcmd_publishedfileid_to_redownload)),
                        information=QCoreApplication.translate(
                            "ModListWidget",
                            "<br>This operation will recursively delete all mod files, except for .dds textures found, "
                            + "and attempt to re-download the mods via SteamCMD. Do you want to proceed?",
                        ),
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        logger.debug(
                            f"Deleting + redownloading {len(steamcmd_publishedfileid_to_redownload)} SteamCMD mod(s)"
                        )
                        for path in steamcmd_mod_paths:
                            # Delete all files except .dds
                            delete_files_except_extension(
                                directory=path, extension=".dds"
                            )
                            # Calculate SteamCMD mod publishedfileids to purge from acf metadata
                            steamcmd_acf_pfid_purge = set(
                                steamcmd_publishedfileid_to_redownload
                            )
                        # Purge any deleted SteamCMD mods from acf metadata (only if auto-clear depot cache is enabled)
                        if steamcmd_acf_pfid_purge:
                            steamcmd_purge_mods(
                                metadata_controller=self.metadata_controller,
                                publishedfileids=steamcmd_acf_pfid_purge,
                                auto_clear_enabled=self.settings.instances[
                                    self.settings.current_instance
                                ].steamcmd_auto_clear_depot_cache,
                            )
                        # Emit signal to steamcmd downloader to re-download
                        logger.debug(
                            f"Emitting do_steamcmd_download for {list(steamcmd_publishedfileid_to_redownload)}"
                        )
                        EventBus().do_steamcmd_download.emit(
                            list(steamcmd_publishedfileid_to_redownload)
                        )
                    return True
                elif (  # ACTION: Convert Steam mod(s) -> local
                    action == convert_workshop_local_action
                    and len(steam_mod_paths) > 0
                    and len(steam_publishedfileid_to_name) > 0
                ):
                    for path in steam_mod_paths:
                        publishedfileid_from_folder_name = os.path.split(path)[1]
                        mod_name = steam_publishedfileid_to_name.get(
                            publishedfileid_from_folder_name
                        )
                        if mod_name:
                            mod_name = sanitize_filename(mod_name)
                        renamed_mod_path = str(
                            (
                                Path(
                                    self.settings.instances[
                                        self.settings.current_instance
                                    ].local_folder
                                )
                                / (
                                    mod_name
                                    if mod_name
                                    else publishedfileid_from_folder_name
                                )
                            )
                        )
                        if os.path.exists(path):
                            try:
                                if os.path.exists(renamed_mod_path):
                                    logger.warning(
                                        "Destination exists. Removing all files except for .dds textures first..."
                                    )
                                    delete_files_except_extension(
                                        directory=renamed_mod_path, extension=".dds"
                                    )
                                try:
                                    copytree(path, renamed_mod_path)
                                except FileExistsError:
                                    for root, dirs, files in os.walk(path):
                                        dest_dir = root.replace(path, renamed_mod_path)
                                        if not os.path.isdir(dest_dir):
                                            os.makedirs(dest_dir)
                                        for file in files:
                                            src_file = os.path.join(root, file)
                                            dst_file = os.path.join(dest_dir, file)
                                            copy2(src_file, dst_file)
                                logger.debug(
                                    f'Successfully "converted" Steam mod by copying {publishedfileid_from_folder_name} -> {mod_name} and migrating mod to local mods directory'
                                )
                            except Exception as e:
                                stacktrace = format_exc()
                                logger.error(f"Failed to convert mod: {path} - {e}")
                                logger.error(stacktrace)
                    self.refresh_signal.emit()
                    return True
                elif (  # ACTION: Re-subscribe to mod(s) with Steam
                    action == re_steam_action and len(steam_publishedfileid_to_name) > 0
                ):
                    publishedfileids = steam_publishedfileid_to_name.keys()
                    # Prompt user
                    answer = show_dialogue_conditional(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Are you sure?"
                        ),
                        text=QCoreApplication.translate(
                            "ModListWidget",
                            "You have selected {len} mods for resubscribe:(unsubscribe + subscribe).",
                        ).format(len=len(publishedfileids)),
                        information=QCoreApplication.translate(
                            "ModListWidget",
                            "<br>This operation will potentially delete .dds textures leftover. Steam is unreliable for this. Do you want to proceed?",
                        ),
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        logger.warning(
                            f"re-subscribing: (Unsubscribing + subscribing) to {len(publishedfileids)} mod(s)"
                        )
                        for path in steam_mod_paths:
                            delete_files_except_extension(
                                directory=path, extension=".dds"
                            )
                        EventBus().do_steamworks_api_call.emit(
                            [
                                "resubscribe",
                                [int(str_pfid) for str_pfid in publishedfileids],
                            ]
                        )
                    return True
                elif (  # ACTION: Unsubscribe mod(s) with steam
                    action == unsubscribe_mod_steam_action
                    and len(steam_publishedfileid_to_name) > 0
                ):
                    publishedfileids = steam_publishedfileid_to_name.keys()
                    # Prompt user
                    answer = show_dialogue_conditional(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Are you sure?"
                        ),
                        text=QCoreApplication.translate(
                            "ModListWidget",
                            "You have selected {len} mods for unsubscribe.",
                        ).format(len=len(publishedfileids)),
                        information=QCoreApplication.translate(
                            "ModListWidget", "<br>Do you want to proceed?"
                        ),
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        logger.debug(
                            f"Unsubscribing from {len(publishedfileids)} mod(s)"
                        )
                        EventBus().do_steamworks_api_call.emit(
                            [
                                "unsubscribe",
                                [int(str_pfid) for str_pfid in publishedfileids],
                            ]
                        )
                    return True
                elif (
                    action == add_to_steamdb_blacklist_action
                ):  # ACTION: Blacklist workshop mod in SteamDB
                    _sdb_add = self.metadata_controller.steam_db
                    if _sdb_add is None or steamdb_add_blacklist is None:
                        logger.error(
                            f"Unable to add mod to SteamDB blacklist: {steamdb_remove_blacklist}"
                        )
                        show_warning(
                            "Warning",
                            "Unable to add mod to SteamDB blacklist",
                            "Metadata controller steam_db or steamdb_add_blacklist was None type",
                            parent=cast(QWidget, self),
                        )
                        return False

                    _bl_entry = _sdb_add.database.get(steamdb_add_blacklist)
                    _bl_name = (
                        _bl_entry.steamName if _bl_entry else steamdb_add_blacklist
                    )
                    args, ok = QInputDialog.getText(
                        cast(QWidget, self),
                        QCoreApplication.translate("ModListWidget", "Add comment"),
                        QCoreApplication.translate(
                            "ModListWidget",
                            "Enter a comment providing your reasoning for wanting to blacklist this mod: ",
                        )
                        + f"{_bl_name}",
                    )
                    if ok:
                        self.steamdb_blacklist_signal.emit(
                            [steamdb_add_blacklist, True, args]
                        )
                    else:
                        show_warning(
                            title=QCoreApplication.translate(
                                "ModListWidget", "Unable to add to blacklist"
                            ),
                            text=QCoreApplication.translate(
                                "ModListWidget",
                                "Comment was not provided or entry was cancelled. Comments are REQUIRED for this action!",
                            ),
                        )
                    return True
                elif (
                    action == remove_from_steamdb_blacklist_action
                ):  # ACTION: Blacklist workshop mod in SteamDB
                    _sdb_rm = self.metadata_controller.steam_db
                    if _sdb_rm is None or steamdb_remove_blacklist is None:
                        logger.error(
                            f"Unable to remove mod from SteamDB blacklist: {steamdb_remove_blacklist}"
                        )
                        show_warning(
                            "Warning",
                            "Unable to remove mod from SteamDB blacklist",
                            "Metadata controller steam_db or steamdb_remove_blacklist was None type",
                            parent=cast(QWidget, self),
                        )
                        return False

                    _rm_entry = _sdb_rm.database.get(steamdb_remove_blacklist)
                    _rm_name = (
                        _rm_entry.steamName if _rm_entry else steamdb_remove_blacklist
                    )
                    answer = show_dialogue_conditional(
                        title=QCoreApplication.translate(
                            "ModListWidget", "Are you sure?"
                        ),
                        text=QCoreApplication.translate(
                            "ModListWidget", "This will remove the selected mod, "
                        )
                        + f"{_rm_name}, "
                        + "from your configured Steam DB blacklist."
                        + "<br>Do you want to proceed?",
                    )
                    if answer == QMessageBox.StandardButton.Yes:
                        self.steamdb_blacklist_signal.emit(
                            [steamdb_remove_blacklist, False]
                        )
                    return True

                if action in [add_mod_tags_action, replace_mod_tags_action]:
                    selected_uuids = list(all_selected_paths.values())
                    existing_selected_tags = self.get_common_selected_tags(
                        selected_uuids
                    )

                    tag_dialog = TagEditDialog(
                        settings=self.settings,
                        title=(
                            QCoreApplication.translate("ModListWidget", "Replace tags")
                            if action == replace_mod_tags_action
                            else QCoreApplication.translate("ModListWidget", "Add tags")
                        ),
                        existing_selected_tags=existing_selected_tags,
                        parent=cast(QWidget, self),
                    )

                    if tag_dialog.exec() == QDialog.DialogCode.Accepted:
                        tags = tag_dialog.selected_tags()

                        for selected_uuid in selected_uuids:
                            if action == replace_mod_tags_action:
                                auxdb_replace_mod_tags(
                                    self.settings,
                                    selected_uuid,
                                    tags,
                                )
                            else:
                                auxdb_add_mod_tags(
                                    self.settings,
                                    selected_uuid,
                                    tags,
                                )

                            self.refresh_mod_tags_for_uuid(selected_uuid)

                        if action == replace_mod_tags_action:
                            auxdb_cleanup_unused_tags(self.settings)

                        self.tags_changed_signal.emit()
                        return True
                    return True

                if action == remove_mod_tags_action:
                    selected_uuids = list(all_selected_paths.values())
                    for selected_uuid in selected_uuids:
                        auxdb_remove_mod_tags(self.settings, selected_uuid)
                        self.refresh_mod_tags_for_uuid(selected_uuid)
                    auxdb_cleanup_unused_tags(self.settings)
                    self.tags_changed_signal.emit()
                    return True
                # If user is changing mod color, display color picker once no matter how many mods are selected
                invalid_color = True
                new_color = QColor()
                if action == change_mod_color_action:
                    color_dlg = QColorDialog(
                        options=QColorDialog.ColorDialogOption.DontUseNativeDialog
                    )
                    self.SetUserCustomColors(color_dlg)
                    new_color = color_dlg.getColor()
                    self.SaveUserCustomColors(color_dlg)
                    invalid_color = not new_color.isValid()
                if action in self.deletion_sub_menu.actions():
                    # Deletion menu handles whatever action it was, exit now
                    return True
                # Execute action for each selected mod
                for item_idx, source_item in enumerate(selected_items):
                    if type(source_item) is CustomListWidgetItem:
                        item_data = source_item.data(Qt.ItemDataRole.UserRole)
                        if getattr(item_data, "is_divider", False):
                            continue
                        uuid = all_selected_paths[item_idx]
                        # Retrieve metadata
                        mod_obj = self.metadata_controller.get_mod(uuid)
                        if mod_obj is None:
                            continue
                        mod_metadata = self._mod_to_context_dict(mod_obj)
                        mod_data_source = mod_metadata.get("data_source")
                        mod_path = mod_metadata["path"]
                        # Toggle warning action
                        if action == toggle_warning_action:
                            if len(selected_items) > 1:
                                # If toggling multiple items, if all of them are already toggled off then toggle back on.
                                # Otherwise if they are all off or a mix, toggled them all on.
                                if all_warnings_toggled:
                                    self.toggle_warning(mod_metadata["packageid"], uuid)
                                else:
                                    if not item_data["warning_toggled"]:
                                        self.toggle_warning(
                                            mod_metadata["packageid"], uuid
                                        )
                            else:
                                self.toggle_warning(mod_metadata["packageid"], uuid)
                        elif action == change_mod_color_action and not invalid_color:
                            if (
                                len(selected_items) > 1
                                and item_idx == len(selected_items) - 1
                            ):
                                self.change_all_mod_colors(
                                    list(all_selected_paths.values()), new_color
                                )
                            elif len(selected_items) == 1:
                                self.change_mod_color(uuid, new_color)
                        elif action == reset_mod_color_action:
                            if (
                                len(selected_items) > 1
                                and item_idx == len(selected_items) - 1
                            ):
                                self.reset_all_mod_colors(
                                    list(all_selected_paths.values())
                                )
                            elif len(selected_items) == 1:
                                self.reset_mod_color(uuid)
                        # Open folder action
                        elif action == open_folder_action:  # ACTION: Open folder
                            if os.path.exists(mod_path):  # If the path actually exists
                                logger.info(f"Opening folder: {mod_path}")
                                platform_specific_open(mod_path)
                        elif (
                            action == open_folder_text_editor_action
                        ):  # ACTION: Open folder in text editor
                            if os.path.exists(mod_path):
                                logger.info(
                                    f"Opening folder in text editor: {mod_path}"
                                )
                                launch_process(
                                    self.settings.text_editor_location,
                                    self.settings.text_editor_folder_arg.split(" ")
                                    + [mod_path],
                                    str(AppInfo().application_folder),
                                )

                        # Open url action
                        elif (
                            action == open_url_browser_action
                        ):  # ACTION: Open URL in browser
                            if mod_metadata.get("url") or mod_metadata.get(
                                "steam_url"
                            ):  # If we have some form of "url" to work with...
                                url = None
                                if (
                                    mod_data_source == "expansion"
                                    or mod_metadata.get("steamcmd")
                                    or mod_data_source == "workshop"
                                ):
                                    url = mod_metadata.get(
                                        "steam_url", mod_metadata.get("url")
                                    )
                                elif (
                                    mod_data_source == "local"
                                    and not mod_metadata.get("steamcmd")
                                ):
                                    url = mod_metadata.get(
                                        "url", mod_metadata.get("steam_url")
                                    )
                                if url:
                                    logger.info(f"Opening url in browser: {url}")
                                    open_url_browser(url)
                        # Open Steam URI with Steam action
                        elif (
                            action == open_mod_steam_action
                        ):  # ACTION: Open steam:// uri in Steam
                            if mod_metadata.get("steam_uri"):  # If we have steam_uri
                                platform_specific_open(mod_metadata["steam_uri"])
                        # Find translation mods action
                        elif (
                            action == find_translation_action
                        ):  # ACTION: Find translation mods
                            package_id = mod_metadata.get("packageid")
                            if package_id:
                                self._find_and_open_translations(
                                    package_id, mod_metadata
                                )
                        # Copy to clipboard actions
                        elif (
                            action == copy_packageid_to_clipboard_action
                        ):  # ACTION: Copy packageId to clipboard
                            copy_to_clipboard_safely(mod_metadata["packageid"])
                        elif (
                            action == copy_url_to_clipboard_action
                        ):  # ACTION: Copy URL to clipboard
                            if mod_metadata.get("url") or mod_metadata.get(
                                "steam_url"
                            ):  # If we have some form of "url" to work with...
                                url = None
                                if (
                                    mod_data_source == "expansion"
                                    or mod_metadata.get("steamcmd")
                                    or mod_data_source == "workshop"
                                ):
                                    url = mod_metadata.get(
                                        "steam_url", mod_metadata.get("url")
                                    )
                                elif (
                                    mod_data_source == "local"
                                    and not mod_metadata.get("steamcmd")
                                ):
                                    url = mod_metadata.get(
                                        "url", mod_metadata.get("steam_url")
                                    )
                                if url:
                                    copy_to_clipboard_safely(url)
                        # Edit mod rules action
                        elif action == edit_mod_rules_action:
                            self.edit_rules_signal.emit(
                                True, "user_rules", mod_metadata["packageid"]
                            )
            return True
        return QObject.eventFilter(cast(QObject, self), object, event)

    def _show_divider_context_menu(
        self,
        item: CustomListWidgetItem,
        data: DividerData,
        pos_local: Any,
    ) -> bool:
        menu = QMenu()
        rename_action = menu.addAction(
            QCoreApplication.translate("ModListWidget", "Rename divider")
        )
        toggle_action = menu.addAction(
            QCoreApplication.translate("ModListWidget", "Expand")
            if data.collapsed
            else QCoreApplication.translate("ModListWidget", "Collapse")
        )
        menu.addSeparator()
        delete_action = menu.addAction(
            QCoreApplication.translate("ModListWidget", "Delete divider")
        )
        action = menu.exec_(self.mapToGlobal(pos_local))
        if action == rename_action:
            new_name, ok = QInputDialog.getText(
                cast(QWidget, self),
                QCoreApplication.translate("ModListWidget", "Rename Divider"),
                QCoreApplication.translate("ModListWidget", "New name:"),
                text=data.name,
            )
            if ok and new_name.strip():
                self.rename_divider(data.uuid, new_name.strip())
        elif action == toggle_action:
            self.toggle_divider_collapse(data.uuid)
        elif action == delete_action:
            self.remove_divider(data.uuid)
        return True
