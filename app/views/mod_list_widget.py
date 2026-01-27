from typing import cast

from loguru import logger
from PySide6.QtCore import QEvent, QItemSelection, QObject, Qt, Signal
from PySide6.QtGui import (
    QCursor,
    QDropEvent,
    QFocusEvent,
    QKeyEvent,
    QKeySequence,
    QResizeEvent,
)
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QMenu

from app.controllers.metadata_controller import MetadataController
from app.models.settings import Settings
from app.sort.mod_sorting import ModsPanelSortKey
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.views.deletion_menu import ModDeletionMenu
from app.views.mixins.colors_tags_mixin import ColorsTagsMixin
from app.views.mixins.context_menu_mixin import ContextMenuMixin
from app.views.mixins.divider_mixin import DividerMixin
from app.views.mixins.errors_warnings_mixin import ErrorsWarningsMixin
from app.views.mixins.list_item_mixin import ListItemMixin


class ModListWidget(  # pyright: ignore[reportIncompatibleMethodOverride]
    ContextMenuMixin,
    DividerMixin,
    ListItemMixin,
    ErrorsWarningsMixin,
    ColorsTagsMixin,
    QListWidget,
):
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

    def eventFilter(self, object: QObject | None, event: QEvent) -> bool:
        """
        Forward the per-item context-menu event filter to the
        ContextMenuMixin implementation. Declared here (rather than letting
        the mixin override it directly) so that ``QListWidget`` stays last in
        the base tuple, keeping PySide's cooperative ``__init__`` order correct.
        """
        return ContextMenuMixin.eventFilter(self, cast(QObject, object), event)

    def mod_double_clicked(self, item: CustomListWidgetItem) -> None:
        """
        Method to handle double clicking on a row.
        """
        data = item.data(Qt.ItemDataRole.UserRole)
        if getattr(data, "is_divider", False):
            self.toggle_divider_collapse(data.uuid)
            return
        self.key_press_signal.emit("DoubleClick")
