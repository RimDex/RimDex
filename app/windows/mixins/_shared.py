"""Shared types and constants for the BaseModsPanel mixins.

Kept dependency-free (no import of ``base_mods_panel``) so the mixin
modules and ``base_mods_panel`` can both import from here without
creating an import cycle.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class TrMixin:
    """Structural type for the Qt object/widget surface the plain-Python
    ``BaseModsPanel`` mixins call via MRO (``self.tr``, ``self.close``,
    ``self.setObjectName`` etc.).

    The mixins are intentionally *not* ``QObject`` subclasses (that caused a
    diamond-inheritance double-init segfault with ``QWidget``). They instead
    rely on the concrete ``BaseModsPanel -> QWidget`` MRO to provide these
    methods at runtime. Declaring them here lets mypy/pyright resolve
    ``self.<method>`` without a ``# type: ignore[attr-defined]`` on every
    call site.
    """

    def tr(self, source_text: str, *args: Any, **kwargs: Any) -> str:
        return ""

    def close(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def setObjectName(self, name: str) -> None:
        pass

    def setWindowTitle(self, title: str) -> None:
        pass

    def setLayout(self, layout: Any) -> None:
        pass

    def resize(self, *args: Any, **kwargs: Any) -> None:
        pass

    def installEventFilter(self, filterObj: Any) -> None:
        pass


# By default, we assume Stretch for all columns.
# Tuples should be used if this should be overridden
HeaderColumn = str | tuple[str, QHeaderView.ResizeMode]


@dataclass
class UIElements:
    """Dataclass to group UI elements for better organization."""

    title: QLabel
    details_label: QLabel
    editor_select_all_button: QPushButton
    editor_cancel_button: QPushButton


@dataclass
class Layouts:
    """Dataclass to group layout elements for better organization."""

    upper_layout: QVBoxLayout
    lower_layout: QVBoxLayout
    details_layout: QVBoxLayout
    editor_layout: QVBoxLayout
    editor_actions_layout: QHBoxLayout
    editor_checkbox_actions_layout: QHBoxLayout
    editor_main_actions_layout: QHBoxLayout
    editor_exit_actions_layout: QHBoxLayout


class ColumnIndex(Enum):
    """Enumeration for table column indices to eliminate magic numbers."""

    CHECKBOX = 0
    NAME = 1
    AUTHOR = 2
    PACKAGE_ID = 3
    PUBLISHED_FILE_ID = 4
    SUPPORTED_VERSIONS = 5
    MOD_DOWNLOADED = 6
    UPDATED_ON_WORKSHOP = 7
    SOURCE = 8
    PATH = 9
    WORKSHOP_PAGE = 10


# Common column definitions for standardization
COL_MOD_NAME = "Name"
COL_AUTHOR = "Author"
COL_PACKAGE_ID = "Package ID"
COL_PUBLISHED_FILE_ID = "Published File Id"
COL_SUPPORTED_VERSIONS = "Supported Versions"
COL_MOD_DOWNLOADED = "Mod Downloaded"
COL_UPDATED_ON_WORKSHOP = "Updated on Workshop"
COL_SOURCE = "Source"
COL_PATH = "Path"
COL_WORKSHOP_PAGE = "Workshop Page"

__all__ = [
    "HeaderColumn",
    "UIElements",
    "Layouts",
    "TrMixin",
    "ColumnIndex",
    "COL_MOD_NAME",
    "COL_AUTHOR",
    "COL_PACKAGE_ID",
    "COL_PUBLISHED_FILE_ID",
    "COL_SUPPORTED_VERSIONS",
    "COL_MOD_DOWNLOADED",
    "COL_UPDATED_ON_WORKSHOP",
    "COL_SOURCE",
    "COL_PATH",
    "COL_WORKSHOP_PAGE",
    "BaseModsPanelSurface",
]


class BaseModsPanelSurface:
    """Declares the cross-mixin surface the plain-Python ``BaseModsPanel``
    mixins call on each other via MRO (``self._add_row``,
    ``self._refresh_metadata_and_panel``, ``self.metadata_controller``, etc.).

    Like ``TrMixin``, the mixins are intentionally *not* ``QObject``
    subclasses, so sibling-mixin methods resolve at runtime through the
    concrete ``BaseModsPanel`` MRO rather than being inherited directly. This
    plain (non-Protocol) base class gives mypy/pyright a type for those calls
    without a ``# type: ignore[attr-defined]`` on every site. Its method
    bodies are no-ops: on a real ``BaseModsPanel`` instance the actual mixin
    method (defined in one of the sibling mixins) always shadows them via
    MRO, so they are never executed. Kept as a regular class (not a
    ``Protocol``) so the stubbed methods are not treated as implicitly
    abstract — a ``Protocol`` would break ``BaseModsPanel`` subclass
    instantiation, the same trap hit with the first ``TrMixin`` attempt.
    """

    metadata_controller: Any
    _metadata_controller: Any
    editor_table_view: Any

    def _get_selected_mod_metadata(self) -> "list[dict[str, Any]]":
        return []

    def _refresh_metadata_and_panel(self) -> None:
        pass

    def _add_row(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _create_path_link(self, *args: Any, **kwargs: Any) -> "QLabel":
        raise NotImplementedError()

    def _create_workshop_button(self, *args: Any, **kwargs: Any) -> "QPushButton":
        raise NotImplementedError()

    def _clear_table_model(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _row_is_checked(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def _get_key_from_row(self, *args: Any, **kwargs: Any) -> "str | None":
        return None

    def _populate_from_metadata(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _setup_table_and_model(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get_button_factory(self, *args: Any, **kwargs: Any) -> Any:
        return None
