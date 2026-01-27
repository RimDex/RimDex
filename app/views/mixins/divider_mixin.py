"""Divider helpers mixin for ModListWidget.

Holds the divider create/rename/toggle/remove logic and the collapse-state
tracking that keeps mods hidden under a collapsed divider in sync.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt

from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.divider import DividerData, generate_divider_uuid
from app.views.divider_widget import DividerItemInner
from app.views.mixins._shared import ModListWidgetMixinBase


class DividerMixin(ModListWidgetMixinBase):
    """Divider create/rename/toggle/remove + collapse-state tracking."""

    def add_divider(self, index: int, name: str) -> None:
        uuid = generate_divider_uuid()
        data = DividerData(uuid=uuid, name=name)
        item = CustomListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass
        self.insertItem(index, item)
        self.paths.insert(index, uuid)
        self.create_widget_for_item(item)
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.apply_collapse_states()
        self.list_update_signal.emit(str(self.count()))

    def remove_divider(self, uuid: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        # Expand hidden items first so they become visible
        next_div = self._find_next_divider_index(idx + 1)
        for i in range(idx + 1, next_div):
            self.item(i).setHidden(False)
        self.paths.pop(idx)
        self.takeItem(idx)
        self._update_divider_mod_counts()
        self.list_update_signal.emit(str(self.count()))

    def rename_divider(self, uuid: str, new_name: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        item = self.item(idx)
        data = item.data(Qt.ItemDataRole.UserRole)
        data.name = new_name
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_name(new_name)

    def toggle_divider_collapse(self, uuid: str) -> None:
        if uuid not in self.paths:
            return
        idx = self.paths.index(uuid)
        item = self.item(idx)
        data = item.data(Qt.ItemDataRole.UserRole)
        data.collapsed = not data.collapsed
        item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_collapsed(data.collapsed)
        next_div = self._find_next_divider_index(idx + 1)
        for i in range(idx + 1, next_div):
            self.item(i).setHidden(data.collapsed)
        self._update_single_divider_mod_count(item)

    def _find_next_divider_index(self, start: int) -> int:
        for i in range(start, self.count()):
            d = self.item(i).data(Qt.ItemDataRole.UserRole)
            if getattr(d, "is_divider", False):
                return i
        return self.count()

    def _update_single_divider_mod_count(self, item: CustomListWidgetItem) -> None:
        idx = self.row(item)
        if idx < 0:
            return
        next_div = self._find_next_divider_index(idx + 1)
        count = next_div - idx - 1
        widget = self.itemWidget(item)
        if isinstance(widget, DividerItemInner):
            widget.set_mod_count(count)

    def _update_divider_mod_counts(self) -> None:
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                self._update_single_divider_mod_count(item)

    def apply_collapse_states(self) -> None:
        """Hide/show items according to their preceding divider's collapsed state."""
        collapsed = False
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                collapsed = data.collapsed
                widget = self.itemWidget(item)
                if isinstance(widget, DividerItemInner):
                    widget.set_collapsed(collapsed)
            else:
                hidden_by_filter = getattr(data, "hidden_by_filter", False)
                item.setHidden(collapsed or hidden_by_filter)
        self._update_divider_mod_counts()

    def get_dividers_data(self) -> list[dict[str, Any]]:
        """Return serialisable divider info for persistence."""
        result = []
        for i in range(self.count()):
            item = self.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if getattr(data, "is_divider", False):
                result.append(
                    {
                        "uuid": data.uuid,
                        "name": data.name,
                        "collapsed": data.collapsed,
                        "index": i,
                    }
                )
        return result

    def restore_dividers(self, dividers: list[dict[str, Any]]) -> None:
        """Re-insert dividers at saved positions after a list rebuild."""
        if not dividers:
            return
        # Disconnect model signals to avoid handle_rows_inserted duplicating uuids
        try:
            self.model().rowsInserted.disconnect(self.handle_rows_inserted)
        except TypeError:
            pass
        sorted_dividers = sorted(dividers, key=lambda d: d.get("index", 0))
        for div in sorted_dividers:
            idx = min(div.get("index", 0), self.count())
            uuid = div.get("uuid", generate_divider_uuid())
            data = DividerData(
                uuid=uuid,
                name=div.get("name", ""),
                collapsed=div.get("collapsed", False),
            )
            item = CustomListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, data, avoid_emit=True)
            self.insertItem(idx, item)
            self.paths.insert(idx, uuid)
        # Reconnect model signals
        self.model().rowsInserted.connect(
            self.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
        )
        self.check_widgets_visible()
        self.apply_collapse_states()
