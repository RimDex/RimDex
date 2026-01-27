from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.ui.widgets.gui_info import GUIInfo


class DatabaseBuilderDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(self.tr("Database Builder"))
        self.setObjectName("databaseBuilderPanel")
        self.setMinimumWidth(600)
        self.setModal(False)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # "When building the database:" radio buttons
        when_building_database_label = QLabel(self.tr("When building the database:"))
        when_building_database_label.setFont(GUIInfo().emphasis_font)
        main_layout.addWidget(when_building_database_label)

        self.db_builder_include_all_radio = QRadioButton(
            self.tr("Get PublishedFileIDs from locally installed mods.")
        )
        main_layout.addWidget(self.db_builder_include_all_radio)

        explanatory_label = QLabel(
            self.tr(
                "Mods you wish to update must be installed, "
                "as the initial DB is built including data from mods' About.xml files."
            )
        )
        main_layout.addWidget(explanatory_label)

        self.db_builder_include_no_local_radio = QRadioButton(
            self.tr("Get PublishedFileIDs from the Steam Workshop.")
        )
        main_layout.addWidget(self.db_builder_include_no_local_radio)

        explanatory_label = QLabel(
            self.tr(
                "Mods to be updated don't have to be installed, "
                "as the initial DB is built by scraping the Steam Workshop."
            )
        )
        main_layout.addWidget(explanatory_label)

        # Checkboxes
        main_layout.addWidget(QLabel(""))

        self.db_builder_query_dlc_checkbox = QCheckBox(
            self.tr("Query DLC dependency data with Steamworks API")
        )
        main_layout.addWidget(self.db_builder_query_dlc_checkbox)

        self.db_builder_update_instead_of_overwriting_checkbox = QCheckBox(
            self.tr("Update database instead of overwriting")
        )
        main_layout.addWidget(self.db_builder_update_instead_of_overwriting_checkbox)

        # Text fields
        group_box = QGroupBox()
        main_layout.addWidget(group_box)

        grid_group_layout = QGridLayout()
        group_box.setLayout(grid_group_layout)

        steam_api_key_label = QLabel(self.tr("Steam API key:"))
        grid_group_layout.addWidget(steam_api_key_label, 1, 0)

        self.db_builder_steam_api_key = QLineEdit()
        self.db_builder_steam_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        grid_group_layout.addWidget(self.db_builder_steam_api_key, 1, 1)

        grid_group_layout.setColumnStretch(0, 0)
        grid_group_layout.setColumnStretch(1, 1)

        main_layout.addStretch()

        # "Download all workshop mods via" buttons
        item_layout = QHBoxLayout()
        main_layout.addLayout(item_layout)

        item_layout.addStretch()

        item_label = QLabel(self.tr("Download all published Workshop mods via:"))
        item_layout.addWidget(item_label)

        self.db_builder_download_all_mods_via_steamcmd_button = QPushButton(
            self.tr("SteamCMD")
        )
        item_layout.addWidget(self.db_builder_download_all_mods_via_steamcmd_button)

        self.db_builder_download_all_mods_via_steam_button = QPushButton(
            self.tr("Steam")
        )
        self.db_builder_download_all_mods_via_steam_button.setFixedWidth(
            self.db_builder_download_all_mods_via_steamcmd_button.sizeHint().width()
        )
        item_layout.addWidget(self.db_builder_download_all_mods_via_steam_button)

        # Compare/Merge/Build database buttons
        item_layout = QHBoxLayout()
        main_layout.addLayout(item_layout)

        item_layout.addStretch()

        self.db_builder_compare_databases_button = QPushButton(
            self.tr("Compare Databases")
        )
        item_layout.addWidget(self.db_builder_compare_databases_button)

        self.db_builder_merge_databases_button = QPushButton(self.tr("Merge Databases"))
        self.db_builder_merge_databases_button.setFixedWidth(
            self.db_builder_compare_databases_button.sizeHint().width()
        )
        item_layout.addWidget(self.db_builder_merge_databases_button)

        self.db_builder_build_database_button = QPushButton(self.tr("Build Database"))
        self.db_builder_build_database_button.setFixedWidth(
            self.db_builder_compare_databases_button.sizeHint().width()
        )
        item_layout.addWidget(self.db_builder_build_database_button)
