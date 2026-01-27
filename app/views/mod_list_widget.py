import os
from difflib import SequenceMatcher
from pathlib import Path
from shutil import copy2, copytree
from traceback import format_exc
from typing import Any, Dict, cast

from loguru import logger
from platformdirs import PlatformDirs
from PySide6.QtCore import (
    QEvent,
    QItemSelection,
    QModelIndex,
    QObject,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDropEvent,
    QFocusEvent,
    QKeyEvent,
    QKeySequence,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
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

from app.controllers.metadata_controller import MetadataController
from app.controllers.metadata_db_controller import AuxMetadataController
from app.models.divider import DividerData, generate_divider_uuid, is_divider_uuid
from app.models.metadata.metadata_structure import AboutXmlMod, ListedMod, ModType
from app.models.settings import Settings
from app.sort.mod_sorting import (
    ModsPanelSortKey,
    sort_paths,
)
from app.utils.acf_utils import steamcmd_purge_mods
from app.utils.app_info import AppInfo
from app.utils.aux_db_utils import (
    auxdb_add_mod_tags,
    auxdb_cleanup_unused_tags,
    auxdb_get_mod_tags,
    auxdb_remove_mod_tags,
    auxdb_replace_mod_tags,
    auxdb_update_all_mod_colors,
    auxdb_update_mod_color,
)
from app.utils.constants import KNOWN_MOD_REPLACEMENTS
from app.utils.custom_list_widget_item import CustomListWidgetItem
from app.utils.custom_list_widget_item_metadata import (
    CustomListWidgetItemMetadata,
    bulk_prefetch_item_metadata,
)
from app.utils.event_bus import EventBus
from app.utils.generic import (
    copy_to_clipboard_safely,
    delete_files_except_extension,
    launch_process,
    open_url_browser,
    platform_specific_open,
    sanitize_filename,
)
from app.utils.mod_utils import MOD_TYPE_TO_FILTER_SOURCE
from app.utils.xml import extract_xml_package_ids, fast_rimworld_xml_save_validation
from app.views.deletion_menu import ModDeletionMenu
from app.views.dialogue import show_dialogue_conditional, show_warning
from app.views.divider_widget import DividerItemInner
from app.views.mod_list_item_inner import ModListItemInner
from app.views.tag_edit_dialog import TagEditDialog


class ModListWidget(QListWidget):
    """
    Subclass for QListWidget. Used to store lists for
    active and inactive mods. Mods can be rearranged within
    their own lists or moved from one list to another.
    """

    SORT_TEXT_TO_KEY_MAP = {
        "Name": ModsPanelSortKey.MODNAME,
        "Author": ModsPanelSortKey.AUTHOR,
        "Modified Time": ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME,
        "Folder Size": ModsPanelSortKey.FOLDER_SIZE,
        "Version": ModsPanelSortKey.VERSION,
        "PackageId": ModsPanelSortKey.PACKAGEID,
        "Color": ModsPanelSortKey.MOD_COLOR,
        "Tags": ModsPanelSortKey.MOD_TAGS,
        "Workshop Updated": ModsPanelSortKey.MOD_UPDATED,
    }

    @staticmethod
    def _text_to_sort_key(text: str) -> ModsPanelSortKey:
        return ModListWidget.SORT_TEXT_TO_KEY_MAP.get(text, ModsPanelSortKey.MODNAME)

    edit_rules_signal = Signal(bool, str, str)
    item_added_signal = Signal(str)
    key_press_signal = Signal(str)
    list_update_signal = Signal(str)
    mod_info_signal = Signal(str, CustomListWidgetItem)
    recalculate_warnings_signal = Signal()
    refresh_signal = Signal()
    tags_changed_signal = Signal()
    update_git_mods_signal = Signal(list)
    steamdb_blacklist_signal = Signal(list)

    def __init__(
        self,
        list_type: str,
        settings: Settings,
        metadata_controller: MetadataController,
    ) -> None:
        """
        Initialize the ListWidget with a dict of mods.
        Keys are the package ids and values are a dict of
        mod attributes. See tags:
        https://rimworldwiki.com/wiki/About.xml
        """
        logger.debug("Initializing ModListWidget")

        # Cache list_type for later use
        self.list_type = list_type

        # Cache MetadataController instance
        self.metadata_controller = metadata_controller

        self.settings = settings

        super(ModListWidget, self).__init__()

        # Track when a custom widget (ModListItemInner) is selected/not selected
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Allow for dragging and dropping between lists
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        # Allow for selecting and moving multiple items
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # When an item is clicked, display the mod information
        self.currentItemChanged.connect(self.mod_changed_to)
        self.itemClicked.connect(self.mod_clicked)

        # When an item is double clicked, move it to the opposite list
        self.itemDoubleClicked.connect(self.mod_double_clicked)

        # Add an eventFilter for per mod_list_item context menu
        self.installEventFilter(self)

        # Disable horizontal scroll bar
        self.horizontalScrollBar().setEnabled(False)
        self.horizontalScrollBar().setVisible(False)

        # Optimizes performance
        # self.setUniformItemSizes(True)

        # Slot to handle item widgets when itemChanged()
        self.itemChanged.connect(self.handle_item_data_changed)

        # Allow inserting custom list items
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )

        # Handle removing items to update count
        self.model().rowsAboutToBeRemoved.connect(
            self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
        )

        # Lazy load ModListItemInner
        self.verticalScrollBar().valueChanged.connect(self.check_widgets_visible)

        # This set is used to keep track of mods that have been loaded
        # into widgets. Used for an optimization strategy for `handle_rows_inserted`
        self.paths: list[str] = []
        self.ignore_warning_list: list[str] = []
        # Cache of latest save package ids to check new mods
        self._latest_save_package_ids: set[str] | None = None

        # Translation status
        self.show_translation_status: bool = False
        self.translation_lookup: set[str] = set()

        # User tags display state. This must survive list rebuilds/sorting.
        self.show_tags: bool = False

        self.deletion_sub_menu = ModDeletionMenu(
            self.settings,
            self._get_selected_metadata,
            metadata_controller=self.metadata_controller,
            remove_from_uuids=self.paths,
        )
        logger.debug("Finished ModListWidget initialization")

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

    def on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        """
        Used to indicate when the custom widget is selected/not selected.
        """
        for index in selected.indexes():
            item = self.item(index.row())
            widget = self.itemWidget(item)
            if widget and (set_selected := getattr(widget, "set_selected", None)):
                set_selected(True)

        for index in deselected.indexes():
            item = self.item(index.row())
            widget = self.itemWidget(item)
            if widget and (set_selected := getattr(widget, "set_selected", None)):
                set_selected(False)

    def item(self, row: int) -> CustomListWidgetItem:
        """
        Return the currently selected item.

        It should always be a CustomListWidgetItem.*
        """
        widget = super().item(row)
        # This fixes mypy linter errors
        # * The only scenario of where the item is QListWidgetItem is in dropEvent, where it's dropped from one list to another.
        # * This is handled in dropEvent directly and it converts this item to CustomListWidgetItem.
        return cast(CustomListWidgetItem, widget)

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        source_widget = event.source()
        drop_action = event.dropAction()
        # Only manipulate paths for within-list reorder (same source and dest).
        # For cross-list drops, handle_rows_inserted (queued) handles path
        # insertion exclusively — doing it here too creates duplicates that
        # break the count guard in handle_rows_inserted.
        if drop_action == Qt.DropAction.MoveAction and source_widget == self:
            new_indexes = [index.row() for index in self.selectedIndexes()]
            paths = [
                item.data(Qt.ItemDataRole.UserRole)["path"]
                for item in self.selectedItems()
            ]
            for idx, path in zip(new_indexes, paths):
                if path in self.paths:
                    self.paths.remove(path)
                self.paths.insert(idx, path)
        # Re-apply divider collapse states after reorder
        self.apply_collapse_states()
        logger.debug(
            f"Emitting {self.list_type} list update signal after rows dropped [{self.count()}]"
        )
        # Emit signal for within-list drops. Cross-list drops will emit
        # from handle_rows_inserted once the queued insertion completes.
        if source_widget == self:
            self.list_update_signal.emit("drop")

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
                title=self.tr("Database not available"),
                text=self.tr(
                    "Steam Workshop metadata database is not loaded. "
                    "Please build the database first using the Database Builder."
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
                title=self.tr("No translations found"),
                text=self.tr(
                    "No translation mods were found for this mod in the Steam Workshop database."
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
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Select Translation"))
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()

        # Add label
        label = QLabel(
            self.tr(
                f"Found {len(translation_mods)} translation(s). Select one to open:"
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
        open_button = QPushButton(self.tr("Open"))
        cancel_button = QPushButton(self.tr("Cancel"))

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
                return super().eventFilter(object, event)

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
                    open_folder_action.setText(self.tr("Open folder"))
                    # Open folder in text editor text
                    if self.settings.text_editor_location:
                        open_folder_text_editor_action = QAction()
                        open_folder_text_editor_action.setText(
                            self.tr("Open folder in text editor")
                        )
                    # Change mod color action
                    change_mod_color_action = QAction()
                    change_mod_color_action.setText(self.tr("Change mod color"))
                    reset_mod_color_action = QAction()
                    reset_mod_color_action.setText(self.tr("Reset mod color"))

                    add_mod_tags_action = QAction()
                    add_mod_tags_action.setText(self.tr("Add new tags..."))
                    replace_mod_tags_action = QAction()
                    replace_mod_tags_action.setText(self.tr("Replace all tags..."))
                    remove_mod_tags_action = QAction()
                    remove_mod_tags_action.setText(self.tr("Remove all tags"))

                    # If we have a "url" or "steam_url"
                    if mod_metadata.get("url") or mod_metadata.get("steam_url"):
                        open_url_browser_action = QAction()
                        open_url_browser_action.setText(self.tr("Open URL in browser"))
                        copy_url_to_clipboard_action = QAction()
                        copy_url_to_clipboard_action.setText(
                            self.tr("Copy URL to clipboard")
                        )
                    # If we have a "steam_uri"
                    if (
                        mod_metadata.get("steam_uri")
                        and self.settings.instances[
                            self.settings.current_instance
                        ].steam_client_integration
                    ):
                        open_mod_steam_action = QAction()
                        open_mod_steam_action.setText(self.tr("Open mod in Steam"))
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
                                self.tr("Convert local mod to SteamCMD")
                            )
                        if mod_metadata.get("steamcmd"):
                            steamcmd_mod_paths.append(mod_folder_path)
                            steamcmd_publishedfileid_to_name[publishedfileid] = mod_name
                            # Convert steamcmd mods -> local
                            convert_steamcmd_local_action = QAction()
                            convert_steamcmd_local_action.setText(
                                self.tr("Convert SteamCMD mod to local")
                            )
                            # Re-download steamcmd mods
                            re_steamcmd_action = QAction()
                            re_steamcmd_action.setText(
                                self.tr("Re-download mod with SteamCMD")
                            )
                        # Update local mods that contain git repos that are not steamcmd mods
                        if not mod_metadata.get("steamcmd") and mod_metadata.get(
                            "git_repo"
                        ):
                            git_paths.append(mod_folder_path)
                            re_git_action = QAction()
                            re_git_action.setText(self.tr("Update mod with git"))
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
                            self.tr("Convert Steam mod to local")
                        )
                        # Only enable subscription actions if user has enabled Steam client integration
                        if self.settings.instances[
                            self.settings.current_instance
                        ].steam_client_integration:
                            # Re-subscribe steam mods
                            re_steam_action = QAction()
                            re_steam_action.setText(
                                self.tr("Re-subscribe mod with Steam")
                            )
                            # Unsubscribe steam mods
                            unsubscribe_mod_steam_action = QAction()
                            unsubscribe_mod_steam_action.setText(
                                self.tr("Unsubscribe mod with Steam")
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
                                self.tr("Remove mod from SteamDB blacklist")
                            )
                        else:
                            steamdb_add_blacklist = publishedfileid
                            add_to_steamdb_blacklist_action = QAction()
                            add_to_steamdb_blacklist_action.setText(
                                self.tr("Add mod to SteamDB blacklist")
                            )
                    # Copy packageId to clipboard
                    copy_packageid_to_clipboard_action = QAction()
                    copy_packageid_to_clipboard_action.setText(
                        self.tr("Copy packageId to clipboard")
                    )
                    # Edit mod rules with Rule Editor (only for individual mods)
                    edit_mod_rules_action = QAction()
                    edit_mod_rules_action.setText(self.tr("Edit mod with Rule Editor"))
                    # Ignore error action
                    toggle_warning_action = QAction()
                    toggle_warning_action.setText(self.tr("Toggle warning"))
                    package_id = mod_metadata.get("packageid")
                    if package_id and package_id in self.ignore_warning_list:
                        toggle_warning_action.setCheckable(True)
                        toggle_warning_action.setChecked(True)
                    # Find translation action (only for single mod selection)
                    if package_id:
                        find_translation_action = QAction()
                        find_translation_action.setText(self.tr("Find translations"))
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
                        open_folder_action.setText(self.tr("Open folder(s)"))
                        if self.settings.text_editor_location:
                            open_folder_text_editor_action = QAction()
                            open_folder_text_editor_action.setText(
                                self.tr("Open folder(s) in text editor")
                            )
                        # Change mod color action
                        change_mod_color_action = QAction()
                        change_mod_color_action.setText("Change mod colors")
                        reset_mod_color_action = QAction()
                        reset_mod_color_action.setText("Reset mod colors")

                        add_mod_tags_action = QAction()
                        add_mod_tags_action.setText(self.tr("Add new tags..."))
                        replace_mod_tags_action = QAction()
                        replace_mod_tags_action.setText(self.tr("Replace all tags..."))
                        remove_mod_tags_action = QAction()
                        remove_mod_tags_action.setText(self.tr("Remove all tags"))

                        # If we have a "url" or "steam_url"
                        if mod_metadata.get("url") or mod_metadata.get("steam_url"):
                            open_url_browser_action = QAction()
                            open_url_browser_action.setText(
                                self.tr("Open URL(s) in browser")
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
                                        self.tr("Convert local mod(s) to SteamCMD")
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
                                        self.tr("Convert SteamCMD mod(s) to local")
                                    )
                                # Re-download steamcmd mods
                                if not re_steamcmd_action:
                                    re_steamcmd_action = QAction()
                                    re_steamcmd_action.setText(
                                        self.tr("Re-download mod(s) with SteamCMD")
                                    )
                            # Update git mods if local mod with git repo, but not steamcmd
                            if not mod_metadata.get("steamcmd") and mod_metadata.get(
                                "git_repo"
                            ):
                                git_paths.append(mod_folder_path)
                                if not re_git_action:
                                    re_git_action = QAction()
                                    re_git_action.setText(
                                        self.tr("Update mod(s) with git")
                                    )
                        # No "Edit mod rules" when multiple selected
                        # Toggle warning
                        if item_idx == len(selected_items) - 1:
                            toggle_warning_action = QAction()
                            toggle_warning_action.setText(self.tr("Toggle warning(s)"))
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
                                    self.tr("Convert Steam mod(s) to local")
                                )
                            # Only enable subscription actions if user has enabled Steam client integration
                            if self.settings.instances[
                                self.settings.current_instance
                            ].steam_client_integration:
                                # Re-subscribe steam mods
                                if not re_steam_action:
                                    re_steam_action = QAction()
                                    re_steam_action.setText(
                                        self.tr("Re-subscribe mod(s) with Steam")
                                    )
                                # Unsubscribe steam mods
                                if not unsubscribe_mod_steam_action:
                                    unsubscribe_mod_steam_action = QAction()
                                    unsubscribe_mod_steam_action.setText(
                                        self.tr("Unsubscribe mod(s) with Steam")
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
                tags_menu = QMenu(title=self.tr("Tags"))
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
                misc_options_menu = QMenu(title=self.tr("Miscellaneous options"))
                if copy_packageid_to_clipboard_action:
                    clipboard_options_menu = QMenu(title=self.tr("Clipboard options"))
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
                workshop_actions_menu = QMenu(title=self.tr("Workshop mods options"))
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
                add_divider_action.setText(self.tr("Add divider here"))
                context_menu.addAction(add_divider_action)
            # Execute QMenu and return it's ACTION
            action = context_menu.exec_(self.mapToGlobal(pos_local))
            if action:  # Handle the action for all selected items
                if action == add_divider_action:
                    row = self.row(item)
                    name, ok = QInputDialog.getText(
                        self,
                        self.tr("Add Divider"),
                        self.tr("Divider name:"),
                    )
                    if ok and name.strip():
                        self.add_divider(row, name.strip())
                    return True
                if (  # ACTION: Update git mod(s)
                    action == re_git_action and len(git_paths) > 0
                ):
                    # Prompt user
                    answer = show_dialogue_conditional(
                        title=self.tr("Are you sure?"),
                        text=self.tr(
                            "You have selected {len} git mods to be updated."
                        ).format(len=len(git_paths)),
                        information=self.tr("Do you want to proceed?"),
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
                        title=self.tr("Are you sure?"),
                        text=self.tr(
                            "You have selected {len} mods for deletion + re-download."
                        ).format(len=len(steamcmd_publishedfileid_to_redownload)),
                        information=self.tr(
                            "<br>This operation will recursively delete all mod files, except for .dds textures found, "
                            + "and attempt to re-download the mods via SteamCMD. Do you want to proceed?"
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
                        title=self.tr("Are you sure?"),
                        text=self.tr(
                            "You have selected {len} mods for resubscribe:(unsubscribe + subscribe)."
                        ).format(len=len(publishedfileids)),
                        information=self.tr(
                            "<br>This operation will potentially delete .dds textures leftover. Steam is unreliable for this. Do you want to proceed?"
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
                        title=self.tr("Are you sure?"),
                        text=self.tr(
                            "You have selected {len} mods for unsubscribe."
                        ).format(len=len(publishedfileids)),
                        information=self.tr("<br>Do you want to proceed?"),
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
                            parent=self,
                        )
                        return False

                    _bl_entry = _sdb_add.database.get(steamdb_add_blacklist)
                    _bl_name = (
                        _bl_entry.steamName if _bl_entry else steamdb_add_blacklist
                    )
                    args, ok = QInputDialog.getText(
                        self,
                        self.tr("Add comment"),
                        self.tr(
                            "Enter a comment providing your reasoning for wanting to blacklist this mod: "
                        )
                        + f"{_bl_name}",
                    )
                    if ok:
                        self.steamdb_blacklist_signal.emit(
                            [steamdb_add_blacklist, True, args]
                        )
                    else:
                        show_warning(
                            title=self.tr("Unable to add to blacklist"),
                            text=self.tr(
                                "Comment was not provided or entry was cancelled. Comments are REQUIRED for this action!"
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
                            parent=self,
                        )
                        return False

                    _rm_entry = _sdb_rm.database.get(steamdb_remove_blacklist)
                    _rm_name = (
                        _rm_entry.steamName if _rm_entry else steamdb_remove_blacklist
                    )
                    answer = show_dialogue_conditional(
                        title=self.tr("Are you sure?"),
                        text=self.tr("This will remove the selected mod, ")
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
                            self.tr("Replace tags")
                            if action == replace_mod_tags_action
                            else self.tr("Add tags")
                        ),
                        existing_selected_tags=existing_selected_tags,
                        parent=self,
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
        return super().eventFilter(object, event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """
        Slot to handle unhighlighting any items in the
        previous list when clicking out of that list.
        """
        self.clearFocus()
        return super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        This event occurs when the user presses a key while the mod
        list is in focus.
        """
        if event.key() == Qt.Key.Key_Delete:
            if len(self.selectedItems()) > 0:
                # Let deletion menu handle options and actual removal of mods
                menu = QMenu(self)
                for action in self.deletion_sub_menu.actions():
                    menu.addAction(action)
                self.deletion_sub_menu._refresh_actions()
                menu.exec_(QCursor.pos())
        elif (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Return
        ):
            self.key_press_signal.emit("Ctrl+Return")
        else:
            key_pressed = QKeySequence(event.key()).toString()
            if (
                key_pressed == "Left"
                or key_pressed == "Right"
                or key_pressed == "Return"
                or key_pressed == "Space"
            ):
                self.key_press_signal.emit(key_pressed)
            else:
                # Handle Delete key for mod deletion
                if event.key() == Qt.Key.Key_Delete:
                    # Only trigger if there are selected mods
                    if self.selectedItems():
                        self.deletion_sub_menu.delete_mod_completely()
                    return
                return super().keyPressEvent(event)

    def resizeEvent(self, e: QResizeEvent) -> None:
        """
        When the list widget is resized (as the window is resized),
        ensure that all visible items have widgets loaded.

        :param event: the resize event
        """
        self.check_widgets_visible()
        return super().resizeEvent(e)

    def SetUserCustomColors(self, color_dlg: QColorDialog) -> None:
        """
        Sets the user's custom colors in the QColorDialog from settings.json.
        """
        settings = self.settings
        colors = settings.color_picker_custom_colors
        if len(colors) != 16:
            return
        for i in range(16):
            color_dlg.setCustomColor(i, colors[i])

    def SaveUserCustomColors(self, color_dlg: QColorDialog) -> None:
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

    def append_new_item(self, uuid: str) -> None:
        if uuid not in self.metadata_controller.mods_metadata:
            logger.error(f"Attempted to append item with uuid not in metadata: {uuid}")
            return

        mod = self.metadata_controller.get_mod(uuid)
        mod_path = str(mod.mod_path) if mod and mod.mod_path else uuid
        aux_metadata_controller = AuxMetadataController.get_or_create_cached_instance(
            self.settings.aux_db_path
        )
        with aux_metadata_controller.Session() as aux_metadata_session:
            aux_metadata_controller.get_or_create(aux_metadata_session, mod_path)
            aux_metadata_controller.update(
                aux_metadata_session, mod_path, outdated=False
            )
            data = CustomListWidgetItemMetadata(
                path=uuid,
                list_type=self.list_type,
                aux_metadata_controller=aux_metadata_controller,
                aux_metadata_session=aux_metadata_session,
                settings=self.settings,
            )
            data.__dict__["show_tags"] = self.show_tags
        # Create item without a parent first so we can set data before adding to the list.
        # This ensures handle_rows_inserted (connected via QueuedConnection) sees the data
        # when it fires after addItem, and can correctly track the UUID in self.paths.
        item = CustomListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        self.addItem(item)

    def get_all_mod_list_items(self) -> list[CustomListWidgetItem]:
        """
        This gets all modlist items (excludes dividers).

        :return: List of all modlist items as CustomListWidgetItem
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                continue
            mod_list_items.append(item)
        return mod_list_items

    def get_all_loaded_mod_list_items(self) -> list[ModListItemInner]:
        """
        This gets all modlist items as ModListItemInner.
        Mods that have not been loaded or lazy loaded will not be returned.

        :return: List of all modlist items as ModListItemInner
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            if isinstance(widget, ModListItemInner):
                mod_list_items.append(widget)
        return mod_list_items

    def get_all_toggled_mod_list_items(self) -> list[CustomListWidgetItem]:
        """
        This returns all modlist items that have their warnings toggled.

        :return: List of all toggled modlist items as CustomListWidgetItem
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(item_data, "is_divider", False):
                continue
            if item_data["warning_toggled"]:
                mod_list_items.append(item)
        return mod_list_items

    def get_all_loaded_and_toggled_mod_list_items(self) -> list[ModListItemInner]:
        """
        This returns all modlist items that have their warnings toggled.
        Mods that have not been loaded or lazy loaded will not be returned.

        :return: List of all toggled modlist items as ModListItemInner
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(item_data, "is_divider", False):
                continue
            if item_data["warning_toggled"]:
                widget = self.itemWidget(item)
                if isinstance(widget, ModListItemInner):
                    mod_list_items.append(widget)
        return mod_list_items

    def check_item_visible(self, item: CustomListWidgetItem) -> bool:
        # Determines if the item is currently visible in the viewport.
        rect = self.visualItemRect(item)
        return rect.top() < self.viewport().height() and rect.bottom() > 0

    def create_widget_for_item(self, item: CustomListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            logger.debug("Attempted to create widget for item with None data")
            return

        if getattr(data, "is_divider", False):
            divider_widget = DividerItemInner(
                uuid=data.uuid, name=data.name, collapsed=data.collapsed
            )
            divider_widget.toggle_signal.connect(self.toggle_divider_collapse)
            item.setSizeHint(divider_widget.sizeHint())
            self.setItemWidget(item, divider_widget)
            self._update_single_divider_mod_count(item)
            return

        errors_warnings = data["errors_warnings"]
        errors = data["errors"]
        warnings = data["warnings"]
        filtered = data["filtered"]
        invalid = data["invalid"]
        mismatch = data["mismatch"]
        alternative = data["alternative"]
        uuid = data["path"]
        mod_color = data["mod_color"]
        if uuid:
            widget = ModListItemInner(
                errors_warnings=errors_warnings,
                errors=errors,
                warnings=warnings,
                filtered=filtered,
                invalid=invalid,
                mismatch=mismatch,
                alternative=alternative,
                settings=self.settings,
                path=uuid,
                mod_color=mod_color,
                metadata_controller=self.metadata_controller,
            )
            widget.toggle_warning_signal.connect(self.toggle_warning)
            widget.toggle_error_signal.connect(self.toggle_warning)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

            # Apply translation status if enabled
            if self.show_translation_status:
                _mod_tr = self.metadata_controller.get_mod(uuid)
                pkg_id = (
                    str(_mod_tr.package_id) if isinstance(_mod_tr, AboutXmlMod) else ""
                )
                has_translation = pkg_id in self.translation_lookup
                widget.update_translation_status(has_translation)

            # Ensure initial icon states reflect current item data
            widget.repolish(item)

    def check_widgets_visible(self) -> None:
        # This function checks the visibility of each item and creates a widget if the item is visible and not already setup.
        indexes = self.get_visible_indexes()
        for idx in indexes:
            item = self.item(idx)
            # Check for visible item without a widget set
            if item and self.itemWidget(item) is None:
                self.create_widget_for_item(item)

    def get_visible_indexes(self) -> set[int]:
        """This function returns the set of indexes for items that are currently visible in the viewport."""
        indexes: set[int] = set()

        top_index = self.indexAt(self.viewport().rect().topLeft())
        if not top_index.isValid():
            return indexes

        row = top_index.row()
        model = self.model()

        while row < model.rowCount():
            idx = model.index(row, 0)
            rect = self.visualRect(idx)
            if rect.top() > self.viewport().height():
                break
            elif rect.bottom() >= 0:
                indexes.add(row)

            row += 1

        return indexes

    def handle_item_data_changed(self, item: CustomListWidgetItem) -> None:
        """
        This slot is called when an item's data changes
        """
        widget = self.itemWidget(item)
        if widget is not None and isinstance(widget, ModListItemInner):
            widget.repolish(item)

    def handle_other_list_row_added(self, uuid: str) -> None:
        """
        When a mod is moved from Inactive->Active, the uuid is removed from the Inactive list.

        When a mod is moved from Active->Inactive, the uuid is removed from the Active list.
        """
        if uuid in self.paths:
            self.paths.remove(uuid)

    def handle_rows_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        """
        This slot is called when rows are inserted.

        When mods are inserted into the mod list, either through the
        `recreate_mod_list` method above or automatically through dragging
        and dropping on the UI, this function is called. For single-item
        inserts, which happens through the above method or through dragging
        and dropping individual mods, `first` equals `last` and the below
        loop is just run once. In this loop, a custom widget is created,
        which displays the text, icons, etc, and is added to the list item.

        For dragging and dropping multiple items, the loop is run multiple
        times. Importantly, even for multiple items, the number of list items
        is set BEFORE the loop starts running, e.g. if we were dragging 3 mods
        onto a list of 100 mods, this method is called once and by the start
        of this method, `self.count()` is already 103; there are 3 "empty"
        list items that do not have widgets assigned to them.

        However, inserting the initial `n` mods with `recreate_mod_list` has
        an inefficiency: it is only able to insert one at a time. This means
        this method is called `n` times for the first `n` mods.
        One optimization here (saving about 1 second with a 200 mod list) is
        to not emit the list update signal until the number of widgets is
        equal to the number of items. If widgets < items, that means
        widgets are still being added. Only when widgets == items does it mean
        we are done with adding the initial set of mods. We can do this
        by keeping track of the number of widgets currently loaded in the list
        through a set of UUIDs which we can compare to the number of items
        directly, as this set will equate to the items in the list.

        :param parent: parent to get rows under (not used)
        :param first: index of first item inserted
        :param last: index of last item inserted
        """
        # Loop through the indexes of inserted items, load widgets if not
        # already loaded. Each item index corresponds to a UUID index.
        for idx in range(first, last + 1):
            item = self.item(idx)
            if not isinstance(item, CustomListWidgetItem):
                # Convert to CustomListWidgetItem
                item = CustomListWidgetItem(item)
                self.replaceItemAtIndex(idx, item)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data is None:
                    logger.debug(f"Attempted to insert item with None data. Idx: {idx}")
                    continue
                if getattr(data, "is_divider", False):
                    uuid = data["path"]
                    self.paths.insert(idx, uuid)
                    self.create_widget_for_item(item)
                    continue
                # Ensure the item's persisted list_type matches the destination list after insertion
                try:
                    data["list_type"] = self.list_type
                    item.setData(Qt.ItemDataRole.UserRole, data)
                except Exception:
                    pass
                uuid = data["path"]
                self.paths.insert(idx, uuid)
                self.item_added_signal.emit(uuid)
        # Update list signal if all items are loaded
        if len(self.paths) == self.count():
            # Update list with the number of items
            logger.debug(
                f"Emitting {self.list_type} list update signal after rows inserted [{self.count()}]"
            )
            self.list_update_signal.emit(str(self.count()))

    def handle_rows_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        """
        This slot is called when rows are removed.
        Emit a signal with the count of objects remaining to update
        the count label. For some reason this seems to call twice on
        dragging and dropping multiple mods.

        The condition is required because when we `do_clear` or `do_import`,
        the existing list needs to be "wiped", and this counts as `n`
        calls to this function. When this happens, `self.paths` is
        cleared and `self.count()` remains at the previous number, so we can
        just check for equality here.

        :param parent: parent to get rows under (not used)
        :param first: index of first item removed (not used)
        :param last: index of last item removed (not used)
        """
        # Update list signal if all items are loaded
        if len(self.paths) == self.count():
            # Update list with the number of items
            logger.debug(
                f"Emitting {self.list_type} list update signal after rows removed [{self.count()}]"
            )
            self.list_update_signal.emit(str(self.count()))

    def get_item_widget_at_index(self, idx: int) -> QWidget | None:
        item = self.item(idx)
        if item:
            return self.itemWidget(item)
        return None

    # ── Divider helpers ──────────────────────────────────────────────

    def _show_divider_context_menu(
        self,
        item: CustomListWidgetItem,
        data: DividerData,
        pos_local: Any,
    ) -> bool:
        menu = QMenu()
        rename_action = menu.addAction(self.tr("Rename divider"))
        toggle_action = menu.addAction(
            self.tr("Expand") if data.collapsed else self.tr("Collapse")
        )
        menu.addSeparator()
        delete_action = menu.addAction(self.tr("Delete divider"))
        action = menu.exec_(self.mapToGlobal(pos_local))
        if action == rename_action:
            new_name, ok = QInputDialog.getText(
                self,
                self.tr("Rename Divider"),
                self.tr("New name:"),
                text=data.name,
            )
            if ok and new_name.strip():
                self.rename_divider(data.uuid, new_name.strip())
        elif action == toggle_action:
            self.toggle_divider_collapse(data.uuid)
        elif action == delete_action:
            self.remove_divider(data.uuid)
        return True

    def add_divider(self, index: int, name: str) -> None:
        uuid = generate_divider_uuid()
        data = DividerData(uuid=uuid, name=name)
        item = CustomListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass
        self.insertItem(index, item)
        self.paths.insert(index, uuid)
        self.create_widget_for_item(item)
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.apply_collapse_states()
        self.list_update_signal.emit(str(self.count()))

    def remove_divider(self, uuid: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        # Expand hidden items first so they become visible
        next_div = self._find_next_divider_index(idx + 1)
        for i in range(idx + 1, next_div):
            self.item(i).setHidden(False)
        self.paths.pop(idx)
        self.takeItem(idx)
        self._update_divider_mod_counts()
        self.list_update_signal.emit(str(self.count()))

    def rename_divider(self, uuid: str, new_name: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        item = self.item(idx)
        data = item.data(Qt.ItemDataRole.UserRole)
        data.name = new_name
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_name(new_name)

    def toggle_divider_collapse(self, uuid: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        item = self.item(idx)
        data = item.data(Qt.ItemDataRole.UserRole)
        data.collapsed = not data.collapsed
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_collapsed(data.collapsed)
        next_div = self._find_next_divider_index(idx + 1)
        for i in range(idx + 1, next_div):
            self.item(i).setHidden(data.collapsed)
        self._update_single_divider_mod_count(item)

    def _find_next_divider_index(self, start: int) -> int:
        for i in range(start, self.count()):
            d = self.item(i).data(Qt.ItemDataRole.UserRole)
            if getattr(d, "is_divider", False):
                return i
        return self.count()

    def _update_single_divider_mod_count(self, item: CustomListWidgetItem) -> None:
        idx = self.row(item)
        if idx < 0:
            return
        next_div = self._find_next_divider_index(idx + 1)
        count = next_div - idx - 1
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_mod_count(count)

    def _update_divider_mod_counts(self) -> None:
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                self._update_single_divider_mod_count(item)

    def apply_collapse_states(self) -> None:
        """Hide/show items according to their preceding divider's collapsed state."""
        collapsed = False
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                collapsed = data.collapsed
                widget = self.itemWidget(item)
                if isinstance(widget, DividerItemInner):
                    widget.set_collapsed(collapsed)
            else:
                hidden_by_filter = getattr(data, "hidden_by_filter", False)
                item.setHidden(collapsed or hidden_by_filter)
        self._update_divider_mod_counts()

    def get_dividers_data(self) -> list[dict[str, Any]]:
        """Return serialisable divider info for persistence."""
        result = []
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                result.append(
                    {
                        "uuid": data.uuid,
                        "name": data.name,
                        "collapsed": data.collapsed,
                        "index": i,
                    }
                )
        return result

    def restore_dividers(self, dividers: list[dict[str, Any]]) -> None:
        """Re-insert dividers at saved positions after a list rebuild."""
        if not dividers:
            return
        # Disconnect model signals to avoid handle_rows_inserted duplicating uuids
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass
        sorted_dividers = sorted(dividers, key=lambda d: d.get("index", 0))
        for div in sorted_dividers:
            idx = min(div.get("index", 0), self.count())
            uuid = div.get("uuid", generate_divider_uuid())
            data = DividerData(
                uuid=uuid,
                name=div.get("name", ""),
                collapsed=div.get("collapsed", False),
            )
            item = CustomListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
            self.insertItem(idx, item)
            self.paths.insert(idx, uuid)
        # Reconnect model signals
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.check_widgets_visible()
        self.apply_collapse_states()

    # ── End divider helpers ──────────────────────────────────────────

    def mod_changed_to(
        self, current: CustomListWidgetItem, previous: CustomListWidgetItem
    ) -> None:
        """
        Method to handle clicking on a row or navigating between rows with
        the keyboard. Look up the mod's data by uuid
        """
        if current is not None:
            data = current.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                return
            self.mod_info_signal.emit(data["path"], current)

    def mod_clicked(self, current: CustomListWidgetItem) -> None:
        """
        Method to handle clicking on a row. Necessary because `mod_changed_to` does not
        properly handle clicking on a previous selected item after clicking on an item
        in another list. For example, clicking on item 1 in the inactive list, then on item 2
        in the active list, then back to item 1 in the inactive list-- this method makes
        it so that mod info is updated as expected.
        """
        if current is not None:
            data = current.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                return
            self.mod_info_signal.emit(data["path"], current)
            mod = self.metadata_controller.get_mod(data["path"])
            logger.debug(
                f"USER ACTION: mod was clicked: [{data['path']}] {mod.name if mod else 'unknown'}"
            )

    def mod_double_clicked(self, item: CustomListWidgetItem) -> None:
        """
        Method to handle double clicking on a row.
        """
        data = item.data(Qt.ItemDataRole.UserRole)
        if getattr(data, "is_divider", False):
            self.toggle_divider_collapse(data.uuid)
            return
        self.key_press_signal.emit("DoubleClick")

    def rebuild_item_widget_from_uuid(self, uuid: str) -> None:
        if is_divider_uuid(uuid):
            return
        item_index = self.paths.index(uuid)
        item = self.item(item_index)
        logger.debug(f"Rebuilding widget for item {uuid} at index {item_index}")
        # Destroy the item's previous widget immediately. Recreate if the item is visible.
        widget = self.itemWidget(item)
        if widget:
            self.removeItemWidget(item)
        # If it is visible, create a new widget. Otherwise, allow lazy loading to handle this.
        if self.check_item_visible(item):
            self.create_widget_for_item(item)
        # If the current item is selected, update the info panel
        if self.currentItem() == item:
            self.mod_info_signal.emit(uuid, item)

    def _check_missing_dependencies(
        self, mod_data: ListedMod, package_ids_set: set[str]
    ) -> tuple[set[str], set[str]]:
        """Check for missing dependencies and alternative dependencies."""
        missing_deps: set[str] = set()
        alternative_deps: set[str] = set()
        if not isinstance(mod_data, AboutXmlMod):
            return missing_deps, alternative_deps
        consider_alternatives = self.metadata_controller.settings.use_alternative_package_ids_as_satisfying_dependencies
        for dep_id, dep_mod in mod_data.overall_rules.dependencies.items():
            alt_ids: set[str] = {str(a) for a in dep_mod.alternative_package_ids}

            satisfied = str(dep_id) in package_ids_set
            if not satisfied and consider_alternatives:
                satisfied = any(alt in package_ids_set for alt in alt_ids)
            if not satisfied and self._has_replacement(
                str(mod_data.package_id), str(dep_id), package_ids_set
            ):
                satisfied = True

            if not satisfied:
                missing_deps.add(str(dep_id))
                if consider_alternatives:
                    alt_candidates = {a for a in alt_ids if a not in package_ids_set}
                    alternative_deps.update(
                        alt_candidates if alt_candidates else alt_ids
                    )
        return missing_deps, alternative_deps

    def _check_incompatibilities(
        self, mod_data: ListedMod, package_ids_set: set[str]
    ) -> tuple[set[str], set[str]]:
        """Check for conflicting incompatibilities.

        :return: (declared, reverse_only) — declared are incompatibilities this
            mod declared itself; reverse_only are ones only declared by the
            other mod.
        """
        if not isinstance(mod_data, AboutXmlMod):
            return set(), set()
        # overall_rules.incompatible_with is the merged set from all rule sources
        all_incomp = {
            str(incomp)
            for incomp in mod_data.overall_rules.incompatible_with
            if str(incomp) in package_ids_set
        }
        # about_rules.incompatible_with is what the mod itself declared
        own_declared = {
            str(incomp)
            for incomp in mod_data.about_rules.incompatible_with
            if str(incomp) in package_ids_set
        }
        declared = all_incomp & own_declared
        reverse_only = all_incomp - own_declared
        return declared, reverse_only

    def _check_load_order_violations(
        self,
        mod_data: ListedMod,
        packageid_to_path: dict[str, str],
        current_mod_index: int,
    ) -> tuple[set[str], set[str]]:
        """Check for load order violations."""
        load_before_violations: set[str] = set()
        load_after_violations: set[str] = set()
        if not isinstance(mod_data, AboutXmlMod):
            return load_before_violations, load_after_violations
        # load_before: this mod should load BEFORE the listed mods
        # violation: this mod's index >= the other mod's index
        for pid in mod_data.overall_rules.load_before:
            pid_str = str(pid)
            if pid_str in packageid_to_path:
                other_path = packageid_to_path[pid_str]
                if other_path in self.paths and current_mod_index >= self.paths.index(
                    other_path
                ):
                    load_before_violations.add(pid_str)
        # load_after: this mod should load AFTER the listed mods
        # violation: this mod's index <= the other mod's index
        for pid in mod_data.overall_rules.load_after:
            pid_str = str(pid)
            if pid_str in packageid_to_path:
                other_path = packageid_to_path[pid_str]
                if other_path in self.paths and current_mod_index <= self.paths.index(
                    other_path
                ):
                    load_after_violations.add(pid_str)
        return load_before_violations, load_after_violations

    def _check_version_mismatch(self, uuid: str) -> bool:
        """Check if mod has version mismatch."""
        return self.metadata_controller.is_version_mismatch(uuid)

    def _check_use_this_instead(self, current_item_data: dict[str, Any]) -> bool:
        """Check if use_this_instead is applicable."""
        return bool(current_item_data["alternative"])

    def recalculate_internal_errors_warnings(self) -> tuple[str, str, int, int]:
        """
        Whenever the respective mod list has items added to it, or has
        items removed from it, or has items rearranged around within it,
        calculate the internal list errors / warnings for the mod list
        """
        logger.info(f"Recalculating {self.list_type} list errors / warnings")

        all_mods_metadata = self.metadata_controller.mods_metadata

        mod_uuids = [u for u in self.paths if not is_divider_uuid(u)]
        packageid_to_uuid: dict[str, str] = {}
        for uuid in mod_uuids:
            mod = all_mods_metadata.get(uuid)
            if isinstance(mod, AboutXmlMod):
                packageid_to_uuid[str(mod.package_id)] = uuid
        package_ids_set = set(packageid_to_uuid.keys())

        package_id_to_errors: dict[str, dict[str, None | set[str] | bool]] = {
            uuid: {
                "missing_dependencies": set() if self.list_type == "Active" else None,
                "alternative_dependencies": set()
                if self.list_type == "Active"
                else None,
                "conflicting_incompatibilities": (
                    set() if self.list_type == "Active" else None
                ),
                "reverse_incompatibilities": (
                    set() if self.list_type == "Active" else None
                ),
                "load_before_violations": set() if self.list_type == "Active" else None,
                "load_after_violations": set() if self.list_type == "Active" else None,
                "version_mismatch": True,
                "use_this_instead": set()
                if self.settings.external_use_this_instead_metadata_source != "None"
                else None,
            }
            for uuid in mod_uuids
        }

        num_warnings = 0
        total_warning_text = ""
        num_errors = 0
        total_error_text = ""

        # Load latest save package ids once for this run, only if feature enabled
        save_compare_enabled: bool = self.settings.show_save_comparison_indicators
        if save_compare_enabled:
            latest_save_ids = self._get_latest_save_package_ids()
        else:
            latest_save_ids = None

        for uuid, mod_errors in package_id_to_errors.items():
            current_mod_index = self.paths.index(uuid)
            current_item = self.item(current_mod_index)
            if current_item is None:
                continue
            current_item_data = current_item.data(Qt.ItemDataRole.UserRole)
            if getattr(current_item_data, "is_divider", False):
                continue
            current_item_data["mismatch"] = False
            current_item_data["errors"] = ""
            current_item_data["warnings"] = ""
            # Mark active as new if not present in latest save; mark inactive as in_save if present in save
            if save_compare_enabled:
                try:
                    mod_obj = all_mods_metadata.get(uuid)
                    pkg_id = (
                        str(mod_obj.package_id)
                        if isinstance(mod_obj, AboutXmlMod)
                        else ""
                    )
                    is_in_save = (
                        pkg_id in latest_save_ids
                        if latest_save_ids is not None and pkg_id
                        else False
                    )
                    if self.list_type == "Active":
                        current_item_data.__dict__["is_new"] = not is_in_save
                        current_item_data.__dict__["in_save"] = False
                    else:
                        current_item_data.__dict__["is_new"] = False
                        current_item_data.__dict__["in_save"] = is_in_save
                except Exception:
                    current_item_data.__dict__["is_new"] = False
                    current_item_data.__dict__["in_save"] = False
            else:
                current_item_data.__dict__["is_new"] = False
                current_item_data.__dict__["in_save"] = False
            mod_data = all_mods_metadata.get(uuid)
            if mod_data is None:
                continue
            pkg_id_str = (
                str(mod_data.package_id) if isinstance(mod_data, AboutXmlMod) else ""
            )
            # Check mod supportedversions against currently loaded version of game
            mod_errors["version_mismatch"] = self._check_version_mismatch(uuid)
            # Set an item's validity dynamically based on the version mismatch value
            if (
                pkg_id_str not in self.ignore_warning_list
                and not current_item_data["warning_toggled"]
            ):
                current_item_data["mismatch"] = mod_errors["version_mismatch"]
            else:
                # If a mod has been moved for eg. inactive -> active. We keep ignoring the warnings.
                # This makes sure to add the mod to the ignore list of the new modlist.
                # TODO: Check if toggle_warning method can add a mod to the ignore list
                # of both ModListWidgets (Active and Inactive) at the same time. Then we can remove some of this confusing code...
                if not current_item_data["warning_toggled"]:
                    if pkg_id_str in self.ignore_warning_list:
                        self.ignore_warning_list.remove(pkg_id_str)
                elif pkg_id_str not in self.ignore_warning_list:
                    self.ignore_warning_list.append(pkg_id_str)
            # Check for "Active" mod list specific errors and warnings
            if (
                self.list_type == "Active"
                and pkg_id_str
                and pkg_id_str not in self.ignore_warning_list
            ):
                # Use helper functions
                (
                    mod_errors["missing_dependencies"],
                    mod_errors["alternative_dependencies"],
                ) = self._check_missing_dependencies(mod_data, package_ids_set)
                (
                    mod_errors["conflicting_incompatibilities"],
                    mod_errors["reverse_incompatibilities"],
                ) = self._check_incompatibilities(mod_data, package_ids_set)
                (
                    mod_errors["load_before_violations"],
                    mod_errors["load_after_violations"],
                ) = self._check_load_order_violations(
                    mod_data, packageid_to_uuid, current_mod_index
                )
            # Calculate any needed string for errors
            tool_tip_text = ""
            # Build tooltip sections, conditionally include alternatives
            tooltip_sections = [
                ("missing_dependencies", self.tr("\nMissing Dependencies:")),
                ("conflicting_incompatibilities", self.tr("\nIncompatibilities:")),
                (
                    "reverse_incompatibilities",
                    self.tr("\nIncompatible (per other mod's rules):"),
                ),
            ]
            if self.metadata_controller.settings.use_alternative_package_ids_as_satisfying_dependencies:
                tooltip_sections.insert(
                    1,
                    (
                        "alternative_dependencies",
                        self.tr("\nAlternative Dependencies:"),
                    ),
                )

            for error_type, tooltip_header in tooltip_sections:
                if mod_errors[error_type]:
                    tool_tip_text += tooltip_header
                    errors = mod_errors[error_type]
                    assert isinstance(errors, set)
                    for key in errors:
                        # Try to resolve name from local metadata first, then steamdb
                        resolved_path = packageid_to_uuid.get(key, "")
                        resolved_mod = (
                            all_mods_metadata.get(resolved_path)
                            if resolved_path
                            else None
                        )
                        name = (
                            resolved_mod.name
                            if resolved_mod
                            else self.metadata_controller.steamdb_packageid_to_name.get(
                                key, key
                            )
                        )
                        tool_tip_text += f"\n  * {name}"
            # If missing dependency and/or incompatibility, add tooltip to errors
            current_item_data["errors"] = tool_tip_text
            # Calculate any needed string for warnings
            for error_type, tooltip_header in [
                ("load_before_violations", self.tr("\nShould be Loaded After:")),
                ("load_after_violations", self.tr("\nShould be Loaded Before:")),
            ]:
                if mod_errors[error_type]:
                    tool_tip_text += tooltip_header
                    errors = mod_errors[error_type]
                    assert isinstance(errors, set)
                    for key in errors:
                        resolved_path = packageid_to_uuid.get(key, "")
                        resolved_mod = (
                            all_mods_metadata.get(resolved_path)
                            if resolved_path
                            else None
                        )
                        name = (
                            resolved_mod.name
                            if resolved_mod
                            else self.metadata_controller.steamdb_packageid_to_name.get(
                                key, key
                            )
                        )
                        tool_tip_text += f"\n  * {name}"
            # Handle version mismatch behavior
            if (
                mod_errors["version_mismatch"]
                and pkg_id_str not in self.ignore_warning_list
            ):
                # Add tool tip to indicate mod and game version mismatch
                tool_tip_text += self.tr("\nMod and Game Version Mismatch")
            # Handle "use this instead" behavior
            if (
                self._check_use_this_instead(current_item_data)
                and pkg_id_str not in self.ignore_warning_list
            ):
                mod_errors["use_this_instead"] = True
                tool_tip_text += self.tr(
                    "\nAn alternative updated mod is recommended:\n{alternative}"
                ).format(alternative=current_item_data["alternative"])
            # Add to error summary if any missing dependencies or incompatibilities
            if self.list_type == "Active" and any(
                [
                    mod_errors[key]
                    for key in [
                        "missing_dependencies",
                        "conflicting_incompatibilities",
                        "reverse_incompatibilities",
                    ]
                ]
            ):
                num_errors += 1
                total_error_text += f"\n\n{mod_data.name}"
                total_error_text += "\n" + "=" * len(mod_data.name)
                total_error_text += tool_tip_text

            # Add to warning summary if any loadBefore or loadAfter violations, or version mismatch
            # Version mismatch is determined earlier without checking if the mod is in ignore_warning_list
            # so we have to check it again here in order to not display a faulty, empty version warning
            if (
                self.list_type == "Active"
                and pkg_id_str not in self.ignore_warning_list
                and any(
                    [
                        mod_errors[key]
                        for key in [
                            "load_before_violations",
                            "load_after_violations",
                            "version_mismatch",
                            "use_this_instead",
                        ]
                    ]
                )
            ):
                num_warnings += 1
                total_warning_text += f"\n\n{mod_data.name}"
                total_warning_text += "\n============================="
                total_warning_text += tool_tip_text
            # Add tooltip to item data and set the data back to the item
            current_item_data["errors_warnings"] = tool_tip_text.strip()
            current_item_data["warnings"] = tool_tip_text[
                len(current_item_data["errors"]) :
            ].strip()
            current_item_data["errors"] = current_item_data["errors"].strip()
            current_item.setData(Qt.ItemDataRole.UserRole, current_item_data)
        logger.info(f"Finished recalculating {self.list_type} list errors and warnings")
        return total_error_text, total_warning_text, num_errors, num_warnings

    def _get_latest_save_package_ids(self) -> set[str] | None:
        """Attempt to find the latest RimWorld save file in the configured instance and extract modIds.

        Returns a set of packageIds in the save, or None on failure. Cached per list instance.
        """
        # Respect setting: fully disable feature to avoid performance impact
        if not self.settings.show_save_comparison_indicators:
            return None
        if self._latest_save_package_ids is not None:
            return self._latest_save_package_ids

        try:
            # Config path typically points to the RimWorld config folder; Saves is sibling folder
            cfg_path = self.settings.instances[
                self.settings.current_instance
            ].config_folder
            if not cfg_path:
                return None
            saves_dir = Path(cfg_path).parent / "Saves"
            if not saves_dir.exists():
                # Try common default path
                pd = PlatformDirs(appname="RimWorld by Ludeon Studios", appauthor=False)
                candidate = Path(pd.user_data_dir).parent / "Saves"
                saves_dir = candidate if candidate.exists() else saves_dir

            if not saves_dir.exists():
                return None

            # Find latest .rws by modified time
            latest: Path | None = None
            latest_mtime = -1.0
            for p in saves_dir.glob("*.rws"):
                m = p.stat().st_mtime
                if m > latest_mtime:
                    latest_mtime = m
                    latest = p
            if latest is None:
                return None

            if fast_rimworld_xml_save_validation(str(latest)):
                ids_set = extract_xml_package_ids(str(latest))
            else:
                ids_set = set("Ludeon.RimWorld")
            # Normalize to lowercase
            self._latest_save_package_ids = {str(i).lower() for i in ids_set}
            return self._latest_save_package_ids
        except Exception:
            return None

    def _has_replacement(
        self, package_id: str, dep: str, package_ids_set: set[str]
    ) -> bool:
        # Get a list of mods that can replace this mod
        replacements = KNOWN_MOD_REPLACEMENTS.get(dep, set())
        # Return true if any of the above mods (replacements) are in the mod list
        # If no replacements exist for dep, returns false
        for replacement in replacements:
            if replacement in package_ids_set:
                logger.debug(
                    f"Missing dependency [{dep}] for [{package_id}] replaced with [{replacement}]"
                )
                return True
        return False

    def recreate_mod_list_and_sort(
        self,
        list_type: str,
        uuids: list[str],
        key: ModsPanelSortKey,
        descending: bool = False,
    ) -> None:
        """
        Reconstructs and sorts a mod list based on provided UUIDs and a sorting key.

        This method takes a list of mod UUIDs, sorts them according to the specified
        sorting key, and then recreates the mod list of the given type with the sorted order.

        Args:
            list_type (str): The type of mod list to recreate. ("Active", "Inactive")
            uuids (List[str]): The list of UUIDs representing the mods.
            key (ModsPanelSortKey): An enumeration value that determines the
                                     sorting criterion for the mods.
            descending (bool, optional): Whether to sort in descending order. Defaults to False.

        Returns:
            None
        """
        sorted_uuids = sort_paths(
            uuids,
            key=key,
            descending=descending,
            settings=self.settings,
        )
        self.recreate_mod_list(list_type, sorted_uuids, filtering=True)

    def recreate_mod_list(
        self, list_type: str, uuids: list[str], filtering: bool = False
    ) -> None:
        """
        Clear all mod items and add new ones from a dict.

        :param mods: dict of mod data
        :param filtering: if True, UUIDs are already sorted; skip sorting
        """
        logger.info(f"Internally recreating {list_type} mod list")
        # Skip sorting if UUIDs are already filtered/sorted (filtering=True)
        if not filtering:
            # Sort inactive mods using saved settings if enabled
            if list_type == "Inactive" and self.settings.save_inactive_mods_sort_state:
                sort_key = ModsPanelSortKey[self.settings.inactive_mods_sort_key]
                descending = self.settings.inactive_mods_sort_descending
                uuids = sort_paths(
                    uuids,
                    key=sort_key,
                    descending=descending,
                    settings=self.settings,
                )
            else:
                if list_type == "Inactive":
                    uuids = sort_paths(
                        uuids,
                        key=ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME,
                        descending=True,
                        settings=self.settings,
                    )
        # Disable updates and disconnect model signals during rebuild
        self.setUpdatesEnabled(False)
        # Temporarily disconnect model signals to avoid cascading updates and duplicate items
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass  # Signal not connected
        try:
            self.model().rowsAboutToBeRemoved.disconnect(self.handle_rows_removed)
        except TypeError:
            pass  # Signal not connected

        self.clear()
        self.paths = list()
        if uuids:  # Insert data...
            # Filter out dividers up-front so we can bulk-fetch real UUIDs
            real_uuids = [u for u in uuids if not is_divider_uuid(u)]

            aux_metadata_controller = (
                AuxMetadataController.get_or_create_cached_instance(
                    self.settings.aux_db_path
                )
            )
            # Single session + single aux query + single metadata pass
            with aux_metadata_controller.Session() as aux_metadata_session:
                aux_entries = aux_metadata_controller.get_all_by_paths(
                    aux_metadata_session, real_uuids
                )
                pre_fetched = bulk_prefetch_item_metadata(
                    self.metadata_controller, aux_entries, real_uuids
                )
                for uuid_key in real_uuids:
                    _mod = self.metadata_controller.get_mod(uuid_key)
                    mod_path = (
                        str(_mod.mod_path) if _mod and _mod.mod_path else uuid_key
                    )
                    aux_metadata_controller.get_or_create(
                        aux_metadata_session, mod_path
                    )
                    aux_metadata_controller.update(
                        aux_metadata_session, mod_path, outdated=False
                    )
                    item_data = CustomListWidgetItemMetadata(
                        path=uuid_key,
                        list_type=self.list_type,
                        settings=self.settings,
                        **pre_fetched[uuid_key],
                    )
                    item_data.__dict__["show_tags"] = self.show_tags
                    list_item = CustomListWidgetItem(self)
                    list_item.setData(Qt.ItemDataRole.UserRole, item_data)
                    self.addItem(list_item)
            # Set uuids list to match the widget after all items are added
            self.paths = list(uuids)

        else:  # ...unless we don't have mods, at which point reenable updates and exit
            self.setUpdatesEnabled(True)
            # Reconnect model signals
            self.model().rowsInserted.connect(
                self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
            )
            self.model().rowsAboutToBeRemoved.connect(
                self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
            )
            return

        # Reconnect model signals
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.model().rowsAboutToBeRemoved.connect(
            self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
        )
        # Enable updates and repaint
        self.setUpdatesEnabled(True)
        self.repaint()
        # Load visible widgets after rebuild completes
        self.check_widgets_visible()
        # Emit signal to update counts and errors/warnings
        self.list_update_signal.emit(str(self.count()))

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
        uuid_to_color: dict[str, QColor | None] = {}
        for uuid in uuids:
            current_mod_index = self.paths.index(uuid)
            item = self.item(current_mod_index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            item_data["mod_color"] = new_color
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            uuid_to_color[uuid] = new_color
        auxdb_update_all_mod_colors(self.settings, uuid_to_color)

    def reset_mod_color(self, uuid: str) -> None:
        current_mod_index = self.paths.index(uuid)
        item = self.item(current_mod_index)
        item_data = item.data(Qt.ItemDataRole.UserRole)
        item_data["mod_color"] = None
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        auxdb_update_mod_color(self.settings, uuid, None)

    def reset_all_mod_colors(self, uuids: list[str]) -> None:
        uuid_to_color: dict[str, QColor | None] = {}
        for uuid in uuids:
            current_mod_index = self.paths.index(uuid)
            item = self.item(current_mod_index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            item_data["mod_color"] = None
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            uuid_to_color[uuid] = None
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

    def replaceItemAtIndex(self, index: int, item: CustomListWidgetItem) -> None:
        """
        IMPORTANT: This is used to replace an item without triggering the rowsInserted signal and rowsAboutToBeRemoved signal.
        :param index: The index of the item to replace.
        :param item: The new item that will replace the old one.
        """
        # The rowsInserted signal should be removed from ALL slots and then reconnected to ALL slots.
        # This will have to be manually done below, unless we start tracking which slots that signal is connected to.

        # Check if the signal is connected before disconnecting
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass  # Signal was not connected
        try:
            self.model().rowsAboutToBeRemoved.disconnect(self.handle_rows_removed)
        except TypeError:
            pass  # Signal was not connected

        # Perform the replacement
        self.takeItem(index)
        self.insertItem(index, item)
        # Ensure the item's metadata reflects this list's type after replacement
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data is not None:
                data["list_type"] = self.list_type
                item.setData(Qt.ItemDataRole.UserRole, data)
        except Exception:
            pass

        # Reconnect to ALL slots
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.model().rowsAboutToBeRemoved.connect(
            self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
        )
