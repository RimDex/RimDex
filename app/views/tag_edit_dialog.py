from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import Settings
from app.utils.aux_db_utils import auxdb_get_all_tags


class TagEditDialog(QDialog):
    def __init__(
        self,
        settings: Settings,
        title: str,
        existing_selected_tags: set[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.existing_selected_tags = existing_selected_tags or set()

        self.setObjectName("TagEditDialog")
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setMinimumHeight(360)

        self.dialog_layout = QVBoxLayout()

        self.info_label = QLabel(
            self.tr("Select existing tags and/or enter new tags separated by commas:")
        )
        self.info_label.setObjectName("TagEditDialogLabel")
        self.info_label.setWordWrap(True)
        self.dialog_layout.addWidget(self.info_label)

        self.new_tags_input = QLineEdit()
        self.new_tags_input.setObjectName("TagEditDialogInput")
        self.new_tags_input.setPlaceholderText(self.tr("new-tag, qol, framework"))
        self.new_tags_input.textChanged.connect(self._filter_tags)
        self.dialog_layout.addWidget(self.new_tags_input)

        self.tags_list = QListWidget()
        self.tags_list.setObjectName("TagEditDialogList")
        self.tags_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.dialog_layout.addWidget(self.tags_list)

        self.buttons_layout = QHBoxLayout()

        self.select_all_button = QPushButton(self.tr("Select all"))
        self.select_all_button.setObjectName("TagEditDialogButton")
        self.select_none_button = QPushButton(self.tr("Select none"))
        self.select_none_button.setObjectName("TagEditDialogButton")
        self.ok_button = QPushButton(self.tr("OK"))
        self.ok_button.setObjectName("TagEditDialogButton")
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.setObjectName("TagEditDialogButton")

        self.select_all_button.clicked.connect(self.select_all)
        self.select_none_button.clicked.connect(self.select_none)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.buttons_layout.addWidget(self.select_all_button)
        self.buttons_layout.addWidget(self.select_none_button)
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)

        self.dialog_layout.addLayout(self.buttons_layout)
        self.setLayout(self.dialog_layout)

        self.populate_tags()

    def populate_tags(self) -> None:
        try:
            tags = auxdb_get_all_tags(self.settings)
        except Exception as e:
            logger.debug(f"Unable to load existing tags: {e}")
            tags = []

        for tag in tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if tag in self.existing_selected_tags
                else Qt.CheckState.Unchecked
            )
            self.tags_list.addItem(item)

    def _filter_tags(self, text: str) -> None:
        for index in range(self.tags_list.count()):
            item = self.tags_list.item(index)
            item.setHidden(text not in item.text() if text else False)

    def select_all(self) -> None:
        for index in range(self.tags_list.count()):
            self.tags_list.item(index).setCheckState(Qt.CheckState.Checked)

    def select_none(self) -> None:
        for index in range(self.tags_list.count()):
            self.tags_list.item(index).setCheckState(Qt.CheckState.Unchecked)

    def selected_tags(self) -> list[str]:
        selected = set()

        for index in range(self.tags_list.count()):
            item = self.tags_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected.add(item.text().strip().lower())

        manual_tags = [
            tag.strip().lower()
            for tag in self.new_tags_input.text().split(",")
            if tag.strip()
        ]
        selected.update(manual_tags)

        return sorted(selected)
