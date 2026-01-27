"""Table model and row mixin for BaseModsPanel.

Holds low-level QStandardItemModel / QTableView operations: adding,
setting, counting, and clearing rows, plus runtime sort toggling.
"""

from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHeaderView,
    QTableView,
)

from app.windows.mixins._shared import ColumnIndex, HeaderColumn


class TableMixin:
    """Table model and row operations for BaseModsPanel."""

    editor_model: "QStandardItemModel"
    editor_table_view: "QTableView"

    def _setup_table_and_model(
        self,
        additional_columns: "Sequence[HeaderColumn]",
        sorting_enabled: bool = False,
    ) -> None:
        """
        Set up the complete table model and view with headers.

        This unified method initializes the QStandardItemModel, QTableView, and all headers
        in one consistent operation, preventing configuration conflicts or partial initialization.

        Args:
            additional_columns: List of column definitions (names or tuples of name/ResizeMode)
            sorting_enabled: Whether column sorting is enabled (default: False)
        """
        # Set up model with header labels
        self.editor_model = QStandardItemModel(0, len(additional_columns) + 1)
        editor_header_labels = ["✔"] + [
            col[0] if isinstance(col, tuple) else col for col in additional_columns
        ]
        self.editor_model.setHorizontalHeaderLabels(editor_header_labels)

        # Set up table view
        self.editor_table_view = QTableView()
        self.editor_table_view.setModel(self.editor_model)
        self.editor_table_view.setSortingEnabled(sorting_enabled)
        self.editor_table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.editor_table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.editor_table_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Set up headers - checkbox column resizes to contents
        header = self.editor_table_view.horizontalHeader()
        header.setSectionResizeMode(
            ColumnIndex.CHECKBOX.value, QHeaderView.ResizeMode.ResizeToContents
        )

        # Additional columns: use specified ResizeMode or default to Stretch
        for column_index, column in enumerate(additional_columns):
            if isinstance(column, tuple):
                resize_mode = column[1]
            else:
                resize_mode = QHeaderView.ResizeMode.Stretch
            header.setSectionResizeMode(
                ColumnIndex.CHECKBOX.value + column_index + 1, resize_mode
            )

        # Set vertical header to resize to contents
        self.editor_table_view.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def _add_row(
        self,
        items: list[QStandardItem],
        default_checkbox_state: bool = False,
    ) -> None:
        items = [
            QStandardItem(),
        ] + items
        self.editor_model.appendRow(items)
        checkbox_index = items[0].index()
        checkbox = QCheckBox()
        checkbox.setObjectName("selectCheckbox")
        checkbox.setChecked(default_checkbox_state)
        # Set the checkbox as the index widget
        self.editor_table_view.setIndexWidget(checkbox_index, checkbox)

    def _set_all_checkbox_rows(self, value: bool) -> None:
        # Iterate through the editor's rows
        for row in range(self.editor_model.rowCount()):
            # If an existing row is found, setChecked the value
            checkbox = self.editor_table_view.indexWidget(
                self.editor_model.item(row, 0).index()
            )
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(value)

    def _row_count(self) -> int:
        return self.editor_model.rowCount()

    def _clear_table_model(self) -> None:
        """Clear all rows from the table model."""
        self.editor_model.removeRows(0, self.editor_model.rowCount())

    def _reconfigure_table_sorting(self, sorting_enabled: bool) -> None:
        """
        Reconfigure table sorting after initialization (if needed).

        Most cases should configure sorting in _setup_table_and_model() instead.

        Args:
            sorting_enabled: Whether sorting is enabled
        """
        self.editor_table_view.setSortingEnabled(sorting_enabled)
