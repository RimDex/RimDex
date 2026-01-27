from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

from app.core.event_bus import EventBus
from app.models.settings import Settings
from app.ui.dialogue import BinaryChoiceDialog
from app.views.database_builder_dialog import DatabaseBuilderDialog


class DatabaseBuilderController(QObject):
    def __init__(self, settings: Settings) -> None:
        super().__init__()

        self.settings = settings
        self.dialog = DatabaseBuilderDialog()

        self.connect_signals()
        self._update_view_from_model()

    def connect_signals(self) -> None:
        self.dialog.db_builder_download_all_mods_via_steamcmd_button.clicked.connect(
            self._on_download_all_via_steamcmd
        )
        self.dialog.db_builder_download_all_mods_via_steam_button.clicked.connect(
            self._on_download_all_via_steam
        )
        self.dialog.db_builder_compare_databases_button.clicked.connect(
            self._on_compare_databases
        )
        self.dialog.db_builder_merge_databases_button.clicked.connect(
            self._on_merge_databases
        )
        self.dialog.db_builder_build_database_button.clicked.connect(
            self._on_build_database
        )

    def show(self) -> None:
        self._update_view_from_model()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _update_view_from_model(self) -> None:
        if self.settings.db_builder_include == "all_mods":
            self.dialog.db_builder_include_all_radio.setChecked(True)
        elif self.settings.db_builder_include == "no_local":
            self.dialog.db_builder_include_no_local_radio.setChecked(True)
        self.dialog.db_builder_query_dlc_checkbox.setChecked(
            self.settings.build_steam_database_dlc_data
        )
        self.dialog.db_builder_update_instead_of_overwriting_checkbox.setChecked(
            self.settings.build_steam_database_update_toggle
        )
        self.dialog.db_builder_steam_api_key.setText(self.settings.steam_apikey)

    def _save_settings(self) -> None:
        if self.dialog.db_builder_include_all_radio.isChecked():
            self.settings.db_builder_include = "all_mods"
        elif self.dialog.db_builder_include_no_local_radio.isChecked():
            self.settings.db_builder_include = "no_local"
        self.settings.build_steam_database_dlc_data = (
            self.dialog.db_builder_query_dlc_checkbox.isChecked()
        )
        self.settings.build_steam_database_update_toggle = (
            self.dialog.db_builder_update_instead_of_overwriting_checkbox.isChecked()
        )
        self.settings.steam_apikey = self.dialog.db_builder_steam_api_key.text()
        self.settings.save()

    @Slot()
    def _on_download_all_via_steamcmd(self) -> None:
        confirm_diag = BinaryChoiceDialog(
            "Confirm Build Database (SteamCMD)",
            "Are you sure you want to download all mods via SteamCMD and build the Steam Workshop database?",
            (
                "For most users this is not necessary as the GitHub SteamDB is adequate. Building the database may take a long time. "
                "This process downloads all mods (not just your own) from the Steam Workshop. "
                "This can be a large amount of data and take a long time. Are you sure you want to continue?"
            ),
            icon=QMessageBox.Icon.Warning,
        )

        if not confirm_diag.exec_is_positive():
            return

        self._save_settings()
        EventBus().do_download_all_mods_via_steamcmd.emit()
        self.dialog.close()

    @Slot()
    def _on_download_all_via_steam(self) -> None:
        confirm_diag = BinaryChoiceDialog(
            "Confirm Build Database (Steam Download)",
            "Are you sure you want to download all mods via Steam and build the Steam Workshop database?",
            (
                "For most users this is not necessary as the GitHub SteamDB is adequate. Building the database may take a long time. "
                "This process will subscribe to and download all mods from the Steam Workshop (not just your own). "
                "This can be a large amount of data and take a long time. Are you sure you want to continue?"
            ),
            icon=QMessageBox.Icon.Warning,
        )

        if not confirm_diag.exec_is_positive():
            return

        self._save_settings()
        EventBus().do_download_all_mods_via_steam.emit()
        self.dialog.close()

    @Slot()
    def _on_compare_databases(self) -> None:
        self._save_settings()
        EventBus().do_compare_steam_workshop_databases.emit()
        self.dialog.close()

    @Slot()
    def _on_merge_databases(self) -> None:
        self._save_settings()
        EventBus().do_merge_steam_workshop_databases.emit()
        self.dialog.close()

    @Slot()
    def _on_build_database(self) -> None:
        confirm_diag = BinaryChoiceDialog(
            title="Confirm Build Database",
            text="Are you sure you want to build the Steam Workshop database?",
            information=(
                "For most users this is not necessary as the GitHub SteamDB is adequate. Building the database may take a long time. "
                "Depending on your settings, it may also crawl through the entirety of the steam workshop via the webAPI. "
                "This can be a large amount of data and take a long time. Are you sure you want to continue?"
            ),
            icon=QMessageBox.Icon.Warning,
        )

        if not confirm_diag.exec_is_positive():
            return

        self._save_settings()
        EventBus().do_build_steam_workshop_database.emit()
        self.dialog.close()
