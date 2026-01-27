from __future__ import annotations

from typing import Sequence

from PySide6.QtWidgets import QWidget

from app.controllers.metadata_controller import MetadataController
from app.ui.widgets.button_factory import ButtonConfig, ButtonType
from app.windows.mixins._shared import (
    COL_AUTHOR,
    COL_MOD_DOWNLOADED,
    COL_MOD_NAME,
    COL_PACKAGE_ID,
    COL_PATH,
    COL_PUBLISHED_FILE_ID,
    COL_SOURCE,
    COL_SUPPORTED_VERSIONS,
    COL_UPDATED_ON_WORKSHOP,
    COL_WORKSHOP_PAGE,
    ColumnIndex,
    HeaderColumn,
    Layouts,
    UIElements,
)
from app.windows.mixins.buttons_mixin import ButtonsMixin
from app.windows.mixins.columns_mixin import ColumnsMixin
from app.windows.mixins.mod_rows_mixin import ModRowsMixin
from app.windows.mixins.selection_mixin import SelectionMixin
from app.windows.mixins.table_mixin import TableMixin
from app.windows.mixins.ui_mixin import UIBaseMixin


class BaseModsPanel(  # pyright: ignore[reportIncompatibleMethodOverride]
    UIBaseMixin,
    TableMixin,
    ModRowsMixin,
    SelectionMixin,
    ButtonsMixin,
    ColumnsMixin,
    QWidget,
):
    """
    Base class used for multiple panels that display a list of mods.
    """

    def __init__(
        self,
        object_name: str,
        window_title: str,
        title_text: str,
        details_text: str,
        additional_columns: Sequence[HeaderColumn],
        metadata_controller: MetadataController,
    ):
        super().__init__()
        self._metadata_controller = metadata_controller
        self._initialize_ui_elements()
        self._initialize_layouts()
        self._initialize_components()
        self._setup_components(
            object_name, window_title, title_text, details_text, additional_columns
        )

    def _populate_from_metadata(self) -> None:
        """Populate the table from metadata. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _populate_from_metadata")


__all__ = [
    "BaseModsPanel",
    "ButtonConfig",
    "ButtonType",
    "ColumnIndex",
    "HeaderColumn",
    "Layouts",
    "UIElements",
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
