"""List-item / widget management mixin for ModListWidget.

Holds the item-and-widget lifecycle: lazy widget creation, visibility
tracking, row insert/remove handlers, the full list rebuild, and the
row-replacement helper used during drag/drop.
"""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QWidget

from app.controllers.metadata_db_controller import AuxMetadataController
from app.models.metadata.metadata_structure import AboutXmlMod
from app.sort.mod_sorting import ModsPanelSortKey, sort_paths
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.custom_list_widget_item_metadata import (
    CustomListWidgetItemMetadata,
    bulk_prefetch_item_metadata,
)
from app.ui.widgets.divider import is_divider_uuid
from app.views.divider_widget import DividerItemInner
from app.views.mixins._shared import ModListWidgetMixinBase
from app.views.mod_list_item_inner import ModListItemInner


class ListItemMixin(ModListWidgetMixinBase):
    """Item/widget lifecycle for ModListWidget."""

    def append_new_item(self, uuid: str) -> None:
        if uuid not in self.metadata_controller.mods_metadata:
            logger.error(f"Attempted to append item with uuid not in metadata: {uuid}")
            return

        mod = self.metadata_controller.get_mod(uuid)
        mod_path = str(mod.mod_path) if mod and mod.mod_path else uuid
        aux_metadata_controller = AuxMetadataController.get_or_create_cached_instance(
            self.settings.aux_db_path
        )
        with aux_metadata_controller.Session() as aux_metadata_session:
            aux_metadata_controller.get_or_create(aux_metadata_session, mod_path)
            aux_metadata_controller.update(
                aux_metadata_session, mod_path, outdated=False
            )
            data = CustomListWidgetItemMetadata(
                path=uuid,
                list_type=self.list_type,
                aux_metadata_controller=aux_metadata_controller,
                aux_metadata_session=aux_metadata_session,
                settings=self.settings,
            )
            data.__dict__["show_tags"] = self.show_tags
        # Create item without a parent first so we can set data before adding to the list.
        # This ensures handle_rows_inserted (connected via QueuedConnection) sees the data
        # when it fires after addItem, and can correctly track the UUID in self.paths.
        item = CustomListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        self.addItem(item)

    def get_all_mod_list_items(self) -> list[CustomListWidgetItem]:
        """
        This gets all modlist items (excludes dividers).

        :return: List of all modlist items as CustomListWidgetItem
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                continue
            mod_list_items.append(item)
        return mod_list_items

    def get_all_loaded_mod_list_items(self) -> list[ModListItemInner]:
        """
        This gets all modlist items as ModListItemInner.
        Mods that have not been loaded or lazy loaded will not be returned.

        :return: List of all modlist items as ModListItemInner
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            if isinstance(widget, ModListItemInner):
                mod_list_items.append(widget)
        return mod_list_items

    def get_all_toggled_mod_list_items(self) -> list[CustomListWidgetItem]:
        """
        This returns all modlist items that have their warnings toggled.

        :return: List of all toggled modlist items as CustomListWidgetItem
        """
        mod_list_items = []
        for index in range(self.count()):
            item = self.item(index)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(item_data, "is_divider", False):
                continue
            if item_data["warning_toggled"]:
                mod_list_items.append(item)
        return mod_list_items

    def get_all_loaded_and_toggled_mod_list_items(self) -> list[ModListItemInner]:
        """
        This returns all modlist items that have their warnings toggled.
        Mods that have not been loaded or lazy loaded will not be returned.

        :return: List of all toggled modlist items as ModListItemInner
        """
        mod_list_items = []
        for item in self.get_all_toggled_mod_list_items():
            widget = self.itemWidget(item)
            if isinstance(widget, ModListItemInner):
                mod_list_items.append(widget)
        return mod_list_items

    def check_item_visible(self, item: CustomListWidgetItem) -> bool:
        # Determines if the item is currently visible in the viewport.
        rect = self.visualItemRect(item)
        return rect.top() < self.viewport().height() and rect.bottom() > 0

    def create_widget_for_item(self, item: CustomListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            logger.debug("Attempted to create widget for item with None data")
            return

        if getattr(data, "is_divider", False):
            divider_widget = DividerItemInner(
                uuid=data.uuid, name=data.name, collapsed=data.collapsed
            )
            divider_widget.toggle_signal.connect(self.toggle_divider_collapse)
            item.setSizeHint(divider_widget.sizeHint())
            self.setItemWidget(item, divider_widget)
            self._update_single_divider_mod_count(item)
            return

        errors_warnings = data["errors_warnings"]
        errors = data["errors"]
        warnings = data["warnings"]
        filtered = data["filtered"]
        invalid = data["invalid"]
        mismatch = data["mismatch"]
        alternative = data["alternative"]
        uuid = data["path"]
        mod_color = data["mod_color"]
        if uuid:
            widget = ModListItemInner(
                errors_warnings=errors_warnings,
                errors=errors,
                warnings=warnings,
                filtered=filtered,
                invalid=invalid,
                mismatch=mismatch,
                alternative=alternative,
                settings=self.settings,
                path=uuid,
                mod_color=mod_color,
                metadata_controller=self.metadata_controller,
            )
            widget.toggle_warning_signal.connect(self.toggle_warning)
            widget.toggle_error_signal.connect(self.toggle_warning)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

            # Apply translation status if enabled
            if self.show_translation_status:
                _mod_tr = self.metadata_controller.get_mod(uuid)
                pkg_id = (
                    str(_mod_tr.package_id) if isinstance(_mod_tr, AboutXmlMod) else ""
                )
                has_translation = pkg_id in self.translation_lookup
                widget.update_translation_status(has_translation)

            # Ensure initial icon states reflect current item data
            widget.repolish(item)

    def check_widgets_visible(self) -> None:
        # This function checks the visibility of each item and creates a widget if the item is visible and not already setup.
        indexes = self.get_visible_indexes()
        for idx in indexes:
            item = self.item(idx)
            # Check for visible item without a widget set
            if item and self.itemWidget(item) is None:
                self.create_widget_for_item(item)

    def get_visible_indexes(self) -> set[int]:
        """This function returns the set of indexes for items that are currently visible in the viewport."""
        indexes: set[int] = set()

        top_index = self.indexAt(self.viewport().rect().topLeft())
        if not top_index.isValid():
            return indexes

        row = top_index.row()
        model = self.model()

        while row < model.rowCount():
            idx = model.index(row, 0)
            rect = self.visualRect(idx)
            if rect.top() > self.viewport().height():
                break
            elif rect.bottom() >= 0:
                indexes.add(row)

            row += 1

        return indexes

    def handle_item_data_changed(self, item: CustomListWidgetItem) -> None:
        """
        This slot is called when an item's data changes
        """
        widget = self.itemWidget(item)
        if widget is not None and isinstance(widget, ModListItemInner):
            widget.repolish(item)

    def handle_other_list_row_added(self, uuid: str) -> None:
        """
        When a mod is moved from Inactive->Active, the uuid is removed from the Inactive list.

        When a mod is moved from Active->Inactive, the uuid is removed from the Active list.
        """
        if uuid in self.paths:
            self.paths.remove(uuid)

    def handle_rows_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        """
        This slot is called when rows are inserted.

        When mods are inserted into the mod list, either through the
        `recreate_mod_list` method above or automatically through dragging
        and dropping on the UI, this function is called. For single-item
        inserts, which happens through the above method or through dragging
        and dropping individual mods, `first` equals `last` and the below
        loop is just run once. In this loop, a custom widget is created,
        which displays the text, icons, etc, and is added to the list item.

        For dragging and dropping multiple items, the loop is run multiple
        times. Importantly, even for multiple items, the number of list items
        is set BEFORE the loop starts running, e.g. if we were dragging 3 mods
        onto a list of 100 mods, this method is called once and by the start
        of this method, `self.count()` is already 103; there are 3 "empty"
        list items that do not have widgets assigned to them.

        However, inserting the initial `n` mods with `recreate_mod_list` has
        an inefficiency: it is only able to insert one at a time. This means
        this method is called `n` times for the first `n` mods.
        One optimization here (saving about 1 second with a 200 mod list) is
        to not emit the list update signal until the number of widgets is
        equal to the number of items. If widgets < items, that means
        widgets are still being added. Only when widgets == items does it mean
        we are done with adding the initial set of mods. We can do this
        by keeping track of the number of widgets currently loaded in the list
        through a set of UUIDs which we can compare to the number of items
        directly, as this set will equate to the items in the list.

        :param parent: parent to get rows under (not used)
        :param first: index of first item inserted
        :param last: index of last item inserted
        """
        # Loop through the indexes of inserted items, load widgets if not
        # already loaded. Each item index corresponds to a UUID index.
        for idx in range(first, last + 1):
            item = self.item(idx)
            if not isinstance(item, CustomListWidgetItem):
                # Convert to CustomListWidgetItem
                item = CustomListWidgetItem(item)
                self.replaceItemAtIndex(idx, item)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data is None:
                    logger.debug(f"Attempted to insert item with None data. Idx: {idx}")
                    continue
                if getattr(data, "is_divider", False):
                    uuid = data["path"]
                    self.paths.insert(idx, uuid)
                    self.create_widget_for_item(item)
                    continue
                # Ensure the item's persisted list_type matches the destination list after insertion
                try:
                    data["list_type"] = self.list_type
                    item.setData(Qt.ItemDataRole.UserRole, data)
                except Exception:
                    pass
                uuid = data["path"]
                self.paths.insert(idx, uuid)
                self.item_added_signal.emit(uuid)
        # Update list signal if all items are loaded
        if len(self.paths) == self.count():
            # Update list with the number of items
            logger.debug(
                f"Emitting {self.list_type} list update signal after rows inserted [{self.count()}]"
            )
            self.list_update_signal.emit(str(self.count()))

    def handle_rows_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        """
        This slot is called when rows are removed.
        Emit a signal with the count of objects remaining to update
        the count label. For some reason this seems to call twice on
        dragging and dropping multiple mods.

        The condition is required because when we `do_clear` or `do_import`,
        the existing list needs to be "wiped", and this counts as `n`
        calls to this function. When this happens, `self.paths` is
        cleared and `self.count()` remains at the previous number, so we can
        just check for equality here.

        :param parent: parent to get rows under (not used)
        :param first: index of first item removed (not used)
        :param last: index of last item removed (not used)
        """
        # Update list signal if all items are loaded
        if len(self.paths) == self.count():
            # Update list with the number of items
            logger.debug(
                f"Emitting {self.list_type} list update signal after rows removed [{self.count()}]"
            )
            self.list_update_signal.emit(str(self.count()))

    def get_item_widget_at_index(self, idx: int) -> QWidget | None:
        item = self.item(idx)
        if item:
            return self.itemWidget(item)
        return None

    def rebuild_item_widget_from_uuid(self, uuid: str) -> None:
        if is_divider_uuid(uuid):
            return
        item_index = self.paths.index(uuid)
        item = self.item(item_index)
        logger.debug(f"Rebuilding widget for item {uuid} at index {item_index}")
        # Destroy the item's previous widget immediately. Recreate if the item is visible.
        widget = self.itemWidget(item)
        if widget:
            self.removeItemWidget(item)
        # If it is visible, create a new widget. Otherwise, allow lazy loading to handle this.
        if self.check_item_visible(item):
            self.create_widget_for_item(item)
        # If the current item is selected, update the info panel
        if self.currentItem() == item:
            self.mod_info_signal.emit(uuid, item)

    def recreate_mod_list_and_sort(
        self,
        list_type: str,
        uuids: list[str],
        key: ModsPanelSortKey,
        descending: bool = False,
    ) -> None:
        """
        Reconstructs and sorts a mod list based on provided UUIDs and a sorting key.

        This method takes a list of mod UUIDs, sorts them according to the specified
        sorting key, and then recreates the mod list of the given type with the sorted order.

        Args:
            list_type (str): The type of mod list to recreate. ("Active", "Inactive")
            uuids (List[str]): The list of UUIDs representing the mods.
            key (ModsPanelSortKey): An enumeration value that determines the
                                     sorting criterion for the mods.
            descending (bool, optional): Whether to sort in descending order. Defaults to False.

        Returns:
            None
        """
        sorted_uuids = sort_paths(
            uuids,
            key=key,
            descending=descending,
            settings=self.settings,
        )
        self.recreate_mod_list(list_type, sorted_uuids, filtering=True)

    def recreate_mod_list(
        self, list_type: str, uuids: list[str], filtering: bool = False
    ) -> None:
        """
        Clear all mod items and add new ones from a dict.

        :param mods: dict of mod data
        :param filtering: if True, UUIDs are already sorted; skip sorting
        """
        logger.info(f"Internally recreating {list_type} mod list")
        # Skip sorting if UUIDs are already filtered/sorted (filtering=True)
        if not filtering:
            # Sort inactive mods using saved settings if enabled
            if list_type == "Inactive" and self.settings.save_inactive_mods_sort_state:
                sort_key = ModsPanelSortKey[self.settings.inactive_mods_sort_key]
                descending = self.settings.inactive_mods_sort_descending
                uuids = sort_paths(
                    uuids,
                    key=sort_key,
                    descending=descending,
                    settings=self.settings,
                )
            else:
                if list_type == "Inactive":
                    uuids = sort_paths(
                        uuids,
                        key=ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME,
                        descending=True,
                        settings=self.settings,
                    )
        # Disable updates and disconnect model signals during rebuild
        self.setUpdatesEnabled(False)
        # Temporarily disconnect model signals to avoid cascading updates and duplicate items
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass  # Signal not connected
        try:
            self.model().rowsAboutToBeRemoved.disconnect(self.handle_rows_removed)
        except TypeError:
            pass  # Signal not connected

        self.clear()
        self.paths = list()
        if uuids:  # Insert data...
            # Filter out dividers up-front so we can bulk-fetch real UUIDs
            real_uuids = [u for u in uuids if not is_divider_uuid(u)]

            aux_metadata_controller = (
                AuxMetadataController.get_or_create_cached_instance(
                    self.settings.aux_db_path
                )
            )
            # Single session + single aux query + single metadata pass
            with aux_metadata_controller.Session() as aux_metadata_session:
                aux_entries = aux_metadata_controller.get_all_by_paths(
                    aux_metadata_session, real_uuids
                )
                pre_fetched = bulk_prefetch_item_metadata(
                    self.metadata_controller, aux_entries, real_uuids
                )
                for uuid_key in real_uuids:
                    _mod = self.metadata_controller.get_mod(uuid_key)
                    mod_path = (
                        str(_mod.mod_path) if _mod and _mod.mod_path else uuid_key
                    )
                    aux_metadata_controller.get_or_create(
                        aux_metadata_session, mod_path
                    )
                    aux_metadata_controller.update(
                        aux_metadata_session, mod_path, outdated=False
                    )
                    item_data = CustomListWidgetItemMetadata(
                        path=uuid_key,
                        list_type=self.list_type,
                        settings=self.settings,
                        **pre_fetched[uuid_key],
                    )
                    item_data.__dict__["show_tags"] = self.show_tags
                    list_item = CustomListWidgetItem(self)
                    list_item.setData(Qt.ItemDataRole.UserRole, item_data)
                    self.addItem(list_item)
            # Set uuids list to match the widget after all items are added
            self.paths = list(uuids)

        else:  # ...unless we don't have mods, at which point reenable updates and exit
            self.setUpdatesEnabled(True)
            # Reconnect model signals
            self.model().rowsInserted.connect(
                self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
            )
            self.model().rowsAboutToBeRemoved.connect(
                self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
            )
            return

        # Reconnect model signals
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.model().rowsAboutToBeRemoved.connect(
            self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
        )
        # Enable updates and repaint
        self.setUpdatesEnabled(True)
        self.repaint()
        # Load visible widgets after rebuild completes
        self.check_widgets_visible()
        # Emit signal to update counts and errors/warnings
        self.list_update_signal.emit(str(self.count()))

    def replaceItemAtIndex(self, index: int, item: CustomListWidgetItem) -> None:
        """
        IMPORTANT: This is used to replace an item without triggering the rowsInserted signal and rowsAboutToBeRemoved signal.
        :param index: The index of the item to replace.
        :param item: The new item that will replace the old one.
        """
        # The rowsInserted signal should be removed from ALL slots and then reconnected to ALL slots.
        # This will have to be manually done below, unless we start tracking which slots that signal is connected to.

        # Check if the signal is connected before disconnecting
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass  # Signal was not connected
        try:
            self.model().rowsAboutToBeRemoved.disconnect(self.handle_rows_removed)
        except TypeError:
            pass  # Signal was not connected

        # Perform the replacement
        self.takeItem(index)
        self.insertItem(index, item)
        # Ensure the item's metadata reflects this list's type after replacement
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data is not None:
                data["list_type"] = self.list_type
                item.setData(Qt.ItemDataRole.UserRole, data)
        except Exception:
            pass

        # Reconnect to ALL slots
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.model().rowsAboutToBeRemoved.connect(
            self.handle_rows_removed, Qt.ConnectionType.QueuedConnection
        )
