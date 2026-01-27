import json
import os
import sys
import time
import traceback
import webbrowser
from functools import partial
from pathlib import Path
from typing import Any, Callable, Literal, Optional, cast, overload

from loguru import logger
from PySide6.QtCore import (
    QEventLoop,
    QObject,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QSplitter,
    QWidget,
)

import app.core.constants as app_constants
import app.ui.dialogue as dialogue
from app.controllers.handlers.import_export_handler import ImportExportHandler
from app.controllers.handlers.steam_handler import SteamHandler
from app.controllers.handlers.zip_mod_handler import ZipModHandler
from app.controllers.metadata_controller import MetadataController
from app.controllers.sort_controller import Sorter
from app.controllers.todds_controller import ToddsController
from app.core.app_info import AppInfo
from app.core.dict_utils import recursively_update_dict
from app.core.event_bus import EventBus
from app.core.game_launch import launch_game_process, launch_process
from app.core.system_info import SystemInfo
from app.core.ui_helpers import (
    copy_to_clipboard_safely,
    platform_specific_open,
    upload_data_to_0x0_st,
)
from app.core.update_utils import UpdateManager
from app.io.files import create_backup_in_thread
from app.io.json_utils import atomic_json_dump
from app.io.zip_extractor import ZipExtractThread
from app.models.metadata.metadata_structure import AboutXmlMod, ModType
from app.models.settings import Settings
from app.mods.db_builder import DatabaseBuilder
from app.net import http
from app.services.import_export_service import ImportExportService
from app.services.window_manager import WindowManager
from app.sort.mod_sorting import ModsPanelSortKey
from app.ui.widgets.animations import LoadingAnimation
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.divider import is_divider_uuid
from app.utils.steam.steambrowser.browser import SteamBrowser
from app.utils.steam.steamcmd.wrapper import SteamcmdInterface
from app.views.mod_info_panel import ModInfoPanel
from app.views.mod_list_widget import ModListWidget
from app.views.mods_panel import ModsPanel
from app.views.settings_dialog import SettingsDialog
from app.views.task_progress_window import TaskProgressWindow
from app.windows.duplicate_mods_panel import DuplicateModsPanel
from app.windows.ignore_json_editor import IgnoreJsonEditor
from app.windows.missing_dependencies_dialog import MissingDependenciesDialog
from app.windows.missing_mod_properties_panel import MissingModPropertiesPanel
from app.windows.missing_mods_panel import MissingModsPrompt
from app.windows.rule_editor_panel import RuleEditor
from app.windows.runner_panel import RunnerPanel
from app.windows.use_this_instead_panel import UseThisInsteadPanel


