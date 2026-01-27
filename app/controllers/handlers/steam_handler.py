"""Steam / SteamCMD / Steamworks operations.

Extracted from ``MainContent`` (main_content_panel.py) to keep the view
class focused on layout and widget wiring.
"""

from __future__ import annotations

import os
import shutil
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QMessageBox

import app.ui.dialogue as dialogue
from app.core.app_info import AppInfo
from app.core.ui_helpers import check_internet_connection, platform_specific_open
from app.utils.steam.steambrowser.browser import SteamBrowser
from app.utils.steam.workshop_utils import (
    WorkshopUpdateResult,
    check_if_pfids_blacklisted,
    import_steamcmd_acf_data,
    query_workshop_update_data,
)
from app.windows.runner_panel import RunnerPanel
from app.windows.workshop_mod_updater_panel import WorkshopModUpdaterPanel

if TYPE_CHECKING:
    from app.models.settings import Settings
    from app.views.main_content_panel import MainContent


class SteamHandler:
    """Handles Steam, SteamCMD, and Steamworks operations."""

    def __init__(self, settings: Settings, panel: MainContent) -> None:
        self._settings = settings
        self._panel = panel

    def do_import_steamcmd_acf_data(self) -> None:
        """Import an ACF file to replace the current SteamCMD ACF data."""
        answer = dialogue.show_dialogue_conditional(
            title=self._panel.tr("Confirm ACF import"),
            text=self._panel.tr("This will replace your current steamcmd .acf file"),
            information=self._panel.tr(
                "Are you sure you want to import .acf? This only works for steamcmd"
            ),
            button_text_override=[
                self._panel.tr("Import .acf"),
            ],
        )
        answer_str = str(answer)
        import_text = self._panel.tr("Import .acf")
        if import_text in answer_str:
            logger.debug("User confirmed ACF import")
            logger.info("Importing SteamCMD ACF data...")
            import_steamcmd_acf_data(
                rimdex_storage_path=str(AppInfo().app_storage_folder),
                steamcmd_appworkshop_acf_path=self._panel.steamcmd_wrapper.steamcmd_appworkshop_acf_path,
            )

    def do_export_steamcmd_acf_data(self) -> None:
        """Export the raw ACF file to a user-defined location by copying the file."""
        steamcmd_acf_path = Path(
            self._panel.steamcmd_wrapper.steamcmd_appworkshop_acf_path
        )

        if not steamcmd_acf_path or not steamcmd_acf_path.is_file():
            acf_path_str = str(steamcmd_acf_path) if steamcmd_acf_path else "None"
            logger.error(f"Export failed: ACF file not found: {acf_path_str}")
            dialogue.show_warning(
                title=self._panel.tr("Export Error"),
                text=self._panel.tr("ACF file not found at: {acf_path}").format(
                    acf_path=acf_path_str
                ),
            )
            return

        file_path = dialogue.show_dialogue_file(
            mode="save",
            caption="Export ACF File",
            _dir="appworkshop_294100.acf",
            _filter="ACF Files (*.acf);;All Files (*)",
        )
        if not file_path:
            logger.debug("User canceled export ACF")
            return

        try:
            shutil.copy(str(steamcmd_acf_path), file_path)
            logger.debug(f"Successfully exported ACF to {file_path}")
            dialogue.show_information(
                title=self._panel.tr("Export Success"),
                text=self._panel.tr("Successfully exported ACF to {file_path}").format(
                    file_path=file_path
                ),
            )
        except PermissionError:
            error_msg = self._panel.tr(
                "Export failed: Permission denied - check file permissions"
            )
            logger.error(f"Export failed due to Permission: {error_msg}")
            dialogue.show_warning(title=self._panel.tr("Export Error"), text=error_msg)
        except Exception as e:
            error_msg = self._panel.tr("Export failed: {e}").format(e=str(e))
            logger.error(f"Export failed: {error_msg}")
            dialogue.show_warning(title=self._panel.tr("Export Error"), text=error_msg)

    def do_reset_steamcmd_acf_data(self) -> None:
        answer = dialogue.show_dialogue_conditional(
            title=self._panel.tr("Reset SteamCMD ACF data file"),
            text=self._panel.tr(
                "Are you sure you want to reset SteamCMD ACF data file?"
            ),
            information=self._panel.tr(
                "This file is created and used by steamcmd to track mod informaton, This action cannot be undone."
            ),
        )
        if answer == QMessageBox.StandardButton.Yes:
            logger.info("Resetting SteamCMD ACF data file")
            steamcmd_appworkshop_acf_path = (
                self._panel.steamcmd_wrapper.steamcmd_appworkshop_acf_path
            )
            if os.path.exists(steamcmd_appworkshop_acf_path):
                logger.debug(
                    f"Deleting SteamCMD ACF data file: {steamcmd_appworkshop_acf_path}"
                )
                os.remove(steamcmd_appworkshop_acf_path)
                dialogue.show_information(
                    title=self._panel.tr("Reset SteamCMD ACF data file"),
                    text=self._panel.tr(
                        f"Successfully deleted SteamCMD ACF data file: {steamcmd_appworkshop_acf_path}"
                    ),
                    information=self._panel.tr(
                        "ACF data file will be recreated when you download mods using steamcmd next time."
                    ),
                )
                self._panel._do_refresh()
            else:
                logger.debug("SteamCMD ACF data does not exist. Skipping deletion.")
                dialogue.show_warning(
                    title=self._panel.tr("SteamCMD ACF data file does not exist"),
                    text=self._panel.tr(
                        "ACf file does not exist. It will be created when you download mods using steamcmd."
                    ),
                )
        else:
            logger.debug("user cancelled reset of SteamCMD ACF data file")

    def do_browse_workshop(self) -> None:
        if self._panel.steam_browser:
            self._panel.steam_browser.close()
            self._panel.steam_browser.deleteLater()

        self._panel.steam_browser = SteamBrowser(
            "https://steamcommunity.com/app/294100/workshop/",
            self._panel.metadata_controller,
            self._settings,
        )
        self._panel.window_manager.register_attr(self._panel, "steam_browser")

        self._panel.steam_browser.destroyed.connect(
            lambda: setattr(self._panel, "steam_browser", None)
        )
        self._panel.steam_browser.show()

    def do_check_for_workshop_updates(self) -> None:
        if not check_internet_connection():
            return
        result: WorkshopUpdateResult = self._panel.do_threaded_loading_animation(
            gif_path=str(
                AppInfo().theme_data_folder / "default-icons" / "steam_api.gif"
            ),
            target=partial(
                query_workshop_update_data,
                mods=self._panel.metadata_controller.mods_metadata,
                metadata_controller=self._panel.metadata_controller,
            ),
            text=self._panel.tr("Checking Steam Workshop mods for updates..."),
        )

        if result.status == "no_workshop_mods":
            self._panel.status_signal.emit(
                self._panel.tr("No Workshop mods to check for updates")
            )
            return

        if result.status == "failed":
            dialogue.show_warning(
                title=self._panel.tr("Unable to check for updates"),
                text=self._panel.tr(
                    "RimDex was unable to check your Workshop mods for updates."
                ),
                details="\n".join(result.errors) if result.errors else None,
            )
            return

        if result.status == "partial":
            dialogue.show_warning(
                title=self._panel.tr("Update check partially completed"),
                text=self._panel.tr(
                    "{failed} out of {total} Workshop mods could not be checked for updates."
                ).format(
                    failed=len(result.failed_pfids),
                    total=result.mods_checked,
                ),
                details="\n".join(result.errors) if result.errors else None,
            )

        workshop_mod_updater = WorkshopModUpdaterPanel(
            metadata_controller=self._panel.metadata_controller
        )
        self._panel.window_manager.register(workshop_mod_updater)
        if workshop_mod_updater._row_count() > 0:
            logger.debug("Displaying potential Workshop mod updates")
            workshop_mod_updater.show()
        else:
            self._panel.status_signal.emit(
                self._panel.tr("All Workshop mods appear to be up to date!")
            )

    def do_steam_verify_game_files(self) -> None:
        """Verify RimWorld game files through Steam."""
        steam_client_integration_enabled = self._settings.instances[
            self._settings.current_instance
        ].steam_client_integration

        if not steam_client_integration_enabled:
            logger.warning(
                "Steam Client Integration is disabled. Cannot verify game files."
            )
            dialogue.show_warning(
                title=self._panel.tr("Steam Client Integration is disabled"),
                text=self._panel.tr(
                    "This feature requires Steam Client Integration to be enabled in Settings.<br><br>"
                    "Please enable Steam Client Integration if you own the game on Steam."
                ),
            )
            return

        if not check_internet_connection():
            return

        logger.info("Verifying game files through Steam.")
        logger.info("Steam Client Integration enabled. Opening Steam URI protocol.")
        platform_specific_open("steam://validate/294100")

    def _active_steamcmd_runner(self) -> RunnerPanel | None:
        """Return the running SteamCMD runner, or None if not running."""
        runner = self._panel.steamcmd_runner
        if (
            runner is not None
            and runner.process is not None
            and runner.process.state() == QProcess.ProcessState.Running
        ):
            return runner
        return None

    def _warn_no_publishedfileids(self) -> None:
        dialogue.show_warning(
            title=self._panel.tr("RimDex"),
            text=self._panel.tr("No PublishedFileIds were supplied in operation."),
            information=self._panel.tr(
                "Please add mods to list before attempting to download."
            ),
        )

    def do_setup_steamcmd(self) -> None:
        runner = self._active_steamcmd_runner()
        if runner is not None:
            dialogue.show_warning(
                title=self._panel.tr("RimDex - SteamCMD setup"),
                text=self._panel.tr("Unable to create SteamCMD runner!"),
                information=self._panel.tr(
                    "There is an active process already running!"
                ),
                details=f"PID {runner.process.processId()} : "
                + runner.process.program(),
            )
            return
        local_mods_path = self._settings.instances[
            self._settings.current_instance
        ].local_folder
        if local_mods_path and os.path.exists(local_mods_path):
            self._panel.steamcmd_runner = RunnerPanel()
            self._panel.window_manager.register_attr(self._panel, "steamcmd_runner")
            self._panel.steamcmd_runner.setWindowTitle("RimDex - SteamCMD setup")
            self._panel.steamcmd_runner.show()
            self._panel.steamcmd_runner.message("Setting up steamcmd...")
            self._panel.steamcmd_wrapper.setup_steamcmd(
                local_mods_path,
                False,
                self._panel.steamcmd_runner,
            )
            RunnerPanel().process_complete()
        else:
            dialogue.show_warning(
                title=self._panel.tr("RimDex - SteamCMD setup"),
                text=self._panel.tr(
                    "Unable to initiate SteamCMD installation. Local mods path not set!"
                ),
                information=self._panel.tr(
                    "Please configure local mods path in Settings before attempting to install."
                ),
            )

    def do_download_mods_with_steamcmd(self, publishedfileids: list[str]) -> None:
        logger.debug(
            f"Attempting to download {len(publishedfileids)} mods with SteamCMD"
        )
        steam_db_schema = self._panel.metadata_controller.steam_db
        steam_db = steam_db_schema.database if steam_db_schema else {}
        if steam_db:
            publishedfileids = check_if_pfids_blacklisted(
                publishedfileids=publishedfileids,
                steamdb=steam_db,
            )
        if len(publishedfileids) == 0:
            self._warn_no_publishedfileids()
            return
        runner = self._active_steamcmd_runner()
        if runner is not None:
            dialogue.show_warning(
                title=self._panel.tr("RimDex"),
                text=self._panel.tr("Unable to create SteamCMD runner!"),
                information=self._panel.tr(
                    "There is an active process already running!"
                ),
                details=f"PID {runner.process.processId()} : "
                + runner.process.program(),
            )
            return
        if self._panel.steamcmd_wrapper.steamcmd and os.path.exists(
            self._panel.steamcmd_wrapper.steamcmd
        ):
            if self._panel.steam_browser:
                self._panel.steam_browser.close()

            self._panel.steamcmd_runner = RunnerPanel(
                steamcmd_download_tracking=publishedfileids,
                steam_db=steam_db,
            )
            self._panel.window_manager.register_attr(self._panel, "steamcmd_runner")
            self._panel.steamcmd_runner.setWindowTitle("RimDex - SteamCMD downloader")
            self._panel.steamcmd_runner.show()
            self._panel.steamcmd_runner.message(
                f"Downloading {len(publishedfileids)} mods with SteamCMD..."
            )
            self._panel.steamcmd_wrapper.download_mods(
                publishedfileids=publishedfileids,
                runner=self._panel.steamcmd_runner,
                clear_cache=self._settings.instances[
                    self._settings.current_instance
                ].steamcmd_auto_clear_depot_cache,
            )
        else:
            dialogue.show_warning(
                title=self._panel.tr("SteamCMD not found"),
                text=self._panel.tr("SteamCMD executable was not found."),
                information=self._panel.tr(
                    'Please setup an existing SteamCMD prefix, or setup a new prefix with "Setup SteamCMD".'
                ),
            )

    def handle_steamworks_resubscribe(self, instruction: list[Any]) -> None:
        """Handle mod revalidation by forcing Steam to validate and redownload mods."""
        logger.info(f"Validating mods with instruction: {instruction}")
        platform_specific_open(f"steam://validate/294100/{instruction[1]}")

    def do_steamworks_api_call(self, instruction: list[Any]) -> None:
        """Create & launch Steamworks API process to handle instructions received from connected signals."""
        from app.utils.steam.availability import check_steam_available
        from app.utils.steam.steamworks.wrapper import (
            SteamworksGameLaunch,
            SteamworksSubscriptionHandler,
        )

        logger.info(f"Received Steamworks API instruction: {instruction}")
        libs_path = str(AppInfo().libs_folder)
        if not self._panel.steamworks_in_use:
            if not check_steam_available(_libs=libs_path):
                logger.error("Steam is not available, skipping Steamworks API call")
                return
            subscription_actions = ["resubscribe", "subscribe", "unsubscribe"]
            supported_actions = ["launch_game_process"]
            supported_actions.extend(subscription_actions)
            if instruction[0] in supported_actions:
                if instruction[0] == "launch_game_process":
                    self._panel.steamworks_in_use = True
                    steamworks_api_process = SteamworksGameLaunch(
                        game_install_path=instruction[1][0],
                        run_args=instruction[1][1],
                        _libs=libs_path,
                    )
                    steamworks_api_process.start()
                    logger.info(
                        f"Steamworks API process wrapper started with PID: {steamworks_api_process.pid}"
                    )
                    steamworks_api_process.join()
                    logger.info(
                        f"Steamworks API process wrapper completed for PID: {steamworks_api_process.pid}"
                    )
                    self._panel.steamworks_in_use = False
                elif (
                    instruction[0] in subscription_actions and len(instruction[1]) >= 1
                ):
                    logger.info(
                        f"Creating Steamworks API process with instruction {instruction}"
                    )
                    self._panel.steamworks_in_use = True
                    logger.debug(
                        f"Processing {instruction[0]} sequentially for {len(instruction[1])} mod(s)"
                    )
                    handler = SteamworksSubscriptionHandler(
                        action=instruction[0],
                        pfid_or_pfids=instruction[1],
                        _libs=libs_path,
                    )
                    handler.start()
                    handler.join()
                    self._panel.steamworks_in_use = False
                else:
                    logger.warning(
                        "Skipping Steamworks API call - only 1 Steamworks API initialization allowed at a time!!"
                    )
            else:
                logger.error(f"Unsupported instruction {instruction}")
                return
        else:
            logger.warning(
                "Steamworks API is already initialized! We do NOT want multiple interactions. Skipping instruction..."
            )

    def do_steamworks_api_call_animated(
        self, instruction: list[list[str] | str]
    ) -> None:
        publishedfileids = instruction[1]
        logger.debug(f"Attempting to download {len(publishedfileids)} mods with Steam")
        steam_db_schema = self._panel.metadata_controller.steam_db
        steamdb = steam_db_schema.database if steam_db_schema else {}
        if instruction[0] == "subscribe":
            assert isinstance(publishedfileids, list)
            publishedfileids = check_if_pfids_blacklisted(
                publishedfileids=publishedfileids,
                steamdb=steamdb,
            )
        if len(publishedfileids) == 0:
            self._warn_no_publishedfileids()
            return
        if self._panel.steam_browser:
            self._panel.steam_browser.close()
        self._panel.do_threaded_loading_animation(
            gif_path=str(AppInfo().theme_data_folder / "default-icons" / "steam.gif"),
            target=partial(self.do_steamworks_api_call, instruction=instruction),
            text=self._panel.tr(
                "Processing Steam subscription action(s) via Steamworks API..."
            ),
        )
