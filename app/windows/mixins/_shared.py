"""Shared types and constants for the BaseModsPanel mixins.

Kept dependency-free (no import of ``base_mods_panel``) so the mixin
modules and ``base_mods_panel`` can both import from here without
creating an import cycle.
"""

from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

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
]
