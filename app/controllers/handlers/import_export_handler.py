"""Import / export operations for mod lists.

Extracted from ``MainContent`` (main_content_panel.py) to keep the view
class focused on layout and widget wiring.
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

import app.ui.dialogue as dialogue
from app.core.app_info import AppInfo
from app.core.ui_helpers import check_internet_connection, copy_to_clipboard_safely
from app.utils.rentry.wrapper import RentryImport
from app.utils.steam.webapi.wrapper import CollectionImport

if TYPE_CHECKING:
    from app.models.settings import Settings
    from app.views.main_content_panel import MainContent


class ImportExportHandler:
    """Handles mod list import/export operations (XML, rentry, workshop, clipboard, save)."""

    def __init__(self, settings: Settings, panel: MainContent) -> None:
        self._settings = settings
        self._panel = panel

    def do_import_list_file_xml(self) -> None:
        """Open a user-selected XML file. Calculate and display active and inactive lists based on this file."""
        logger.info("Opening file dialog to select input file")
        file_path = dialogue.show_dialogue_file(
            mode="open",
            caption="Open RimWorld mod list",
            _dir=str(AppInfo().saved_modlists_folder),
            _filter="RimWorld mod list (*.rml *.rws *.xml)",
        )
        logger.info(f"Selected path: {file_path}")
        if file_path:
            self._panel.mods_panel.reset_all_filters_and_search("Active")
            self._panel.mods_panel.reset_all_filters_and_search("Inactive")
            logger.info(f"Trying to import mods list from XML: {file_path}")
            (
                active_mods_uuids,
                inactive_mods_uuids,
                self._panel.duplicate_mods,
                self._panel.missing_mods,
            ) = self._panel.metadata_controller.get_mods_from_list(mod_list=file_path)
            logger.info("Got new mods according to imported XML")
            self._panel._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)
            self._panel._duplicate_mods_prompt()
            self._panel._missing_mods_prompt()
        else:
            logger.info("USER ACTION: pressed cancel, passing")

    def do_export_list_file_xml(self) -> None:
        """Export the current list of active mods to a user-designated file."""
        logger.info("Opening file dialog to specify output file")
        file_path = dialogue.show_dialogue_file(
            mode="save",
            caption="Save mod list",
            _dir=str(AppInfo().saved_modlists_folder),
            _filter="XML (*.xml)",
        )
        logger.info(f"Selected path: {file_path}")
        if file_path:
            data = self._panel._import_export_service.collect_active_mods(
                self._panel.mods_panel.active_mods_list.paths,
                self._panel.duplicate_mods,
            )
            try:
                self._panel._import_export_service.export_to_xml(
                    data.active_mods, file_path
                )
            except Exception:
                dialogue.show_fatal_error(
                    title=self._panel.tr("Failed to export to file"),
                    text=self._panel.tr("Failed to export active mods to file:"),
                    information=f"{file_path}",
                    details=traceback.format_exc(),
                )
        else:
            logger.debug("USER ACTION: pressed cancel, passing")

    def do_import_list_rentry(self) -> None:
        """Import a mod list from a Rentry.co link."""
        rentry_import = RentryImport(self._settings)
        if not rentry_import.package_ids:
            logger.debug("USER ACTION: pressed cancel or no package IDs, passing")
            return

        self._panel.mods_panel.reset_all_filters_and_search("Active")
        self._panel.mods_panel.reset_all_filters_and_search("Inactive")

        if rentry_import.publishedfileids:
            existing_publishedfileids = {
                mod_data.published_file_id
                for mod_data in self._panel.metadata_controller.mods_metadata.values()
                if mod_data.published_file_id is not None
            }
            filtered_publishedfileids = list(
                {
                    pfid
                    for pfid in rentry_import.publishedfileids
                    if pfid not in existing_publishedfileids
                }
            )

            def notify_user() -> None:
                dialogue.show_information(
                    title=self._panel.tr("Important"),
                    text=self._panel.tr(
                        "You will need to redo Rentry import again after downloads complete.<br><br>"
                        "If there missing mods after download completes, they will be shown inside the missing mods panel.<br><br>"
                        "If RimDex is still not able to download some mods, "
                        "It's due to the mod data not being available in both Rentry link and steam database."
                    ),
                )

            def dowmload_using_steamcmd() -> None:
                logger.info("Checking if SteamCMD is set up")
                steamcmd_wrapper = self._panel.steamcmd_wrapper

                if not steamcmd_wrapper.setup:
                    self._panel._do_setup_steamcmd()
                    if steamcmd_wrapper.setup:
                        logger.info("Using SteamCMD to download mods")
                        self._panel._do_download_mods_with_steamcmd(
                            filtered_publishedfileids
                        )
                        notify_user()
                else:
                    self._panel._do_download_mods_with_steamcmd(
                        filtered_publishedfileids
                    )
                    notify_user()

            def dowmload_using_steam() -> None:
                current_instance = self._settings.current_instance
                steam_client_integration = self._settings.instances[
                    current_instance
                ].steam_client_integration

                if steam_client_integration:
                    logger.info("Using Steamworks API to download mods")
                    self._panel._do_steamworks_api_call_animated(
                        [
                            "subscribe",
                            [
                                str(int(str_pfid))
                                for str_pfid in filtered_publishedfileids
                            ],
                        ]
                    )
                    notify_user()
                    return
                else:
                    dialogue.show_warning(
                        title=self._panel.tr("Steam client integration not set up"),
                        text=self._panel.tr(
                            "Steam client integration is not set up. Please set it up to download mods using Steam"
                        ),
                    )

            if filtered_publishedfileids:
                logger.info(
                    f"Trying to download {len(filtered_publishedfileids)} mods using publishedfileid: {filtered_publishedfileids}"
                )
                answer = dialogue.show_dialogue_conditional(
                    title=self._panel.tr("Download Rentry Mods"),
                    text=self._panel.tr("Please select a download method."),
                    information=self._panel.tr(
                        "Select which method you want to use to download missing Rentry mods."
                    ),
                    button_text_override=[
                        "Steam",
                        "SteamCMD",
                    ],
                )
                if answer == "Steam":
                    dowmload_using_steam()
                    return
                if answer == "SteamCMD":
                    dowmload_using_steamcmd()
                    return
                if answer == "Cancel":
                    return

        logger.info(
            f"Trying to import {len(rentry_import.package_ids)} mods from Rentry.co list"
        )

        (
            active_mods_uuids,
            inactive_mods_uuids,
            self._panel.duplicate_mods,
            self._panel.missing_mods,
        ) = self._panel.metadata_controller.get_mods_from_list(
            mod_list=rentry_import.package_ids
        )

        self._panel._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)
        logger.info("Got new mods according to imported Rentry.co")

        self._panel._duplicate_mods_prompt()
        self._panel._missing_mods_prompt()

    def do_import_list_workshop_collection(self) -> None:
        if not check_internet_connection():
            return
        collection_import = CollectionImport(
            metadata_controller=self._panel.metadata_controller
        )
        if not collection_import.package_ids:
            logger.debug("USER ACTION: pressed cancel or no package IDs, passing")
            return

        self._panel.mods_panel.reset_all_filters_and_search("Active")
        self._panel.mods_panel.reset_all_filters_and_search("Inactive")

        logger.info(
            f"Trying to import {len(collection_import.package_ids)} mods from Workshop collection list"
        )

        (
            active_mods_uuids,
            inactive_mods_uuids,
            self._panel.duplicate_mods,
            self._panel.missing_mods,
        ) = self._panel.metadata_controller.get_mods_from_list(
            mod_list=collection_import.package_ids
        )

        self._panel._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)
        logger.info("Got new mods according to imported Workshop collection")

        self._panel._duplicate_mods_prompt()
        self._panel._missing_mods_prompt()

    def do_export_list_clipboard(self) -> None:
        """Export the current list of active mods to the clipboard in a readable format."""
        logger.info("Generating report to export mod list to clipboard")
        data = self._panel._import_export_service.collect_active_mods(
            self._panel.mods_panel.active_mods_list.paths, self._panel.duplicate_mods
        )
        report = self._panel._import_export_service.build_clipboard_report(
            data.active_mods, data.packageid_to_uuid
        )
        dialogue.show_information(
            title=self._panel.tr("Export active mod list"),
            text=self._panel.tr("Copied active mod list report to clipboard..."),
            information=self._panel.tr('Click "Show Details" to see the full report!'),
            details=report,
        )
        copy_to_clipboard_safely(report)

    def do_upload_list_rentry(self) -> None:
        """Export the current list of active mods to Rentry.co."""
        data = self._panel._import_export_service.collect_active_mods(
            self._panel.mods_panel.active_mods_list.paths, self._panel.duplicate_mods
        )
        data.pfid_to_preview_url = (
            self._panel._import_export_service.fetch_steam_preview_urls(data.pfids)
        )
        report = self._panel._import_export_service.build_rentry_report(
            data.active_mods,
            data.packageid_to_uuid,
            data.steam_packageid_to_pfid,
            data.pfid_to_preview_url,
        )
        if len(report) > 200000:
            max_mods = self._panel._import_export_service.calculate_rentry_max_mods(
                data.active_mods,
                data.packageid_to_uuid,
                data.steam_packageid_to_pfid,
                data.pfid_to_preview_url,
            )
            if max_mods == 0:
                dialogue.show_warning(
                    title=self._panel.tr("Report too long"),
                    text=self._panel.tr(
                        "Even the first mod exceeds the 200,000 character limit."
                    ),
                    information=self._panel.tr(
                        "Cannot upload this report to Rentry.co."
                    ),
                )
                return
            answer = dialogue.show_dialogue_conditional(
                title=self._panel.tr("Report too long"),
                text=self._panel.tr("The mod list report exceeds 200,000 characters."),
                information=self._panel.tr(
                    "Rentry.co may reject uploads that are too long. Would you like to truncate the report to the first {max_mods} mods or cancel the upload?"
                ).format(max_mods=max_mods),
                button_text_override=[
                    self._panel.tr("Truncate to the first {max_mods} mods").format(
                        max_mods=max_mods
                    )
                ],
            )
            if answer == self._panel.tr("Truncate to the first {max_mods} mods").format(
                max_mods=max_mods
            ):
                truncated_mods = data.active_mods[:max_mods]
                report = self._panel._import_export_service.build_rentry_report(
                    truncated_mods,
                    data.packageid_to_uuid,
                    data.steam_packageid_to_pfid,
                    data.pfid_to_preview_url,
                    truncated=True,
                )
            else:
                logger.info("USER ACTION: cancelled truncation, passing")
                return
        success, url = self._panel._import_export_service.upload_rentry_report(report)
        if success and url:
            copy_to_clipboard_safely(url)
            dialogue.show_information(
                title=self._panel.tr("Uploaded active mod list"),
                text=self._panel.tr(
                    "Uploaded active mod list report to Rentry.co! The URL has been copied to your clipboard:<br><br>{url}"
                ).format(url=url),
                information=self._panel.tr(
                    'Click "Show Details" to see the full report!'
                ),
                details=report,
            )
        else:
            dialogue.show_warning(
                title=self._panel.tr("Failed to upload"),
                text=self._panel.tr(
                    "Failed to upload exported active mod list to Rentry.co"
                ),
            )

    def do_import_list_from_save_file(self) -> None:
        """Import a mod list from a RimWorld save (.rws) file."""
        logger.info("Opening file dialog to select RimWorld save (.rws)")
        saves_dir = str(
            Path(
                self._settings.instances[self._settings.current_instance].config_folder
            ).parent
            / "Saves"
        )
        file_path = dialogue.show_dialogue_file(
            mode="open",
            caption=self._panel.tr("Import from RimWorld Save File"),
            _dir=saves_dir,
            _filter=self._panel.tr("RimWorld save (*.rws);;All files (*.*)"),
        )
        logger.info(f"Selected save path: {file_path}")
        if not file_path:
            logger.debug("USER ACTION: pressed cancel, passing")
            return

        self._panel.mods_panel.reset_all_filters_and_search("Active")
        self._panel.mods_panel.reset_all_filters_and_search("Inactive")

        logger.info(f"Trying to import mods list from save file: {file_path}")
        (
            active_mods_uuids,
            inactive_mods_uuids,
            self._panel.duplicate_mods,
            self._panel.missing_mods,
        ) = self._panel.metadata_controller.get_mods_from_list(mod_list=file_path)
        logger.info("Got new mods according to imported save file")

        self._panel._insert_data_into_lists(active_mods_uuids, inactive_mods_uuids)

        self._panel._duplicate_mods_prompt()
        self._panel._missing_mods_prompt()
