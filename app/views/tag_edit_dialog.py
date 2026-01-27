from typing import cast

from loguru import logger
from PySide6.QtCore import QEvent, QKeyCombination, QObject, Qt
from PySide6.QtGui import QKeyEvent
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
from app.mods.aux_db_utils import auxdb_get_all_tags


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

        self.tags_text_input = QLineEdit()
        self.tags_text_input.setObjectName("TagEditDialogInput")
        self.tags_text_input.setPlaceholderText(self.tr("new-tag, qol, framework"))
        self.tags_text_input.textChanged.connect(self.filter_tags_list)
        self.tags_text_input.returnPressed.connect(self.upsert_typed_tag)
        self.tags_text_input.installEventFilter(self)
        self.dialog_layout.addWidget(self.tags_text_input)

        self.tags_list = QListWidget(sortingEnabled=True)
        self.tags_list.setObjectName("TagEditDialogList")
        self.tags_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tags_list.installEventFilter(self)
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

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            key = cast(QKeyEvent, event).key()
            if obj is self.tags_text_input and (
                key in [Qt.Key.Key_Down, Qt.Key.Key_Tab]
            ):
                self.tags_list.setFocus(Qt.FocusReason.ShortcutFocusReason)
                return True
            if (
                obj is self.tags_list
                and key == Qt.Key.Key_Up
                and self.tags_list.currentRow() == 0
            ):
                self.tags_text_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.keyCombination() in [
            QKeyCombination(Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Enter),
            QKeyCombination(Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Return),
        ]:
            # On Alt-Enter or Alt-Return key press, accept the current changes.
            self.accept()
            return

        if self.tags_text_input.hasFocus() and event.key() in [
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ]:
            # On Enter or Return key press while focused on the tag text input field,
            # upsert the current tag in the text input field.
            self.upsert_typed_tag()
            return
        if self.tags_list.hasFocus() and event.key() in [
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ]:
            # On Enter or Return key press while focused on the tags list, toggle the
            # selection of the current item.
            self.toggle_tag_item_selection(self.tags_list.currentItem())
            return

        super().keyPressEvent(event)

    def toggle_tag_item_selection(self, tag_item: QListWidgetItem) -> None:
        """
        Toggle the selection of the current tag item in the tags list.

        :param tag_item: Tag item to toggle the selection for.
        """
        tag_item.setSelected(not tag_item.isSelected())

    def upsert_typed_tag(self) -> None:
        """
        Upsert the current tag in the tag input (triggered by the Enter key or typing comma).

        If the typed tag exactly matches an existing tag, it is selected.
        Otherwise, a new pre-selected tag item is added to the list.
        The input field is then cleared so the user can type the next tag.
        """
        for tag in self.tags_text_input.text().split(","):
            tag = tag.strip().lower()
            if not tag:
                continue

            matched_items = self.tags_list.findItems(tag, Qt.MatchFlag.MatchExactly)
            if matched_items:
                assert len(matched_items) == 1, (
                    "Expected exactly one matched item matching exactly the typed tag"
                )
                self.toggle_tag_item_selection(matched_items[0])
            else:
                item_new = QListWidgetItem(tag)
                self.tags_list.addItem(item_new)
                item_new.setSelected(True)

        self.tags_text_input.clear()

    def filter_tags_list(self) -> None:
        """
        Filter the tag list to only items containing the current typed text as a substring.

        Adds a new tag when the user types a comma.
        """
        typed_text = self.tags_text_input.text().strip()
        if typed_text.endswith(","):
            self.upsert_typed_tag()
            return

        typed_tags = [
            tag.strip().lower() for tag in typed_text.split(",") if tag.strip()
        ]

        if not typed_tags:
            for index in range(self.tags_list.count()):
                self.tags_list.item(index).setHidden(False)
            return

        for index in range(self.tags_list.count()):
            item = self.tags_list.item(index)
            item.setHidden(
                not any(
                    typed_tag in item.text().strip().lower() for typed_tag in typed_tags
                )
            )

    def populate_tags(self) -> None:
        try:
            tags = auxdb_get_all_tags(self.settings)
        except Exception as e:
            logger.debug(f"Unable to load existing tags: {e}")
            tags = []

        self.tags_list.addItems(tags)
        for index in range(self.tags_list.count()):
            item = self.tags_list.item(index)
            item.setSelected(item.text().strip().lower() in self.existing_selected_tags)

    def select_all(self) -> None:
        for index in range(self.tags_list.count()):
            self.tags_list.item(index).setSelected(True)

    def select_none(self) -> None:
        for index in range(self.tags_list.count()):
            self.tags_list.item(index).setSelected(False)

    def selected_tags(self) -> list[str]:
        selected = set()

        for index in range(self.tags_list.count()):
            item = self.tags_list.item(index)
            if item.isSelected():
                selected.add(item.text().strip().lower())

        # Include any tag still typed into the input field but not yet committed
        # via Enter/comma, so it is not lost when OK is clicked with the mouse.
        for tag in self.tags_text_input.text().split(","):
            tag = tag.strip().lower()
            if tag:
                selected.add(tag)

        return sorted(selected)
