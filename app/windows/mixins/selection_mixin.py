"""Selection and PFID operations mixin for BaseModsPanel.

Holds row-selection helpers, SteamCMD/Steamworks dispatch, and the
missing-published-file-id notification flow.
"""

from __future__ import annotations

import os
import shutil
from functools import partial
from typing import Any, Callable, TypeVar

from loguru import logger
from PySide6.QtWidgets import QCheckBox, QComboBox

from app.core.event_bus import EventBus
from app.models.operation_mode import OperationMode
from app.mods.mod_utils import get_mod_path_from_pfid
from app.windows.mixins._shared import ColumnIndex


class SelectionMixin:
    """Row selection and PFID operations for BaseModsPanel."""

    settings: Any
    editor_model: Any
    editor_table_view: Any

    T = TypeVar("T")

    def _row_is_checked(self, row: int) -> bool:
        checkbox = self.editor_table_view.indexWidget(
            self.editor_model.item(row, 0).index()
        )
        return isinstance(checkbox, QCheckBox) and checkbox.isChecked()

    def _get_selected_row_indices(self) -> set[int]:
        """
        Get the set of selected row indices.

        Returns:
            Set of row indices that are checked.
        """
        return {
            row
            for row in range(self.editor_model.rowCount())
            if self._row_is_checked(row)
        }

    def _run_for_selected_rows(self, fn: Callable[[int], "T"]) -> list["T"]:
        return [fn(row) for row in self._get_selected_row_indices()]

    def _get_selected_text_by_column(self, column: int) -> Callable[[int], str]:
        def __selected_text_by_column(row: int) -> str:
            item = self.editor_model.item(row, column)
            if item is None:
                return ""
            combo_box = self.editor_table_view.indexWidget(item.index())
            if not isinstance(combo_box, QComboBox):
                return item.text()
            else:
                return combo_box.currentText()

        return __selected_text_by_column

    def _resolve_mode_getter(
        self, mode: OperationMode | str | int
    ) -> Callable[[int], str]:
        """
        Resolve a mode value getter function for the given mode parameter.

        Handles multiple mode type representations (enum, string, int) and returns
        a callable that provides the mode value for any given row.

        Args:
            mode: Operation mode as OperationMode enum, string, or column index (int).

        Returns:
            A callable that takes a row index and returns the mode string value.
        """
        if isinstance(mode, OperationMode):
            # Return constant function for enum mode
            mode_value = mode.value
            return lambda _: mode_value
        elif isinstance(mode, int):
            # Return column text getter for int (column index)
            return self._get_selected_text_by_column(mode)
        else:
            # Return constant function for string mode
            return lambda _: mode

    def _update_mods_from_table(
        self,
        pfid_column: int,
        mode: OperationMode,
        steamworks_cmd: str = "",
        completed: Callable[[], None] | None = None,
    ) -> None:
        """
        Update mods from table by collecting PFIDs and triggering appropriate operations.

        Filters out empty Publish File IDs which can occur when MissingModsPrompt
        doesn't have published_file_id for mods in the table. This prevents crashes
        in steamworks API calls.

        Args:
            pfid_column: Column index for Publish File IDs
            mode: Operation mode (OperationMode.STEAMCMD or OperationMode.STEAM)
            steamworks_cmd: Steamworks command to execute (only used when mode is STEAM).
                Valid values: "subscribe", "resubscribe", "unsubscribe".
                Ignored for OperationMode.STEAMCMD.
            completed: Optional callback to run on completion
        """
        # Check for mods without Publish Field ID and notify user if needed
        self._check_missing_publish_field_id_notification()

        steamcmd_pfids, steam_pfids = self._collect_pfids_by_mode(pfid_column, mode)
        filtered_steamcmd_pfids = self._filter_empty_pfids(steamcmd_pfids)

        if filtered_steamcmd_pfids:
            self._delete_selected_mods(pfid_column, OperationMode.STEAMCMD)
            EventBus().do_steamcmd_download.emit(filtered_steamcmd_pfids)

        if steam_pfids:
            self._emit_steamworks_api_call(steamworks_cmd, steam_pfids)

        if completed:
            completed()

        # Close the panel window after triggering operations
        # Don't close AcfLogReader (it's a persistent view, not a dialog)
        if self.__class__.__name__ != "AcfLogReader":
            self.close()  # type: ignore[attr-defined]

    def _collect_pfids_by_mode(
        self, pfid_column: int, mode: OperationMode
    ) -> tuple[list[str], list[str]]:
        pfid_fn = self._get_selected_text_by_column(pfid_column)
        pfids = [(pfid, mode) for pfid in self._run_for_selected_rows(pfid_fn)]

        steamcmd_pfids = [pfid for pfid, m in pfids if m == OperationMode.STEAMCMD]
        steam_pfids = [pfid for pfid, m in pfids if m == OperationMode.STEAM]
        return steamcmd_pfids, steam_pfids

    def _filter_empty_pfids(self, pfids: list[str]) -> list[str]:
        """
        Filter out empty Publish File IDs from the list.

        Args:
            pfids: List of PFID strings to filter

        Returns:
            List of non-empty PFID strings
        """
        return [pfid for pfid in pfids if pfid.strip()]

    def _emit_steamworks_api_call(self, command: str, steam_pfids: list[str]) -> None:
        """
        Emit steamworks API call with the given command and PFIDs.

        Converts PFIDs to integers and filters out empty values. All calls are routed
        through the animated handler for consistent UI feedback, validation, and safety checks.

        Args:
            command: Steamworks command to execute (subscribe, resubscribe, unsubscribe, launch_game_process, etc.)
            steam_pfids: List of Publish File ID strings to process
        """
        if not command:
            logger.warning("Attempted to emit steamworks API call with empty command")
            return

        filtered_pfids = [int(pfid) for pfid in steam_pfids if pfid.strip()]

        if not filtered_pfids:
            return

        logger.warning(
            f"Queuing '{command}' action for {len(filtered_pfids)} mods via Steamworks API"
        )
        EventBus().do_steamworks_api_call.emit([command, filtered_pfids])

    def _create_update_callback(
        self,
        pfid_column: int,
        mode: OperationMode,
        steamworks_cmd: str | None = None,
        completion_callback: Callable[[], None] | None = None,
    ) -> Callable[[], None]:
        """
        Factory method for creating mod update operation callbacks.

        Args:
            pfid_column: Column index for Publish File IDs
            mode: Operation mode (OperationMode.STEAMCMD or OperationMode.STEAM)
            steamworks_cmd: Steamworks command to execute (only used for STEAM mode).
                Valid values: "subscribe", "resubscribe", "unsubscribe"
            completion_callback: Optional callback to run after completion

        Returns:
            Callback function for update button
        """
        # Use provided steamworks_cmd or empty string (only used for STEAM mode)
        cmd = steamworks_cmd or ""
        return partial(
            self._update_mods_from_table,
            pfid_column,
            mode,
            cmd,
            completed=completion_callback,
        )

    def _delete_selected_mods(
        self, pfid_column: int, mode: OperationMode | str | int
    ) -> None:
        delete_before_update_state = self.settings.steamcmd_delete_before_update
        if delete_before_update_state:
            pfid_fn = self._get_selected_text_by_column(pfid_column)
            get_mode = self._resolve_mode_getter(mode)

            pfid_mode_pairs = self._run_for_selected_rows(
                lambda row: (pfid_fn(row), get_mode(row))
            )
            for pfid, mod_mode in pfid_mode_pairs:
                if mod_mode == OperationMode.STEAMCMD.value:
                    mod_path = get_mod_path_from_pfid(pfid)
                    if mod_path and os.path.exists(mod_path):
                        try:
                            shutil.rmtree(mod_path)
                        except Exception as e:
                            logger.error(
                                f"Error deleting mod directory {mod_path}: {e}"
                            )

    def _refresh_metadata_and_panel(self) -> None:
        """
        Standard refresh method called manually or after deletion operations.
        Refreshes the metadata cache and repopulates the table.

        This refreshes the metadata cache and repopulates the table with the updated mod data.
        ``_populate_from_metadata`` is triggered automatically via
        ``metadata_refreshed`` signal.
        """
        logger.warning("Refreshing metadata and repopulating table")
        # Refresh the metadata to reflect deletion changes
        self.metadata_controller.refresh_metadata()  # type: ignore[attr-defined]

    def _check_missing_publish_field_id_notification(self) -> None:
        """
        Check if selected mods are missing Publish Field IDs and show notification.
        Works with all BaseModsPanel subclasses by checking for empty published_file_id in table data.
        """
        selected_indices = self._get_selected_row_indices()
        if not selected_indices:
            return

        # Check if subclass has missing_publishfieldid_mods attribute (for explicit tracking)
        missing_publishfieldid_mods = getattr(self, "missing_publishfieldid_mods", None)
        use_explicit_mode = missing_publishfieldid_mods is not None

        missing_pfid_mods = [
            self.editor_model.item(row, 1).text()
            for row in selected_indices
            if self._row_has_missing_pfid(
                row, missing_publishfieldid_mods, use_explicit_mode
            )
            and self.editor_model.item(row, 1) is not None
        ]

        if missing_pfid_mods:
            self._show_missing_pfid_notification(missing_pfid_mods)

    def _row_has_missing_pfid(
        self,
        row: int,
        missing_publishfieldid_mods: list[str] | None,
        use_explicit_mode: bool,
    ) -> bool:
        """Check if a mod at given row has missing Publish Field ID."""
        if use_explicit_mode:
            key = self._get_key_from_row(row)  # type: ignore[attr-defined]
            return bool(
                key
                and missing_publishfieldid_mods
                and key in missing_publishfieldid_mods
            )
        else:
            pfid_item = self.editor_model.item(row, ColumnIndex.PUBLISHED_FILE_ID.value)
            return bool(pfid_item and not pfid_item.text().strip())

    def _show_missing_pfid_notification(self, missing_pfid_mods: list[str]) -> None:
        """Show notification about mods without Publish Field ID."""
        show_message = getattr(self, "_show_message", None)
        if not show_message:
            return

        mod_list = "\n".join([f"• {name}" for name in missing_pfid_mods])
        message = (
            "The following selected mods do not have a Publish Field ID "
            "and cannot be updated via Steam Workshop:\n\n"
            f"{mod_list}\n\n"
            "Only mods with valid Publish Field IDs will be updated."
        )
        show_message("Missing Publish Field ID", message, "warning")
