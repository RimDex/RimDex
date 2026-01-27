"""UI and lifecycle mixin for BaseModsPanel.

Holds the widget setup, layout structure, component wiring, and the
shared event-filter / layout-clearing utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLayout, QPushButton, QVBoxLayout

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

from app.controllers.metadata_controller import MetadataController
from app.windows.mixins._shared import HeaderColumn, Layouts, UIElements


class UIBaseMixin:
    """UI construction and lifecycle methods for BaseModsPanel."""

    metadata_controller: MetadataController
    settings: Any
    ui_elements: UIElements
    layouts: Layouts

    def _setup_metadata(self) -> None:
        """Set up metadata controller and settings controller."""
        self.metadata_controller = self._metadata_controller  # type: ignore[attr-defined]
        self.settings = self.metadata_controller.settings
        self.metadata_controller.metadata_refreshed.connect(
            self._populate_from_metadata  # type: ignore[attr-defined]
        )

    def _get_steam_client_integration_enabled(self) -> bool:
        """
        Get whether Steam client integration is enabled.

        Returns:
            True if Steam client integration is enabled, False otherwise.
        """
        return self.settings.instances[
            self.settings.current_instance
        ].steam_client_integration

    def _setup_ui_elements(
        self,
        object_name: str,
        window_title: str,
        title_text: str,
        details_text: str,
    ) -> None:
        """Set up basic UI elements like title and details."""
        self.installEventFilter(self)  # type: ignore[attr-defined]
        self.setObjectName(object_name)  # type: ignore[attr-defined]
        self.ui_elements.title = QLabel(title_text)
        self.ui_elements.title.setObjectName("baseModsPanelTitle")
        self.ui_elements.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ui_elements.details_label = QLabel(details_text)
        self.ui_elements.details_label.setObjectName("baseModsPanelDetails")
        self.ui_elements.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setWindowTitle(window_title)  # type: ignore[attr-defined]

    def _setup_layout_structure(self) -> None:
        """Set up the main layout structure."""
        self.layouts.details_layout.addWidget(self.ui_elements.details_label)
        self.layouts.upper_layout.addLayout(self.layouts.details_layout)

    def _setup_action_buttons(self) -> None:
        """Set up the action buttons layout."""
        self.layouts.editor_actions_layout.addLayout(
            self.layouts.editor_checkbox_actions_layout
        )
        self.layouts.editor_actions_layout.addStretch(25)
        self.layouts.editor_actions_layout.addLayout(
            self.layouts.editor_main_actions_layout
        )
        self.layouts.editor_actions_layout.addStretch(25)
        self.layouts.editor_actions_layout.addLayout(
            self.layouts.editor_exit_actions_layout
        )

        self.layouts.editor_checkbox_actions_layout.addWidget(
            self.ui_elements.editor_select_all_button
        )

        self.ui_elements.editor_cancel_button.clicked.connect(self.close)  # type: ignore[attr-defined]
        self.layouts.editor_exit_actions_layout.addWidget(
            self.ui_elements.editor_cancel_button
        )

        self.layouts.editor_layout.addWidget(self.editor_table_view)  # type: ignore[attr-defined]
        self.layouts.editor_layout.addLayout(self.layouts.editor_actions_layout)

    def _setup_main_layout(self) -> None:
        """Set up the main layout structure."""
        layout = QVBoxLayout()
        layout.addWidget(self.ui_elements.title)
        layout.addLayout(self.layouts.upper_layout)
        layout.addLayout(self.layouts.lower_layout)

        self.layouts.lower_layout.addLayout(self.layouts.editor_layout)
        self.setLayout(layout)  # type: ignore[attr-defined]
        # TODO: let user configure window launch state and size from settings controller
        self.resize(900, 600)  # type: ignore[attr-defined]

    def _setup_table(self, additional_columns: "Sequence[HeaderColumn]") -> None:
        """Set up the table configuration."""
        pass  # Table setup is already done in _setup_ui

    def _setup_buttons(self) -> None:
        """Set up buttons if needed."""
        pass  # Buttons are set up in _setup_ui

    def _initialize_components(self) -> None:
        """Initialize core components."""
        self._setup_metadata()

    def _setup_components(
        self,
        object_name: str,
        window_title: str,
        title_text: str,
        details_text: str,
        additional_columns: "Sequence[HeaderColumn]",
    ) -> None:
        """Set up UI and table components."""
        self._setup_ui_elements(object_name, window_title, title_text, details_text)
        self._setup_layout_structure()
        self._setup_table_and_model(additional_columns)  # type: ignore[attr-defined]
        self._setup_action_buttons()
        self._setup_main_layout()
        self._setup_table(additional_columns)
        self._setup_buttons()

    def _initialize_ui_elements(self) -> None:
        """Initialize UI elements dataclasses."""
        factory = self.get_button_factory()  # type: ignore[attr-defined]
        self.ui_elements = UIElements(
            title=QLabel(),
            details_label=QLabel(),
            editor_select_all_button=factory.create_select_all_button(),
            editor_cancel_button=QPushButton(self.tr("Do nothing and exit")),  # type: ignore[attr-defined]
        )
        self.ui_elements.editor_cancel_button.setObjectName("dangerButton")

    def _initialize_layouts(self) -> None:
        """Initialize layout dataclasses."""
        self.layouts = Layouts(
            upper_layout=QVBoxLayout(),
            lower_layout=QVBoxLayout(),
            details_layout=QVBoxLayout(),
            editor_layout=QVBoxLayout(),
            editor_actions_layout=QHBoxLayout(),
            editor_checkbox_actions_layout=QHBoxLayout(),
            editor_main_actions_layout=QHBoxLayout(),
            editor_exit_actions_layout=QHBoxLayout(),
        )

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            key_event = QKeyEvent(event)  # type: ignore
            if key_event.key() == Qt.Key.Key_Escape:
                # Don't close AcfLogReader on Escape key (it's a persistent view)
                if self.__class__.__name__ != "AcfLogReader":
                    self.close()  # type: ignore[attr-defined]
                return True

        return super().eventFilter(watched, event)  # type: ignore[misc]

    def clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            if child is None:
                continue
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