class MainContent(QObject):
    """
    This class controls the layout and functionality of the main content
    panel of the GUI, containing the mod information display, inactive and
    active mod lists, and the action button panel. Additionally, it acts
    as the main temporary datastore of the app, caching workshop mod information
    and their dependencies.
    """

    _instance: Optional["MainContent"] = None

    disable_enable_widgets_signal = Signal(bool)
    status_signal = Signal(str)
    stop_watchdog_signal = Signal()

    def __new__(cls, *args: Any, **kwargs: Any) -> "MainContent":
        if cls._instance is None:
            cls._instance = super(MainContent, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        settings: Settings,
        metadata_controller: MetadataController,
        show_settings_dialog: Callable[..., None] | None = None,
        settings_dialog: SettingsDialog | None = None,
    ) -> None:
        if not hasattr(self, "initialized"):
            super().__init__()
            logger.debug("Initializing MainContent")
            self.settings = settings
            self._show_settings_dialog = show_settings_dialog
            self._settings_dialog = settings_dialog
            self.metadata_controller = metadata_controller
            self._init_services()
            self._init_widgets()
            self._setup_layout()
            self._connect_signals()
            self._init_state()
            logger.info("Finished MainContent initialization")
            self.initialized = True

    def _init_services(self) -> None:
        self.db_builder = DatabaseBuilder(self.settings)
        self.steam_browser: SteamBrowser | None = None
        self.steamcmd_runner: RunnerPanel | None = None
        self.steamcmd_wrapper = SteamcmdInterface.instance()
        self._import_export_service = ImportExportService(
            self.metadata_controller, self.settings
        )
        self._import_export_handler = ImportExportHandler(
            settings=self.settings, panel=self
        )
        self._steam_handler = SteamHandler(settings=self.settings, panel=self)
        self._zip_mod_handler = ZipModHandler(settings=self.settings, panel=self)
        self.query_runner: RunnerPanel | None = None
        self.steamworks_in_use = False
        self.todds_runner: RunnerPanel | None = None
        self.todds_controller: ToddsController

    def _init_widgets(self) -> None:
        self.mod_info_panel = ModInfoPanel(
            settings=self.settings,
            metadata_controller=self.metadata_controller,
        )
        self.mods_panel = ModsPanel(
            settings=self.settings,
            metadata_controller=self.metadata_controller,
        )
        self.mod_info_container = QWidget()
        self.mod_info_container.setLayout(self.mod_info_panel.panel)
        self.mods_panel_container = QWidget()
        self.mods_panel_container.setLayout(self.mods_panel.panel)

    def _setup_layout(self) -> None:
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_layout_frame = QFrame()
        self.main_layout_frame.setObjectName("MainPanel")
        self.main_layout_frame.setLayout(self.main_layout)
        self.main_splitter.addWidget(self.mod_info_container)
        self.main_splitter.addWidget(self.mods_panel_container)
        self.main_splitter.setHandleWidth(1)
        self.mod_info_container.setMinimumWidth(280)
        self.main_layout.addWidget(self.main_splitter)

    def _connect_signals(self) -> None:
        EventBus().settings_have_changed.connect(self._on_settings_have_changed)
        EventBus().do_check_for_application_update.connect(self._do_check_for_update)
        EventBus().do_open_mod_list.connect(self._do_import_list_file_xml)
        EventBus().do_import_mod_list_from_rentry.connect(self._do_import_list_rentry)
        EventBus().do_import_mod_list_from_workshop_collection.connect(
            self._do_import_list_workshop_collection
        )
        EventBus().do_import_mod_list_from_save_file.connect(
            self._do_import_list_from_save_file
        )
        EventBus().do_save_mod_list_as.connect(self._do_export_list_file_xml)
        EventBus().do_export_mod_list_to_clipboard.connect(
            self._do_export_list_clipboard
        )
        EventBus().do_export_mod_list_to_rentry.connect(self._do_upload_list_rentry)
        EventBus().do_upload_log.connect(self._upload_file)
        EventBus().do_open_default_editor.connect(self._open_in_default_editor)
        EventBus().do_download_all_mods_via_steamcmd.connect(
            self.db_builder._on_do_download_all_mods_via_steamcmd
        )
        EventBus().do_download_all_mods_via_steam.connect(
            self.db_builder._on_do_download_all_mods_via_steam
        )
        EventBus().do_compare_steam_workshop_databases.connect(
            self.db_builder._do_generate_metadata_comparison_report
        )
        EventBus().do_merge_steam_workshop_databases.connect(
            self.db_builder._do_merge_databases
        )
        EventBus().do_build_steam_workshop_database.connect(
            self.db_builder._do_build_database_thread
        )
        EventBus().do_import_acf.connect(self._do_import_steamcmd_acf_data)
        EventBus().do_export_acf.connect(self._do_export_steamcmd_acf_data)
        EventBus().do_delete_acf.connect(self._do_reset_steamcmd_acf_data)
        EventBus().do_install_steamcmd.connect(self._do_setup_steamcmd)

        EventBus().do_refresh_mods_lists.connect(self._do_refresh)
        EventBus().do_clear_active_mods_list.connect(self._do_clear)
        EventBus().do_restore_active_mods_list.connect(self._do_restore)
        EventBus().do_sort_active_mods_list.connect(self._do_sort)
        EventBus().do_save_active_mods_list.connect(self._do_save)
        EventBus().do_run_game.connect(self._do_run_game)

        EventBus().do_open_app_directory.connect(self._do_open_app_directory)
        EventBus().do_open_settings_directory.connect(self._do_open_settings_directory)
        EventBus().do_open_rimdex_logs_directory.connect(
            self._do_open_rimdex_logs_directory
        )
        EventBus().do_open_rimworld_directory.connect(self._do_open_rimworld_directory)
        EventBus().do_open_rimworld_config_directory.connect(
            self._do_open_rimworld_config_directory
        )
        EventBus().do_open_rimworld_logs_directory.connect(
            self._do_open_rimworld_logs_directory
        )
        EventBus().do_open_local_mods_directory.connect(
            self._do_open_local_mods_directory
        )
        EventBus().do_open_steam_mods_directory.connect(
            self._do_open_steam_mods_directory
        )

        EventBus().do_steamcmd_download.connect(self._do_download_mods_with_steamcmd)

        EventBus().do_steamworks_api_call.connect(self._do_steamworks_api_call_animated)

        EventBus().do_rule_editor.connect(
            lambda: self._do_open_rule_editor(
                compact=False, initial_mode="community_rules"
            )
        )
        EventBus().do_ignore_json_editor.connect(self._do_open_ignore_json_editor)
        EventBus().do_check_missing_mod_properties.connect(
            self.__check_and_warn_missing_mod_properties
        )

        EventBus().do_add_zip_mod.connect(self._do_add_zip_mod)
        EventBus().do_browse_workshop.connect(self._do_browse_workshop)
        EventBus().do_check_for_workshop_updates.connect(
            self._do_check_for_workshop_updates
        )
        EventBus().do_steam_verify_game_files.connect(self.do_steam_verify_game_files)

        EventBus().do_optimize_textures.connect(self._do_optimize_textures)
        EventBus().do_delete_dds_textures.connect(self._do_delete_dds_textures)

        self.metadata_controller.mod_created_signal.connect(
            self.mods_panel.on_mod_created
        )
        self.metadata_controller.mod_deleted_signal.connect(
            self.mods_panel.on_mod_deleted
        )
        self.metadata_controller.mod_metadata_updated_signal.connect(
            self.mods_panel.on_mod_metadata_updated
        )
        self.metadata_controller.metadata_refreshed.connect(self._on_metadata_refreshed)
        self.mods_panel.active_mods_list.key_press_signal.connect(
            self.__handle_active_mod_key_press
        )
        self.mods_panel.inactive_mods_list.key_press_signal.connect(
            self.__handle_inactive_mod_key_press
        )
        self.mods_panel.active_mods_list.mod_info_signal.connect(self.__mod_list_slot)
        self.mods_panel.inactive_mods_list.mod_info_signal.connect(self.__mod_list_slot)
        self.mods_panel.active_mods_list.item_added_signal.connect(
            self.mods_panel.inactive_mods_list.handle_other_list_row_added
        )
        self.mods_panel.inactive_mods_list.item_added_signal.connect(
            self.mods_panel.active_mods_list.handle_other_list_row_added
        )
        self.mods_panel.active_mods_list.edit_rules_signal.connect(
            self._do_open_rule_editor
        )
        self.mods_panel.inactive_mods_list.edit_rules_signal.connect(
            self._do_open_rule_editor
        )
        self.mods_panel.active_mods_list.steamdb_blacklist_signal.connect(
            self._do_blacklist_action_steamdb
        )
        self.mods_panel.inactive_mods_list.steamdb_blacklist_signal.connect(
            self._do_blacklist_action_steamdb
        )
        self.mods_panel.active_mods_list.refresh_signal.connect(self._do_refresh)
        self.mods_panel.inactive_mods_list.refresh_signal.connect(self._do_refresh)

        EventBus().use_this_instead_clicked.connect(self._use_this_instead_clicked)
        EventBus().do_threaded_loading_animation.connect(
            self.do_threaded_loading_animation
        )
        EventBus().do_metadata_refresh_cache.connect(self.do_metadata_refresh_cache)

    def _init_state(self) -> None:
        self.active_mods_uuids_last_save: list[str] = []
        self.active_mods_dividers_last_save: list[dict[str, Any]] = []
        self.active_mods_uuids_restore_state: list[str] = []
        self.inactive_mods_uuids_restore_state: list[str] = []
        self.duplicate_mods: dict[str, Any] = {}
        self._extract_progress_widget: Optional[TaskProgressWindow] = None
        self._extract_thread: ZipExtractThread | None = None
        self.window_manager = WindowManager()
        self._active_loading_loop: QEventLoop | None = None
        self._refresh_in_progress: bool = False

    @classmethod
    def instance(cls, *args: Any, **kwargs: Any) -> "MainContent":
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        elif args or kwargs:
            raise ValueError("MainContent instance has already been initialized.")
        return cls._instance

    @Slot()
    def _on_metadata_refreshed(self) -> None:
        """Handle metadata refreshes triggered outside the main refresh flow.

        When ``_refresh_in_progress`` is True, the main ``_do_refresh`` flow is
        already handling repopulation explicitly (so this is a no-op).
        When False — e.g. from ``do_metadata_refresh_cache`` — we repopulate
        the mod lists here so the UI reflects the updated metadata.
        """
        if self._refresh_in_progress:
            return
        self.__repopulate_lists()
        self.mods_panel.refresh_all_tag_filter_selectors()

    def abort_loading(self) -> None:
        """Abort any in-progress loading animation by quitting its nested event loop.

        Called from MainWindow.closeEvent to unblock the startup scanning so
        the process can exit cleanly.
        """
        if self._active_loading_loop is not None:
            self._active_loading_loop.quit()

    def close_child_windows(self) -> None:
        """Close all tracked child windows.

        Called when the main window is closing to ensure no orphan
        windows remain on screen.
        """
        self.window_manager.close_all()

    def do_metadata_refresh_cache(self) -> None:
        """Force Refresh metadata cache"""
        self.metadata_controller.refresh_metadata()

    def check_if_essential_paths_are_set(self, prompt: bool = True) -> bool:
        """
        When the user starts the app for the first time, none
        of the paths will be set. We should check for this and
        not throw a fatal error trying to load mods until the
        user has had a chance to set paths.
        """
        current_instance = self.settings.current_instance
        game_folder_path = self.settings.instances[current_instance].game_folder
        config_folder_path = self.settings.instances[current_instance].config_folder
        local_mods_folder_path = self.settings.instances[current_instance].local_folder
        logger.info(f"Game folder: {game_folder_path}")
        logger.info(f"Config folder: {config_folder_path}")
        logger.info(f"Local mods folder: {local_mods_folder_path}")
        if (
            game_folder_path
            and config_folder_path
            and local_mods_folder_path
            and os.path.exists(game_folder_path)
            and os.path.exists(config_folder_path)
            and os.path.exists(local_mods_folder_path)
        ):
            logger.info("Essential paths set!")
            return True
        else:
            logger.warning("Essential path(s) are invalid or not set!")
            answer = dialogue.show_dialogue_conditional(
                title=self.tr("Essential path(s)"),
                text=self.tr("Essential path(s) are invalid or not set!"),
                information=(
                    self.tr(
                        "RimDex requires the below paths to be set.<br/><br/>"
                        "1) Game folder (Folder where RimWorld is installed).<br/><br/>"
                        "2) Config folder (Folder where ModsConfig.xml is located)<br/><br/>"
                        "3) Local mods folder (Mods folder inside the RimWorld installation).<br/><br/>"
                        "4) Steam mods folder (Only set if you use Steam user also enable Steam Client Integration)<br/><br/>"
                        "Try Using the autodetect functionality to set all paths automatically.<br/><br/>"
                        "Would you like to open the settings to configure them now?"
                    )
                ),
            )
            if (
                answer == QMessageBox.StandardButton.Yes
                and self._show_settings_dialog is not None
            ):
                self._show_settings_dialog("Locations")
            return False

    def ___get_relative_middle(self, some_list: ModListWidget) -> int:
        rect = some_list.contentsRect()
        top = some_list.indexAt(rect.topLeft())
        if top.isValid():
            bottom = some_list.indexAt(rect.bottomLeft())
            if not bottom.isValid():
                bottom = some_list.model().index(some_list.count() - 1, 0)
            return int((top.row() + bottom.row() + 1) / 2)
        return 0

    def __handle_active_mod_key_press(self, key: str) -> None:
        """
        If the Left Arrow key is pressed while the user is focused on the
        Active Mods List, the focus is shifted to the Inactive Mods List.
        If no Inactive Mod was previously selected, the middle (relative)
        one is selected. `__mod_list_slot` is also called to update the
        Mod Info Panel.

        If the Return or Space button is pressed the selected mods in the
        current list are deleted from the current list and inserted
        into the other list.
        """
        aml = self.mods_panel.active_mods_list
        iml = self.mods_panel.inactive_mods_list
        if key == "Left":
            iml.setFocus()
            if not iml.selectedIndexes():
                iml.setCurrentRow(self.___get_relative_middle(iml))
            selected_items = iml.selectedItems()
            if not selected_items:
                return
            item = selected_items[0]
            data = item.data(Qt.ItemDataRole.UserRole)
            uuid = data["path"]
            self.__mod_list_slot(uuid, cast(CustomListWidgetItem, item))

        elif key == "Return" or key == "Space" or key == "DoubleClick":
            # TODO: graphical bug where if you hold down the key, items are
            # inserted too quickly and become empty items

            items_to_move = [
                i
                for i in aml.selectedItems().copy()
                if not getattr(i.data(Qt.ItemDataRole.UserRole), "is_divider", False)
            ]
            if items_to_move:
                first_selected = sorted(aml.row(i) for i in items_to_move)[0]

                # Remove items from current list
                for item in items_to_move:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    uuid = data["path"]
                    aml.paths.remove(uuid)
                    aml.takeItem(aml.row(item))
                if aml.count():
                    if aml.count() == first_selected:
                        aml.setCurrentRow(aml.count() - 1)
                    else:
                        aml.setCurrentRow(first_selected)

                # Insert items into other list
                if not iml.selectedIndexes():
                    count = self.___get_relative_middle(iml)
                else:
                    count = iml.row(iml.selectedItems()[-1]) + 1
                for item in items_to_move:
                    iml.insertItem(count, item)
                    count += 1
        # List error/warnings are automatically recalculated when a mod is inserted/removed from a list

    def __handle_inactive_mod_key_press(self, key: str) -> None:
        """
        If the Right Arrow key is pressed while the user is focused on the
        Inactive Mods List, the focus is shifted to the Active Mods List.
        If no Active Mod was previously selected, the middle (relative)
        one is selected. `__mod_list_slot` is also called to update the
        Mod Info Panel.

        If the Return or Space button is pressed the selected mods in the
        current list are deleted from the current list and inserted
        into the other list.
        """

        aml = self.mods_panel.active_mods_list
        iml = self.mods_panel.inactive_mods_list
        if key == "Right":
            aml.setFocus()
            if not aml.selectedIndexes():
                aml.setCurrentRow(self.___get_relative_middle(aml))
            item = aml.selectedItems()[0]
            data = item.data(Qt.ItemDataRole.UserRole)
            uuid = data["path"]
            self.__mod_list_slot(uuid, cast(CustomListWidgetItem, item))

        elif key == "Return" or key == "Space" or key == "DoubleClick":
            # TODO: graphical bug where if you hold down the key, items are
            # inserted too quickly and become empty items

            items_to_move = iml.selectedItems().copy()
            if items_to_move:
                first_selected = sorted(iml.row(i) for i in items_to_move)[0]

                # Remove items from current list
                for item in items_to_move:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    uuid = data["path"]
                    iml.paths.remove(uuid)
                    iml.takeItem(iml.row(item))
                if iml.count():
                    if iml.count() == first_selected:
                        iml.setCurrentRow(iml.count() - 1)
                    else:
                        iml.setCurrentRow(first_selected)

                # Insert items into other list
                if not aml.selectedIndexes():
                    count = self.___get_relative_middle(aml)
                else:
                    count = aml.row(aml.selectedItems()[-1]) + 1
                for item in items_to_move:
                    aml.insertItem(count, item)
                    count += 1
        # List error/warnings are automatically recalculated when a mod is inserted/removed from a list

    def _insert_data_into_lists(
        self, active_mods_uuids: list[str], inactive_mods_uuids: list[str]
    ) -> None:
        """
        Insert active mods and inactive mods into respective mod list widgets.

        :param active_mods_uuids: list of active mod uuids
        :param inactive_mods_uuids: list of inactive mod uuids
        """
        logger.info(
            f"Inserting mod data into active [{len(active_mods_uuids)}] and inactive [{len(inactive_mods_uuids)}] mod lists"
        )
        # Snapshot live divider state before the list is cleared
        live_dividers = self.mods_panel.active_mods_list.get_dividers_data()
        if live_dividers:
            self.settings.active_mods_dividers = live_dividers
        saved_dividers = self.settings.active_mods_dividers
        self.mods_panel.active_mods_list.recreate_mod_list(
            list_type="active", uuids=active_mods_uuids
        )
        # Restore dividers into the active list
        if saved_dividers:
            self.mods_panel.active_mods_list.restore_dividers(saved_dividers)
        # Use current UI state from the combobox and button for inactive mods.
        sort_key = ModsPanelSortKey[self.mods_panel.inactive_mods_sort_key]
        descending = self.mods_panel.inactive_sort_descending
        self.mods_panel.inactive_mods_list.recreate_mod_list_and_sort(
            list_type="inactive",
            uuids=inactive_mods_uuids,
            key=sort_key,
            descending=descending,
        )
        logger.info(
            f"Finished inserting mod data into active [{len(active_mods_uuids)}] and inactive [{len(inactive_mods_uuids)}] mod lists"
        )
        # Recalculate warnings for both lists
        # self.mods_panel.active_mods_list.recalculate_warnings_signal.emit()
        # self.mods_panel.inactive_mods_list.recalculate_warnings_signal.emit()

    def _duplicate_mods_prompt(self) -> None:
        """
        Opens the DuplicateModsPanel to allow user to resolve duplicate mods.
        """
        if not self.settings.duplicate_mods_warning:
            logger.warning(
                "User preference is not configured to display duplicate mods. Skipping..."
            )
            return
        elif (
            self.settings.duplicate_mods_warning
            and self.duplicate_mods
            and len(self.duplicate_mods) > 0
        ):
            duplicate_mods_count = len(self.duplicate_mods)
            logger.info(
                f"Found {duplicate_mods_count} duplicate mods. Opening DuplicateModsPanel..."
            )
            duplicate_mods_panel = DuplicateModsPanel(
                self.duplicate_mods, metadata_controller=self.metadata_controller
            )
            self.window_manager.register(duplicate_mods_panel)
            duplicate_mods_panel.setWindowModality(Qt.WindowModality.ApplicationModal)
            duplicate_mods_panel.show()
        else:
            logger.info("No duplicate mods found. Skipping...")

    def _missing_mods_prompt(self) -> None:
        """Open the MissingModsPrompt to allow user to download missing mods."""
        if not self.settings.try_download_missing_mods:
            logger.warning(
                "User preference is not configured to attempt downloading missing mods. Skipping..."
            )
            return
        elif (
            self.settings.try_download_missing_mods
            and self.missing_mods
            and len(self.missing_mods) > 0
        ):
            missing_mods_count = len(self.missing_mods)
            logger.info(
                f"Found {missing_mods_count} missing mods. Opening MissingModsPrompt..."
            )
            # Always open the MissingModsPrompt panel, allowing manual entry if Steam database is unavailable
            self.missing_mods_prompt = MissingModsPrompt(
                packageids=self.missing_mods,
                metadata_controller=self.metadata_controller,
            )
            self.window_manager.register_attr(self, "missing_mods_prompt")
            self.missing_mods_prompt._populate_from_metadata()
            self.missing_mods_prompt.setWindowModality(
                Qt.WindowModality.ApplicationModal
            )
            self.missing_mods_prompt.show()
        else:
            logger.info("No missing mods found. Skipping...")

    def __check_and_warn_missing_mod_properties(self) -> None:
        """
        Scan for mods with missing critical properties and notify the user.

        This method checks all loaded mods for two critical properties:
        1. Package ID (required for proper mod identification and dependencies)
        2. Publish Field ID (required for Workshop mods to support updates)

        If any mods are missing these properties, a dedicated panel is displayed
        allowing the user to review the affected mods and contact authors.

        The method handles all exceptions gracefully to prevent disrupting
        the main application flow.
        """
        try:
            # Identify mods with missing critical properties (single pass)
            missing_packageid_paths, missing_publishfieldid_paths = (
                self.metadata_controller.get_missing_properties_paths()
            )

            # If no mods have missing properties, log and return early
            if not missing_packageid_paths and not missing_publishfieldid_paths:
                logger.info("No mods with missing properties found. Skipping...")
                return

            # Log summary statistics for debugging
            missing_packageid_count = len(missing_packageid_paths)
            missing_publishfieldid_count = len(missing_publishfieldid_paths)

            logger.info(
                f"Found {missing_packageid_count} mod(s) with missing Package ID and "
                f"{missing_publishfieldid_count} mod(s) with missing Publish Field ID. "
                f"Opening MissingModPropertiesPanel..."
            )

            # Display a unified panel showing all mods with missing properties,
            # grouped by property type for better user comprehension
            missing_mod_properties_panel = MissingModPropertiesPanel(
                missing_packageid_mods=missing_packageid_paths,
                missing_publishfieldid_mods=missing_publishfieldid_paths,
                metadata_controller=self.metadata_controller,
            )
            self.window_manager.register(missing_mod_properties_panel)
            # Make the panel modal to ensure user acknowledges the issues
            missing_mod_properties_panel.setWindowModality(
                Qt.WindowModality.ApplicationModal
            )
            missing_mod_properties_panel.show()
        except Exception as e:
            logger.error(f"Error checking mod properties: {e}")

    def __mod_list_slot(self, uuid: str, item: CustomListWidgetItem) -> None:
        """
        This slot method is triggered when the user clicks on an item
        on a mod list.

        It takes the internal uuid and gets the
        complete json mod info for that internal uuid. It passes
        this information to the mod info panel to display.

        It also takes the selected mod (CustomListWidgetItem) and passes
        this to the mod info panel to display that mod's notes.

        :param uuid: uuid of mod
        :param item: selected CustomListWidgetItem
        """
        self.mod_info_panel.display_mod_info(uuid=uuid)
        self.mod_info_panel.show_user_mod_notes(item)

    def __repopulate_lists(self, is_initial: bool = False) -> None:
        """
        Get active and inactive mod lists based on the config path
        and write them to the list widgets. is_initial indicates if
        this function is running at app initialization. If is_initial is
        true, then write the active_mods_data and inactive_mods_data to
        restore variables.
        """
        logger.info("Repopulating mod lists")
        (
            active_mods_uuids,
            inactive_mods_uuids,
            self.duplicate_mods,
            self.missing_mods,
        ) = self.metadata_controller.get_mods_from_list(
            mod_list=str(
                (
                    Path(
                        self.settings.instances[
                            self.settings.current_instance
                        ].config_folder
                    )
                    / "ModsConfig.xml"
                )
            )
        )
        self.active_mods_uuids_last_save = active_mods_uuids
        if is_initial:
            logger.info("Caching initial active/inactive mod lists")
            self.active_mods_uuids_restore_state = active_mods_uuids
            self.inactive_mods_uuids_restore_state = inactive_mods_uuids

        self._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)

    def _do_check_for_update(self) -> None:
        """
        Check for RimDex updates using UpdateManager.
        """
        update_manager = UpdateManager(self.settings, self, self.mod_info_panel)
        update_manager.do_check_for_update()

    def __do_get_github_release_info(self) -> dict[str, Any]:
        # Parse latest release
        url = "https://api.github.com/repos/RimDex/RimDex/releases/latest"
        logger.debug(f"Requesting GitHub release info from: {url}")

        raw = http.get(url, timeout=10)

        # Check for HTTP errors
        if raw.status_code != 200:
            logger.warning(f"GitHub API returned status code {raw.status_code}")
            if raw.status_code == 403:
                logger.warning("Possible rate limiting by GitHub API")
            raise Exception(
                f"GitHub API returned status code {raw.status_code}: {raw.text}"
            )

        # Try to parse JSON response
        try:
            response_json = raw.json()
            logger.debug("Successfully parsed GitHub API response")
            return response_json
        except Exception as e:
            logger.error(f"Failed to parse GitHub API response: {e}")
            logger.debug(f"Raw response: {raw.text}")
            raise

    # INFO PANEL ANIMATIONS

    @Slot(str, object, str)
    def do_threaded_loading_animation(
        self, gif_path: str, target: Callable[..., Any], text: str | None = None
    ) -> Any:
        # Hide the info panel widgets
        self.mod_info_panel.info_panel_frame.hide()
        # Disable widgets while loading
        self.disable_enable_widgets_signal.emit(False)
        # Encapsulate mod parsing inside a nice lil animation
        loading_animation = LoadingAnimation(
            gif_path=gif_path,
            target=target,
        )
        self.mod_info_panel.panel.addWidget(loading_animation)
        # If any text message specified, pass it to the info panel as well
        loading_animation_text_label = None
        if text:
            loading_animation_text_label = QLabel(text)
            loading_animation_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_animation_text_label.setObjectName("loadingAnimationString")
            self.mod_info_panel.panel.addWidget(loading_animation_text_label)
        loop = QEventLoop()
        loading_animation.finished.connect(loop.quit)
        # Store ref so closeEvent can break out of this loop
        self._active_loading_loop = loop
        loop.exec_()
        self._active_loading_loop = None
        # If the loop was quit externally (e.g. window close), skip UI cleanup
        if not loading_animation.animation_finished:
            return None
        data = loading_animation.data
        # Remove text label if it was passed
        if text and loading_animation_text_label is not None:
            self.mod_info_panel.panel.removeWidget(loading_animation_text_label)
            loading_animation_text_label.close()
        # Enable widgets again after loading
        self.disable_enable_widgets_signal.emit(True)
        # Show the info panel widgets
        self.mod_info_panel.info_panel_frame.show()
        logger.debug(f"Returning {type(data)}")
        return data

    # ACTIONS PANEL

    def _do_refresh(self, is_initial: bool = False) -> None:
        """
        Refresh expensive calculations & repopulate lists with that refreshed data
        """
        EventBus().refresh_started.emit()
        EventBus().do_save_button_animation_stop.emit()
        # If we are refreshing cache from user action
        if not is_initial:
            # Reset the data source filters to default and clear searches
            # Avoid recalculating warnings/errors when clearing search
            # Recalculation for each list will be triggered by mods being reinserted into inactive and active lists automatically
            self.mods_panel.reset_all_filters_and_search("Active")
            self.mods_panel.reset_all_filters_and_search("Inactive")
        # Check if paths are set
        if self.check_if_essential_paths_are_set(prompt=is_initial):
            # Run expensive calculations to set cache data
            self._refresh_in_progress = True
            result = self.do_threaded_loading_animation(
                gif_path=str(
                    AppInfo().theme_data_folder / "default-icons" / "rimdex.gif"
                ),
                target=partial(
                    self.metadata_controller.refresh_metadata,
                ),
                text=self.tr("Scanning mod sources and populating metadata..."),
            )
            self._refresh_in_progress = False

            # If loading was aborted (e.g. window closed during scan), skip remaining work
            if result is None and self.metadata_controller.is_abort_requested:
                return

            # Insert mod data into list
            self.__repopulate_lists(is_initial=is_initial)
            self.mods_panel.refresh_all_tag_filter_selectors()

            # check if we have duplicate mods, prompt user
            self._duplicate_mods_prompt()

            # check if we have missing mods, prompt user
            self._missing_mods_prompt()

            # Check if we have mods with missing properties (Package ID and/or Publish Field ID)
            self.__check_and_warn_missing_mod_properties()

            # Check Workshop mods for updates if configured
            if self.settings.steam_mods_update_check:
                logger.info("Checking Workshop mods for updates...")
                self._do_check_for_workshop_updates()
            else:
                logger.info(
                    "User preference is not configured to check Workshop mod for updates. Skipping.."
                )
        else:
            self._insert_data_into_lists([], [])
            logger.warning(
                "Essential paths have not been set. Passing refresh and resetting mod lists"
            )
            # Wait for settings dialog to be closed before continuing.
            # This is to ensure steamcmd check and other ops are done after the user has a chance to set paths
            if (
                self._settings_dialog is not None
                and not self._settings_dialog.isHidden()
            ):
                loop = QEventLoop()
                self._settings_dialog.finished.connect(loop.quit)
                loop.exec_()
                logger.debug("Settings dialog closed. Continuing with refresh...")

        EventBus().refresh_finished.emit()

    def _do_clear(self) -> None:
        """
        Method to clear all the non-base, non-DLC mods from the active
        list widget and put them all into the inactive list widget.
        """
        self.mods_panel.reset_all_filters_and_search("Active")
        self.mods_panel.reset_all_filters_and_search("Inactive")
        # Metadata to insert
        active_mods_uuids: list[str] = []
        inactive_mods_uuids: list[str] = []
        logger.info("Clearing mods from active mod list")
        # Define the order of the DLC package IDs
        package_id_order = [
            app_constants.RIMWORLD_DLC_METADATA["294100"]["packageid"],
            app_constants.RIMWORLD_DLC_METADATA["1149640"]["packageid"],
            app_constants.RIMWORLD_DLC_METADATA["1392840"]["packageid"],
            app_constants.RIMWORLD_DLC_METADATA["1826140"]["packageid"],
            app_constants.RIMWORLD_DLC_METADATA["2380740"]["packageid"],
            app_constants.RIMWORLD_DLC_METADATA["3022790"]["packageid"],
        ]
        # If user wants Clear to also move DLC, only keep the base game in Active
        if self.settings.clear_moves_dlc and package_id_order:
            package_ids_to_keep_active = [package_id_order[0]]  # Base game only
        else:
            package_ids_to_keep_active = package_id_order
        # Single pass: build package_id→UUIDs reverse map and collect all UUIDs
        package_id_to_uuids: dict[str, list[str]] = {}
        all_uuids: set[str] = set()
        for uuid, mod_data in self.metadata_controller.mods_metadata.items():
            all_uuids.add(uuid)
            if (
                isinstance(mod_data, AboutXmlMod)
                and mod_data.mod_type == ModType.LUDEON
            ):
                pid = str(mod_data.package_id)
                package_id_to_uuids.setdefault(pid, []).append(uuid)
        # Look up DLC UUIDs from the reverse map (avoids N full scans)
        for package_id in package_ids_to_keep_active:
            if package_id in package_id_to_uuids:
                active_mods_uuids.extend(package_id_to_uuids[package_id])
        # Remainder goes to inactive
        active_uuids_set = set(active_mods_uuids)
        inactive_mods_uuids = [u for u in all_uuids if u not in active_uuids_set]
        # Clear dividers on list clear
        self.settings.active_mods_dividers = []
        self.settings.save()
        # Disable widgets while inserting
        self.disable_enable_widgets_signal.emit(False)
        # Insert data into lists
        self._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)
        # Re-enable widgets after inserting
        self.disable_enable_widgets_signal.emit(True)

    def _do_sort(self, check_deps: bool = True) -> None:
        """
        Trigger sorting of all active mods using user-configured algorithm
        & all available & configured metadata
        """
        # Get the live list of active and inactive mods. This is because the user
        # will likely sort before saving.
        logger.debug("Starting sorting mods")
        self.mods_panel.reset_all_filters_and_search("Active")
        self.mods_panel.reset_all_filters_and_search("Inactive")

        # Get active mods (exclude dividers)
        active_mods = {
            u for u in self.mods_panel.active_mods_list.paths if not is_divider_uuid(u)
        }

        # Check for missing dependencies if enabled in settings and check_deps is True
        if check_deps and self.settings.check_dependencies_on_sort:
            missing_deps = self.metadata_controller.get_missing_dependencies(
                active_mods
            )
            if missing_deps:
                dialog = MissingDependenciesDialog(
                    metadata_controller=self.metadata_controller
                )
                self.window_manager.register(dialog)

                # Build a deps_summary from the missing deps for the dialog display
                deps_summary: dict[str, dict[str, set[str]]] = {}
                for mod_id, deps in missing_deps.items():
                    deps_summary[mod_id] = {
                        "satisfied": set(),
                        "local": set(),
                        "download": deps,
                    }

                selected_deps = dialog.show_dialog(deps_summary, missing_deps)

                if selected_deps:
                    # Add selected mods to active mods
                    for mod_id in selected_deps:
                        # Find the UUID for this package ID
                        for (
                            uuid,
                            mod_data,
                        ) in self.metadata_controller.mods_metadata.items():
                            if (
                                isinstance(mod_data, AboutXmlMod)
                                and str(mod_data.package_id) == mod_id
                            ):
                                if uuid not in active_mods:
                                    active_mods.add(uuid)
                                break

        # Compile dependency data from MetadataController
        try:
            compiled_data = self.metadata_controller.compile(
                use_moddependencies_as_loadTheseBefore=self.settings.use_moddependencies_as_loadTheseBefore,
                use_alternative_package_ids=self.settings.use_alternative_package_ids_as_satisfying_dependencies,
            )
        except ValueError:
            dialogue.show_warning(
                title=self.tr("Metadata not loaded"),
                text=self.tr(
                    "Mod metadata has not finished loading. Please wait and try again."
                ),
            )
            return

        # Bridge: translate UUIDs↔paths for the new sort system.
        # Single pass over mods_metadata serves both maps.
        active_mod_paths: set[str] = set()
        path_to_uuid: dict[str, str] = {}
        for uuid, mod_data in self.metadata_controller.mods_metadata.items():
            if mod_data.mod_path:
                mp = str(mod_data.mod_path)
                path_to_uuid[mp] = uuid
                if uuid in active_mods:
                    active_mod_paths.add(mp)

        # Get the current order of active mods list and create a copy for comparison
        current_order = active_mods
        try:
            sorter = Sorter(
                self.settings.sorting_algorithm,
                compiled_data=compiled_data,
                mods_metadata=self.metadata_controller.mods_metadata,
                active_mod_paths=active_mod_paths,
            )
        except NotImplementedError as e:
            dialogue.show_warning(
                title=self.tr("Sorting algorithm not implemented"),
                text=self.tr("The selected sorting algorithm is not implemented"),
                information=(
                    self.tr(
                        "This may be caused by malformed settings or improper migration between versions or different mod manager.<br><br>"
                        "Try resetting your settings, selecting a different sorting algorithm, or "
                        "deleting your settings file.<br><br>"
                        "If the issue persists, please report it to the developers."
                    )
                ),
                details=str(e),
            )
            logger.error(f"Sort failed. Sorting algorithm not implemented: {e}")
            return

        success, new_order_paths = sorter.sort()

        # Bridge: translate paths back to UUIDs for the list widget
        new_order = [path_to_uuid[p] for p in new_order_paths if p in path_to_uuid]

        # Log the sort result and the order
        logger.debug(
            f"Sort result: {success}, new order: {new_order}, current order: {current_order}"
        )
        # Check if successful and orders differ
        if success and new_order != current_order:
            logger.info(
                "Finished combining all tiers of mods. Inserting into mod lists!"
            )
            # Move all dividers to the bottom after sort so the user
            # can reposition them.  Reset collapsed state so they are visible.
            saved_dividers = self.mods_panel.active_mods_list.get_dividers_data()
            bottom = len(new_order)
            for i, div in enumerate(saved_dividers):
                div["index"] = bottom + i
                div["collapsed"] = False
            self.settings.active_mods_dividers = saved_dividers
            self.settings.save()
            # Disable widgets while inserting
            self.disable_enable_widgets_signal.emit(False)
            # Insert data into lists
            self._insert_data_into_lists(
                new_order,
                [
                    uuid
                    for uuid in self.metadata_controller.mods_metadata
                    if uuid not in set(new_order)
                ],
            )
            # Enable widgets again after inserting
            self.disable_enable_widgets_signal.emit(True)
            logger.info("Insertion finished!")
        elif success and new_order == current_order:
            logger.info(
                "Sort completed, but the order of mods has not changed. No insertion needed."
            )
        elif not success:
            logger.warning("Failed to sort mods. Skipping insertion.")
        else:
            logger.warning("Unknown error occurred. Skipping insertion.")

    def _do_import_list_file_xml(self) -> None:
        self._import_export_handler.do_import_list_file_xml()

    def _do_export_list_file_xml(self) -> None:
        self._import_export_handler.do_export_list_file_xml()

    def _do_import_list_rentry(self) -> None:
        self._import_export_handler.do_import_list_rentry()

    def _do_import_list_workshop_collection(self) -> None:
        self._import_export_handler.do_import_list_workshop_collection()

    def _do_export_list_clipboard(self) -> None:
        self._import_export_handler.do_export_list_clipboard()

    def _do_upload_list_rentry(self) -> None:
        self._import_export_handler.do_upload_list_rentry()

    def _do_import_list_from_save_file(self) -> None:
        self._import_export_handler.do_import_list_from_save_file()

    def _do_open_app_directory(self) -> None:
        app_directory = os.getcwd()
        logger.info(f"Opening app directory: {app_directory}")
        platform_specific_open(app_directory)

    def _do_open_settings_directory(self) -> None:
        settings_directory = AppInfo().app_storage_folder
        logger.info(f"Opening settings directory: {settings_directory}")
        platform_specific_open(settings_directory)

    def _do_open_rimdex_logs_directory(self) -> None:
        logs_directory = AppInfo().user_log_folder
        logger.info(f"Opening RimDex logs directory: {logs_directory}")
        platform_specific_open(logs_directory)

    def _do_open_rimworld_directory(self) -> None:
        self._open_directory("RimWorld game", "game_folder")

    def _do_open_rimworld_config_directory(self) -> None:
        self._open_directory("RimWorld config", "config_folder")

    def _do_open_rimworld_logs_directory(self) -> None:
        user_home = Path.home()
        logs_directory = None
        if SystemInfo().operating_system == SystemInfo.OperatingSystem.MACOS:
            logs_directory = (
                user_home / "Library/Logs/Ludeon Studios/RimWorld by Ludeon Studios"
            )
        elif SystemInfo().operating_system == SystemInfo.OperatingSystem.LINUX:
            logs_directory = (
                user_home / ".config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios"
            )
        elif SystemInfo().operating_system == SystemInfo.OperatingSystem.WINDOWS:
            logs_directory = (
                user_home / "AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios"
            )

        if logs_directory and logs_directory.exists():
            logger.info(f"Opening RimWorld logs directory: {logs_directory}")
            platform_specific_open(logs_directory)
        else:
            self.show_dialog_specify_paths("RimWorld logs")

    def _do_open_local_mods_directory(self) -> None:
        self._open_directory("Local mods", "local_folder")

    def _do_open_steam_mods_directory(self) -> None:
        self._open_directory("Steam mods", "workshop_folder")

    def _open_directory(self, directory_name: str, attribute: str) -> None:
        current_instance = self.settings.current_instance
        directory = getattr(
            self.settings.instances[current_instance],
            attribute,
            None,
        )
        if directory and os.path.exists(directory):
            logger.info(f"Opening {directory_name} directory: {directory}")
            platform_specific_open(directory)
        else:
            self.show_dialog_specify_paths(directory_name)

    def show_dialog_specify_paths(self, directory_name: str) -> None:
        logger.error(f"Could not open {directory_name} directory")
        answer = dialogue.show_dialogue_conditional(
            title=self.tr("Could not open directory"),
            text=self.tr("{directory_name} path does not exist or is not set.").format(
                directory_name=directory_name
            ),
            information=self.tr("Would you like to set the path now?"),
            button_text_override=[self.tr("Open settings")],
        )
        answer_str = str(answer)
        download_text = self.tr("Open settings")
        if download_text in answer_str and self._show_settings_dialog is not None:
            self._show_settings_dialog()

    def _upload_file(self, path: Path | None) -> None:
        if not path or not os.path.exists(path):
            dialogue.show_warning(
                title=self.tr("File not found"),
                text=self.tr("The file you are trying to upload does not exist."),
                information=self.tr("File: {path}").format(path=path),
            )
            return

        success, ret = self.do_threaded_loading_animation(
            gif_path=str(AppInfo().theme_data_folder / "default-icons" / "rimdex.gif"),
            target=partial(upload_data_to_0x0_st, str(path)),
            text=self.tr("Uploading {path.name} to 0x0.st...").format(path=path),
        )

        if success:
            copy_to_clipboard_safely(ret)
            dialogue.show_information(
                title=self.tr("Uploaded file"),
                text=self.tr("Uploaded {path.name} to https://0x0.st/").format(
                    path=path
                ),
                information=self.tr(
                    "The URL has been copied to your clipboard:<br><br>{ret}"
                ).format(ret=ret),
            )
            webbrowser.open(ret)
        else:
            dialogue.show_warning(
                title=self.tr("Failed to upload file."),
                text=self.tr("Failed to upload the file to 0x0.st"),
                information=ret,
            )

    def _open_in_default_editor(self, path: Path | None) -> None:
        if path and path.exists():
            logger.info(f"Opening file in default editor: {path}")
            launch_process(
                self.settings.text_editor_location,
                self.settings.text_editor_folder_arg.split(" ") + [str(path)],
                str(AppInfo().application_folder),
            )
        else:
            dialogue.show_warning(
                title=self.tr("Failed to open file."),
                text=self.tr(
                    "Failed to open the file with default text editor. It may not exist."
                ),
            )

    def _do_save(self) -> None:
        """
        Method to save the current list of active mods to the selected ModsConfig.xml
        """
        logger.info("Saving current active mods to ModsConfig.xml")
        # Persist divider data before saving
        self.settings.active_mods_dividers = (
            self.mods_panel.active_mods_list.get_dividers_data()
        )
        self.settings.save()

        data = self._import_export_service.collect_active_mods(
            self.mods_panel.active_mods_list.paths, self.duplicate_mods
        )
        active_mods_uuids, inactive_mods_uuids, _, _ = (
            self.metadata_controller.get_mods_from_list(mod_list=data.active_mods)
        )
        self.active_mods_uuids_last_save = active_mods_uuids
        logger.info(f"Collected {len(data.active_mods)} active mods for saving")

        try:
            self._import_export_service.save_to_mods_config(data.active_mods)
        except Exception:
            logger.error("Could not save active mods")
            dialogue.show_fatal_error(
                title=self.tr("Could not save active mods"),
                text=self.tr("Failed to save active mods to file:"),
                details=traceback.format_exc(),
            )
        EventBus().do_save_button_animation_stop.emit()
        # Save current modlists to their respective restore states
        self.active_mods_uuids_restore_state = active_mods_uuids
        self.inactive_mods_uuids_restore_state = inactive_mods_uuids
        logger.info("Finished saving active mods")

    def _do_restore(self) -> None:
        """
        Method to restore the mod lists to the last saved state.
        TODO: restoring after clearing will cause a few harmless lines of
        'Inactive mod count changed to: 0' to appear.
        """
        if (
            self.active_mods_uuids_restore_state
            and self.inactive_mods_uuids_restore_state
        ):
            self.mods_panel.reset_all_filters_and_search("Active")
            self.mods_panel.reset_all_filters_and_search("Inactive")
            logger.info(
                f"Restoring cached mod lists with active list [{len(self.active_mods_uuids_restore_state)}] and inactive list [{len(self.inactive_mods_uuids_restore_state)}]"
            )
            # Disable widgets while inserting
            self.disable_enable_widgets_signal.emit(False)
            # Insert items into lists
            self._insert_data_into_lists(
                self.active_mods_uuids_restore_state,
                self.inactive_mods_uuids_restore_state,
            )
            # Reenable widgets after inserting
            self.disable_enable_widgets_signal.emit(True)
        else:
            logger.warning(
                "Cached mod lists for restore function not set as client started improperly. Passing on restore"
            )

    # TODDS ACTIONS
    def _create_todds_runner(self, is_pre_launch: bool) -> RunnerPanel:
        runner = RunnerPanel(
            todds_dry_run_support=self.settings.todds_dry_run,
            auto_close_on_complete=is_pre_launch,
        )

        base_title = "RimDex - todds texture encoder"
        suffix = " (pre-launch)" if is_pre_launch else ""
        runner.setWindowTitle(f"{base_title}{suffix}")

        if not is_pre_launch:
            self.todds_runner = runner
            self.window_manager.register_attr(self, "todds_runner")

        runner.show()
        return runner

    @overload
    def _do_optimize_textures(
        self, block_until_complete: Literal[True]
    ) -> tuple[bool, int]: ...

    @overload
    def _do_optimize_textures(self) -> None: ...

    def _do_optimize_textures(
        self, block_until_complete: bool = False
    ) -> tuple[bool, int] | None:
        logger.info("Optimizing textures with todds...")
        todds_runner = self._create_todds_runner(block_until_complete)
        active_uuids = list(self.mods_panel.active_mods_list.paths)

        started = self.todds_controller.optimize_textures(
            runner=todds_runner,
            active_mod_paths=active_uuids,
        )

        if not started:
            todds_runner.close()
            self._show_todds_no_paths_warning()
            return (False, -1) if block_until_complete else None

        if block_until_complete:
            loop = QEventLoop()
            todds_runner.process.finished.connect(loop.quit)
            loop.exec_()
            exit_code = todds_runner.process.exitCode()
            success = exit_code == 0
            if success:
                logger.info("todds process completed successfully")
            else:
                logger.warning(f"todds process failed with exit code: {exit_code}")
            return success, exit_code

        return None

    def _do_delete_dds_textures(self) -> None:
        answer = dialogue.show_dialogue_conditional(
            title=self.tr("Confirm texture deletion"),
            text=self.tr(
                "This will delete all optimized .dds textures from your active mods"
            ),
            information=self.tr(
                "Are you sure you want to delete all .dds textures? "
                "You can re-optimize them later if needed."
            ),
            button_text_override=[
                self.tr("Delete textures"),
            ],
        )
        if self.tr("Delete textures") not in str(answer):
            return

        logger.info("Deleting .dds textures with todds...")
        todds_runner = self._create_todds_runner(is_pre_launch=False)
        active_uuids = list(self.mods_panel.active_mods_list.paths)

        started = self.todds_controller.delete_dds_textures(
            runner=todds_runner,
            active_mod_paths=active_uuids,
        )

        if not started:
            todds_runner.close()
            self._show_todds_no_paths_warning()

    def _show_todds_no_paths_warning(self) -> None:
        dialogue.show_warning(
            title=self.tr("No valid paths for todds"),
            text=self.tr("todds could not find any valid mod folders to process."),
            information=self.tr(
                "None of the configured mod folder paths exist on disk.<br><br>"
                "Please verify your Local Mods and Workshop folders are correctly "
                "set in Settings, then try again."
            ),
        )

    # STEAM{CMD, WORKS} ACTIONS
    def _do_import_steamcmd_acf_data(self) -> None:
        self._steam_handler.do_import_steamcmd_acf_data()

    def _do_export_steamcmd_acf_data(self) -> None:
        self._steam_handler.do_export_steamcmd_acf_data()

    def _do_reset_steamcmd_acf_data(self) -> None:
        self._steam_handler.do_reset_steamcmd_acf_data()

    def _do_browse_workshop(self) -> None:
        self._steam_handler.do_browse_workshop()

    def _do_check_for_workshop_updates(self) -> None:
        self._steam_handler.do_check_for_workshop_updates()

    def do_steam_verify_game_files(self) -> None:
        self._steam_handler.do_steam_verify_game_files()

    def _do_setup_steamcmd(self) -> None:
        self._steam_handler.do_setup_steamcmd()

    def _do_download_mods_with_steamcmd(self, publishedfileids: list[str]) -> None:
        self._steam_handler.do_download_mods_with_steamcmd(publishedfileids)

    def _handle_steamworks_resubscribe(self, instruction: list[Any]) -> None:
        self._steam_handler.handle_steamworks_resubscribe(instruction)

    def _do_steamworks_api_call(self, instruction: list[Any]) -> None:
        self._steam_handler.do_steamworks_api_call(instruction)

    def _do_steamworks_api_call_animated(
        self, instruction: list[list[str] | str]
    ) -> None:
        self._steam_handler.do_steamworks_api_call_animated(instruction)

        # GIT MOD ACTIONS

    def _do_add_zip_mod(self) -> None:
        self._zip_mod_handler.do_add_zip_mod()

    def _extract_zip_file(self, file_path: str, delete: bool = False) -> None:
        self._zip_mod_handler.do_extract_zip_file(file_path, delete)

    def _do_extract_zip_to_path(
        self, base_path: str, file_path: str, delete: bool = False
    ) -> None:
        self._zip_mod_handler.do_extract_zip_to_path(base_path, file_path, delete)

    def _on_extract_progress(self, percent: int, message: str) -> None:
        self._zip_mod_handler._on_extract_progress(percent, message)

    def _on_extract_finished(self, success: bool, message: str) -> None:
        self._zip_mod_handler._on_extract_finished(success, message)

    def _do_open_rule_editor(
        self, compact: bool, initial_mode: str, packageid: str | None = None
    ) -> None:
        self.rule_editor = RuleEditor(
            metadata_controller=self.metadata_controller,
            compact=compact,
            edit_packageid=packageid,
            initial_mode=initial_mode,
        )
        self.window_manager.register_attr(self, "rule_editor")
        self.rule_editor._populate_from_metadata()
        self.rule_editor.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.rule_editor.update_database_signal.connect(self._do_update_rules_database)
        self.rule_editor.show()

    def _do_open_ignore_json_editor(self) -> None:
        """Open the Ignore JSON Editor dialog."""
        self.ignore_json_editor = IgnoreJsonEditor()
        self.window_manager.register_attr(self, "ignore_json_editor")
        self.ignore_json_editor.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.ignore_json_editor.show()

    def _do_configure_steam_db_file_path(self) -> None:
        # Input file
        logger.info("Opening file dialog to specify Steam DB")
        input_path = dialogue.show_dialogue_file(
            mode="open",
            caption="Choose Steam Workshop Database",
            _dir=str(AppInfo().app_storage_folder),
            _filter="JSON (*.json)",
        )
        logger.info(f"Selected path: {input_path}")
        if input_path and os.path.exists(input_path):
            self.settings.external_steam_metadata_file_path = input_path
            self.settings.save()
        else:
            logger.debug("USER ACTION: cancelled selection!")
            return

    def _do_configure_community_rules_db_file_path(self) -> None:
        # Input file
        logger.info("Opening file dialog to specify Community Rules DB")
        input_path = dialogue.show_dialogue_file(
            mode="open",
            caption="Choose Community Rules DB",
            _dir=str(AppInfo().app_storage_folder),
            _filter="JSON (*.json)",
        )
        logger.info(f"Selected path: {input_path}")
        if input_path and os.path.exists(input_path):
            self.settings.external_community_rules_file_path = input_path
            self.settings.save()
        else:
            logger.debug("USER ACTION: cancelled selection!")
            return

    def _do_configure_steam_database_repo(self) -> None:
        """
        Opens a QDialogInput that allows user to edit their Steam DB repo
        This URL is used for Steam DB repo related actions.
        """
        args, ok = QInputDialog.getText(
            None,
            self.tr("Edit Steam DB repo"),
            self.tr("Enter URL (https://github.com/AccountName/RepositoryName):"),
            text=self.settings.external_steam_metadata_repo,
        )
        if ok:
            self.settings.external_steam_metadata_repo = args
            self.settings.save()

    def _do_configure_community_rules_db_repo(self) -> None:
        """
        Opens a QDialogInput that allows user to edit their Community Rules
        DB repo. This URL is used for Steam DB repo related actions.
        """
        args, ok = QInputDialog.getText(
            None,
            self.tr("Edit Community Rules DB repo"),
            self.tr("Enter URL (https://github.com/AccountName/RepositoryName):"),
            text=self.settings.external_community_rules_repo,
        )
        if ok:
            self.settings.external_community_rules_repo = args
            self.settings.save()

    def _do_blacklist_action_steamdb(self, instruction: list[Any]) -> None:
        logger.info(f"Updating SteamDB blacklist status for item: {instruction}")
        # Retrieve instruction passed from signal
        publishedfileid = instruction[0]
        blacklist = instruction[1]
        comment = instruction[2] if blacklist else ""
        # Delegate to MetadataController
        success = self.metadata_controller.set_steam_db_blacklist(
            published_file_id=publishedfileid,
            blacklisted=blacklist,
            comment=comment or "",
        )
        if success:
            # Do a full refresh of metadata and UI
            self._do_refresh()
        else:
            logger.warning(
                "Could not update SteamDB blacklist: no Steam database loaded"
            )

    def _do_edit_steam_webapi_key(self) -> None:
        """
        Opens a QDialogInput that allows the user to edit their Steam API-key
        that are configured to be passed to the "Dynamic Query" feature for
        the Steam Workshop metadata needed for sorting
        """
        args, ok = QInputDialog.getText(
            None,
            self.tr("Edit Steam WebAPI key"),
            self.tr("Enter your personal 32 character Steam WebAPI key here:"),
            text=self.settings.steam_apikey,
        )
        if ok:
            self.settings.steam_apikey = args
            self.settings.save()

    def _do_update_rules_database(self, instruction: list[Any]) -> None:
        rules_source = instruction[0]
        rules_data = instruction[1]
        # Get path based on rules source
        cr_path = self.metadata_controller.community_rules_path
        if rules_source == "Community Rules" and cr_path:
            path = str(cr_path)
        elif rules_source == "User Rules" and str(
            AppInfo().databases_folder / "userRules.json"
        ):
            path = str(AppInfo().databases_folder / "userRules.json")
        else:
            logger.warning(
                f"No {rules_source} file path is set. There is no configured database to update!"
            )
            return
        # Retrieve original database
        try:
            with open(path, encoding="utf-8") as f:
                json_string = f.read()
                logger.debug("Reading info...")
                db_input_a = json.loads(json_string)
                logger.debug(
                    f"Retrieved copy of existing {rules_source} database to update."
                )
        except Exception:
            logger.error("Failed to read info from existing database")
            dialogue.show_warning(
                title=self.tr("Failed to read existing database"),
                text=self.tr("Failed to read the existing database!"),
                information=self.tr("Path: {path}").format(path=path),
            )
            return
        db_input_b = {"timestamp": int(time.time()), "rules": rules_data}
        db_output_c = db_input_a.copy()
        # Update database in place
        recursively_update_dict(
            db_output_c,
            db_input_b,
            prune_exceptions=app_constants.DB_BUILDER_PRUNE_EXCEPTIONS,
            recurse_exceptions=app_constants.DB_BUILDER_RECURSE_EXCEPTIONS,
        )
        # Overwrite rules database
        answer = dialogue.show_dialogue_conditional(
            title=self.tr("RimDex - DB Builder"),
            text=self.tr("Do you want to continue?"),
            information=self.tr(
                "This operation will overwrite the {rules_source} database located at the following path:<br><br>{path}"
            ).format(rules_source=rules_source, path=path),
        )
        if answer == QMessageBox.StandardButton.Yes:
            atomic_json_dump(db_output_c, path, indent=4)
            # Do a full refresh of metadata and UI
            self._do_refresh()
        else:
            logger.debug("USER ACTION: declined to continue rules database update.")

    def _do_set_database_expiry(self) -> None:
        """
        Opens a QDialogInput that allows the user to edit their preferred
        WebAPI Query Expiry (in seconds)
        """
        args, ok = QInputDialog.getText(
            None,
            self.tr("Edit SteamDB expiry:"),
            self.tr(
                "Enter your preferred expiry duration in seconds (default 1 week/604800 sec):"
            ),
            text=str(self.settings.database_expiry),
        )
        if ok:
            try:
                self.settings.database_expiry = int(args)
                self.settings.save()
            except ValueError:
                dialogue.show_warning(
                    self.tr(
                        "Tried configuring Dynamic Query with a value that is not an integer."
                    ),
                    self.tr(
                        "Please reconfigure the expiry value with an integer in terms of the seconds from epoch you would like your query to expire."
                    ),
                )

    @Slot()
    def _on_settings_have_changed(self) -> None:
        instance = self.settings.instances.get(self.settings.current_instance)
        if not instance:
            logger.warning(
                f"Tried to access instance {self.settings.current_instance} that does not exist!"
            )
            return None

        steamcmd_prefix = instance.steamcmd_install_path

        if steamcmd_prefix:
            self.steamcmd_wrapper.initialize_prefix(
                steamcmd_prefix=str(steamcmd_prefix),
                validate=self.settings.steamcmd_validate_downloads,
            )
        self.steamcmd_wrapper.validate_downloads = (
            self.settings.steamcmd_validate_downloads
        )

    @Slot()
    def _do_run_game(self) -> None:
        """
        Prepare and launch the RimWorld game process.

        This method handles the complete game launch workflow:
        1. Validates essential paths are configured
        2. Creates backup of settings and mod list
        3. Prompts user about unsaved mod list changes
        4. Optionally runs todds texture optimization
        5. Manages steam_appid.txt for Steam integration
        6. Launches game via Steam protocol (with overlay) or direct executable

        The launch method depends on user configuration:
        - If "launch_via_steam_protocol" is enabled: uses steam://rungameid/294100 URI
          (requires Steam Client Integration enabled, ignores custom run arguments)
        - Otherwise: launches executable directly with custom run arguments

        Note: Steam_appid.txt is created/removed based on steam_client_integration setting
        regardless of launch method, for compatibility.
        """
        if not self.check_if_essential_paths_are_set(prompt=True):
            return

        create_backup_in_thread(self.settings)

        # Check for unsaved mod list changes and prompt user
        current_mod_uuids = [
            u for u in self.mods_panel.active_mods_list.paths if not is_divider_uuid(u)
        ]
        if current_mod_uuids != self.active_mods_uuids_last_save:
            answer = dialogue.show_dialogue_conditional(
                title=self.tr("Unsaved Changes"),
                text=self.tr("You have unsaved changes. What would you like to do?"),
                button_text_override=[self.tr("Save and Run"), self.tr("Run Anyway")],
            )
            if answer == self.tr("Save and Run"):
                logger.info(
                    "User chose to save before proceeding with running the game."
                )
                self._do_save()
            elif answer == self.tr("Run Anyway"):
                logger.info(
                    "User chose to ignore unsaved changes and proceed with running the game anyway."
                )
                pass
            elif answer == QMessageBox.StandardButton.Cancel:
                logger.info("User chose to cancel.")
                return

        # Run todds before launch if auto-run is enabled
        if self.settings.auto_run_todds_before_launch:
            success, exit_code = self._do_optimize_textures(block_until_complete=True)

            # Show error message if todds failed, but continue to launch game
            if not success:
                dialogue.show_warning(
                    title=self.tr("todds Optimization Failed"),
                    text=self.tr(
                        "todds texture optimization failed (exit code: {exit_code}), but the game will launch anyway."
                    ).format(exit_code=exit_code),
                    information=self.tr(
                        "You may experience longer loading times or higher memory usage.<br><br>"
                        "Check the todds output window for details."
                    ),
                )

        # Retrieve instance configuration
        current_instance = self.settings.current_instance
        game_install_path = Path(self.settings.instances[current_instance].game_folder)
        run_args = self.settings.instances[current_instance].run_args

        # Retrieve Steam-related settings for this instance
        steam_client_integration = self.settings.instances[
            current_instance
        ].steam_client_integration

        launch_via_steam_protocol = self.settings.instances[
            current_instance
        ].launch_via_steam_protocol

        # Manage steam_appid.txt file for Steam integration
        # If Steam integration is enabled, Steam requires this file with the app ID in the game folder
        # The Steam App ID is "294100" for RimWorld.
        steam_appid_path = (
            # On macOS, steam_appid.txt should be outside the app bundle
            game_install_path.parent / "steam_appid.txt"
            if sys.platform == "darwin"
            # On Windows and Linux, place it directly in the game folder
            else game_install_path / "steam_appid.txt"
        )
        if steam_client_integration and not steam_appid_path.exists():
            with open(steam_appid_path, "w", encoding="utf-8") as f:
                f.write("294100")
        elif not steam_client_integration and steam_appid_path.exists():
            steam_appid_path.unlink()

        # Launch the game using the configured method
        if launch_via_steam_protocol:
            # Validate Steam Client Integration is enabled before using Steam protocol
            if not steam_client_integration:
                logger.warning(
                    "Steam protocol launch requested but Steam Client Integration is disabled."
                )
                dialogue.show_warning(
                    title=self.tr("Steam Client Integration is disabled"),
                    text=self.tr(
                        "Steam protocol launch requires Steam Client Integration to be enabled."
                    ),
                    information=self.tr(
                        "Please enable Steam Client Integration in Settings → Steam to use this feature."
                    ),
                )
                return

            # Launch via Steam protocol URI
            # This allows Steam to manage the game launch and enables the Steam overlay
            # Custom run arguments are ignored when using this method
            logger.info(
                "Launching game via Steam protocol URI (steam://rungameid/294100)..."
            )
            platform_specific_open("steam://rungameid/294100")
        else:
            # Launch game executable directly
            # This method ignores Steam overlay but respects custom run arguments
            logger.info("Launching game process without Steamworks API...")
            launch_game_process(game_install_path=game_install_path, run_args=run_args)

    @Slot()
    def _use_this_instead_clicked(self) -> None:
        """
        When clicked, opens the Use This Instead panel.
        """
        if self.settings.external_use_this_instead_metadata_source == "None":
            dialogue.show_warning(
                title=self.tr("Use This Instead"),
                text=self.tr(
                    'Please configure "Use This Instead" database in settings.'
                ),
            )
            return

        self.use_this_instead_dialog = UseThisInsteadPanel(
            mod_metadata=self.metadata_controller.mods_metadata,
            metadata_controller=self.metadata_controller,
        )
        self.window_manager.register_attr(self, "use_this_instead_dialog")
        if not self.use_this_instead_dialog.show_if_has_alternatives():
            dialogue.show_information(
                title=self.tr("Use This Instead"),
                text=self.tr(
                    'No suggestions were found in the "Use This Instead" database.'
                ),
            )
