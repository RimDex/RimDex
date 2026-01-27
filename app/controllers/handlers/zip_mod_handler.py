"""ZIP mod import operations.

Extracted from ``MainContent`` (main_content_panel.py) to keep the view
class focused on layout and widget wiring.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox

import app.ui.dialogue as dialogue
from app.core.app_info import AppInfo
from app.core.ui_helpers import check_internet_connection
from app.io.zip_extractor import (
    BadZipFile,
    ZipExtractThread,
    get_zip_contents,
)
from app.net import http
from app.views.task_progress_window import TaskProgressWindow

if TYPE_CHECKING:
    from app.models.settings import Settings
    from app.views.main_content_panel import MainContent


class ZipModHandler:
    """Handles ZIP mod import operations (download, select, extract)."""

    def __init__(self, settings: Settings, panel: MainContent) -> None:
        self._settings = settings
        self._panel = panel

    def do_add_zip_mod(self) -> None:
        """Opens a dialog to select a ZIP file to add to the local mods directory."""
        answer = dialogue.show_dialogue_conditional(
            title=self._panel.tr("Download or select from local"),
            text=self._panel.tr(
                "Please select a ZIP file to add to the local mods directory."
            ),
            information=self._panel.tr(
                "You can download a ZIP file from the internet, or select a file from your local machine."
            ),
            button_text_override=[
                "Download",
                "Select from local",
            ],
        )

        if answer == "Download":
            url, ok = QInputDialog.getText(
                None,
                self._panel.tr("Enter zip file url"),
                self._panel.tr(
                    "Enter a zip file url (http/https) to download to local mods:"
                ),
            )
            if url and ok:
                if not check_internet_connection():
                    return
                file_download, temp_path = tempfile.mkstemp(suffix=".zip")
                os.close(file_download)

                self._panel.mod_info_panel.info_panel_frame.hide()
                self._panel.disable_enable_widgets_signal.emit(False)

                progress_widget = TaskProgressWindow(
                    title="Downloading ZIP File",
                    show_message=True,
                    show_percent=True,
                )
                self._panel.mod_info_panel.panel.addWidget(progress_widget)

                download_cancelled = False

                def on_cancel_requested() -> None:
                    nonlocal download_cancelled
                    download_cancelled = True
                    logger.info("User cancelled download")

                progress_widget.cancel_requested.connect(on_cancel_requested)

                try:
                    logger.info(f"Downloading {url} to {temp_path}")
                    response = http.get(url, stream=True, timeout=30)
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded_size = 0

                    with open(temp_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if download_cancelled:
                                logger.warning("Download cancelled by user")
                                break

                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                if total_size > 0:
                                    percent = int((downloaded_size / total_size) * 100)
                                    size_mb = downloaded_size / (1024 * 1024)
                                    total_mb = total_size / (1024 * 1024)
                                    message = f"Downloading: {size_mb:.2f} / {total_mb:.2f} MB"
                                else:
                                    percent = -1
                                    size_mb = downloaded_size / (1024 * 1024)
                                    message = f"Downloading: {size_mb:.2f} MB"

                                progress_widget.update_progress(percent, message)
                                QApplication.processEvents()

                    self._panel.mod_info_panel.panel.removeWidget(progress_widget)
                    progress_widget.close()

                    if not download_cancelled:
                        self.do_extract_zip_file(temp_path, delete=True)
                    else:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        logger.info("Download cancelled, cleaned up temporary file")

                except Exception as e:
                    self._panel.mod_info_panel.panel.removeWidget(progress_widget)
                    progress_widget.close()
                    logger.error(f"Failed to download zip file: {e}")
                    dialogue.show_warning(
                        title=self._panel.tr("Failed to download zip file"),
                        text=self._panel.tr("The zip file could not be downloaded."),
                        information=self._panel.tr(
                            "File: {file_path}<br>Error: {e}"
                        ).format(file_path=temp_path, e=e),
                    )
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                self._panel.mod_info_panel.info_panel_frame.show()
                self._panel.disable_enable_widgets_signal.emit(True)
        elif answer == "Select from local":
            file_path = dialogue.show_dialogue_file(
                mode="open",
                caption="Choose Zip File",
                _dir=str(AppInfo().app_storage_folder),
                _filter="Zip file (*.zip)",
            )
            if file_path:
                self.do_extract_zip_file(file_path)

    def do_extract_zip_file(self, file_path: str, delete: bool = False) -> None:
        logger.info(f"Selected path: {file_path}")
        if not file_path:
            logger.debug("USER ACTION: cancelled selection!")
            return

        if not os.path.isfile(file_path):
            logger.error(f"ZIP file does not exist: {file_path}")
            dialogue.show_warning(
                title=self._panel.tr("File not found"),
                text=self._panel.tr("The selected file does not exist."),
                information=self._panel.tr("File: {file_path}").format(
                    file_path=file_path
                ),
            )
            return

        base_path = str(
            self._settings.instances[self._settings.current_instance].local_folder
        )

        try:
            self.do_extract_zip_to_path(base_path, file_path, delete)
        except NotImplementedError as e:
            logger.error(f"Unsupported compression method: {e}")
            dialogue.show_warning(
                title=self._panel.tr("Unsupported Compression Method"),
                text=self._panel.tr(
                    "This ZIP file uses a compression method that is not supported by this version."
                ),
                information=self._panel.tr("File: {file_path}<br>Error: {e}").format(
                    file_path=file_path, e=e
                ),
            )
        except (BadZipFile, ValueError, PermissionError, OSError) as e:
            logger.error(f"Failed to extract zip file: {e}")
            dialogue.show_warning(
                title=self._panel.tr("Failed to extract zip file"),
                text=self._panel.tr("The zip file could not be extracted."),
                information=self._panel.tr("File: {file_path}<br>Error: {e}").format(
                    file_path=file_path, e=e
                ),
            )

    def do_extract_zip_to_path(
        self, base_path: str, file_path: str, delete: bool = False
    ) -> None:
        zip_contents = get_zip_contents(file_path)
        conflicts = []
        non_conflicts = []

        top_level_dirs = set(p.split("/")[0] for p in zip_contents if "/" in p)
        is_bare_mod = "About" in top_level_dirs and not all(
            p.startswith(tuple(top_level_dirs - {"About"})) for p in zip_contents
        )

        if is_bare_mod or len(top_level_dirs) == 0:
            folder_name = Path(file_path).stem
            base_path = os.path.join(base_path, folder_name)
            os.makedirs(base_path, exist_ok=True)

        for item in zip_contents:
            target_path = os.path.join(base_path, item)
            if os.path.exists(target_path):
                conflicts.append(item)
            else:
                non_conflicts.append(item)

        overwrite = True
        if conflicts and not non_conflicts:
            answer = dialogue.show_dialogue_conditional(
                title=self._panel.tr("Existing files or directories found"),
                text=self._panel.tr(
                    "All files in the archive already exist in the target path."
                ),
                information=self._panel.tr(
                    "How would you like to proceed?<br><br>"
                    "1) Overwrite All — Replace all existing files and directories.<br>"
                    "2) Cancel — Abort the operation."
                ),
                button_text_override=["Overwrite All"],
            )
            if answer != "Overwrite All":
                return
            overwrite = True
        elif conflicts:
            answer = dialogue.show_dialogue_conditional(
                title=self._panel.tr("Existing files or directories found"),
                text=self._panel.tr(
                    "The following files or directories already exist in the target path:"
                ),
                information=self._panel.tr(
                    "{conflicts_list}<br><br>"
                    "How would you like to proceed?<br><br>"
                    "1) Overwrite All — Replace all existing files and directories.<br>"
                    "2) Skip Existing — Extract only new files and leave existing ones untouched.<br>"
                    "3) Cancel — Abort the extraction."
                ).format(
                    conflicts_list="<br/>".join(conflicts[:5])
                    + ("<br/>...<br/>" if len(conflicts) > 5 else "")
                ),
                button_text_override=["Overwrite All", "Skip Existing"],
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            overwrite = answer == "Overwrite All"

        self._panel.mod_info_panel.info_panel_frame.hide()
        self._panel.disable_enable_widgets_signal.emit(False)

        progress_widget = TaskProgressWindow(
            title="Extracting ZIP File",
            show_message=True,
            show_percent=True,
        )
        self._panel.mod_info_panel.panel.addWidget(progress_widget)

        self._panel._extract_progress_widget = progress_widget

        self._panel._extract_thread = ZipExtractThread(
            file_path, base_path, overwrite_all=overwrite, delete=delete
        )
        self._panel._extract_thread.progress.connect(self._on_extract_progress)
        self._panel._extract_thread.finished.connect(self._on_extract_finished)
        progress_widget.cancel_requested.connect(self._panel._extract_thread.stop)

        self._panel._extract_thread.start()

    def _on_extract_progress(self, percent: int, message: str) -> None:
        """Update progress bar during extraction."""
        if (
            hasattr(self._panel, "_extract_progress_widget")
            and self._panel._extract_progress_widget
        ):
            self._panel._extract_progress_widget.update_progress(percent, message)

    def _on_extract_finished(self, success: bool, message: str) -> None:
        """Handle extraction completion."""
        try:
            if (
                hasattr(self._panel, "_extract_progress_widget")
                and self._panel._extract_progress_widget
            ):
                self._panel.mod_info_panel.panel.removeWidget(
                    self._panel._extract_progress_widget
                )
                self._panel._extract_progress_widget.close()
                self._panel._extract_progress_widget = None

            if success:
                dialogue.show_information(
                    title=self._panel.tr("Extraction completed"),
                    text=self._panel.tr("The ZIP file was successfully extracted!"),
                    information=message,
                )
            else:
                dialogue.show_warning(
                    title=self._panel.tr("Extraction failed"),
                    text=self._panel.tr("An error occurred during extraction."),
                    information=message,
                )

        finally:
            self._panel.mod_info_panel.info_panel_frame.show()
