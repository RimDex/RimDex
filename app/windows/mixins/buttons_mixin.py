"""Button-creation mixin for BaseModsPanel.

Holds all button factory/config logic: refresh, SteamCMD, Steam,
delete, custom, and the centralized config-driven dispatcher.
"""

from __future__ import annotations

from functools import partial
from typing import Any, Callable

from PySide6.QtWidgets import QLabel, QPushButton

from app.core.ui_helpers import platform_specific_open
from app.ui.widgets.button_factory import (
    ButtonConfig,
    ButtonFactory,
    ButtonType,
)
from app.views.deletion_menu import ModDeletionMenu
from app.views.mod_info_panel import ClickablePathLabel
from app.windows.mixins._shared import BaseModsPanelSurface, TrMixin


class ButtonsMixin(TrMixin, BaseModsPanelSurface):
    """Button creation and configuration for BaseModsPanel."""

    settings: Any
    metadata_controller: Any
    layouts: Any

    def _configure_button(
        self,
        button: QPushButton,
        text: str,
        object_name: str,
        callback: Callable[[], None] | None = None,
    ) -> None:
        """
        Configure a button with common properties.

        Args:
            button: The button to configure.
            text: Button text.
            object_name: Object name for the button.
            callback: Optional callback for the clicked signal.
        """
        button.setText(text)
        button.setObjectName(object_name)
        if callback is not None:
            button.clicked.connect(callback)

    def _create_workshop_button(
        self, url: str, object_name: str = "workshopButton"
    ) -> QPushButton:
        """
        Create a standardized workshop button that opens the Steam Workshop page.

        Args:
            url: The full URL to the Steam Workshop page.
            object_name: The object name for the button widget (default: "workshopButton").

        Returns:
            QPushButton: Configured button that opens the workshop page when clicked.
        """
        button = QPushButton()
        self._configure_button(
            button,
            self.tr("Open Page"),
            object_name,
            partial(platform_specific_open, url),
        )
        return button

    def _create_path_link(self, path: str, object_name: str = "pathLink") -> QLabel:
        """
        Create a clickable label that opens the mod path when clicked.

        Args:
            path: The file system path to open.
            object_name: The object name for the label widget (default: "pathLink").

        Returns:
            QLabel: Configured label that displays the path as clickable text.
        """
        label = ClickablePathLabel()
        label.setPath(path)
        label.setObjectName(object_name)
        return label

    def _create_deletion_button(self, config: ButtonConfig) -> QPushButton:
        """
        Create a standardized deletion button with menu from a config.

        Args:
            config: ButtonConfig with DELETE type and menu parameters.

        Returns:
            QPushButton: Configured deletion button with dropdown menu.
        """
        button = QPushButton()
        button.setText(self.tr("Delete"))
        button.setObjectName("dangerButton")
        deletion_menu = ModDeletionMenu(
            settings=self.settings,
            get_selected_mod_metadata=self._get_selected_mod_metadata,
            metadata_controller=self.metadata_controller,
            completion_callback=config.completion_callback
            or self._refresh_metadata_and_panel,
            enable_delete_mod=config.enable_delete_mod,
            enable_delete_keep_dds=config.enable_delete_keep_dds,
            enable_delete_dds_only=config.enable_delete_dds_only,
            enable_delete_and_unsubscribe=config.enable_delete_and_unsubscribe,
            enable_delete_and_resubscribe=config.enable_delete_and_resubscribe,
        )
        button.setMenu(deletion_menu)
        button.clicked.connect(
            lambda: deletion_menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        )
        return button

    def _setup_buttons_from_config(self, button_configs: list[ButtonConfig]) -> None:
        """
        Set up buttons from a list of button configurations.

        Args:
            button_configs: List of ButtonConfig objects defining the buttons to create.
        """
        factory = self.get_button_factory()
        for config in button_configs:
            button = self._create_button_from_config_with_factory(config, factory)
            if button:
                self.layouts.editor_main_actions_layout.addWidget(button)

    def _create_button_from_config(self, config: ButtonConfig) -> object:
        """
        Create a button from a single button configuration.

        Args:
            config: ButtonConfig object defining the button to create.

        Returns:
            The created button widget, or None if creation failed.
        """
        factory = self.get_button_factory()
        return self._create_button_from_config_with_factory(config, factory)

    def _create_button_from_config_with_factory(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """
        Create a button from a single button configuration using a factory.

        Args:
            config: ButtonConfig object defining the button to create.
            factory: ButtonFactory instance to create buttons.

        Returns:
            The created button widget, or None if creation failed.
        """
        if config.button_type == ButtonType.REFRESH:
            return self._create_refresh_button_from_config(config, factory)
        elif config.button_type == ButtonType.STEAMCMD:
            return self._create_steamcmd_button_from_config(config, factory)
        elif config.button_type == ButtonType.STEAM:
            return self._create_steam_button_from_config(config, factory)
        elif config.button_type == ButtonType.DELETE:
            return self._create_delete_button_from_config(config, factory)
        elif config.button_type == ButtonType.CUSTOM:
            return self._create_custom_button_from_config(config, factory)

        return None

    def _create_refresh_button_from_config(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """Create a refresh button from config."""
        return factory.create_refresh_button(config.custom_callback)

    def _create_steamcmd_button_from_config(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """Create a SteamCMD button from config."""
        if config.pfid_column is not None:
            return factory.create_steamcmd_button(config.pfid_column)
        return None

    def _create_steam_button_from_config(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """Create a Steam button from config."""
        if config.pfid_column is not None:
            return factory.create_steam_button(
                config.pfid_column, config.completion_callback
            )
        return None

    def _create_delete_button_from_config(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """Create a delete button from config."""
        return self._create_deletion_button(config)

    def _create_custom_button_from_config(
        self, config: ButtonConfig, factory: ButtonFactory
    ) -> object:
        """Create a custom button from config."""
        if config.custom_callback is not None:
            return factory.create_custom_button(config.text, config.custom_callback)
        return None

    def _create_custom_button(
        self, text: str, callback: Callable[[], None]
    ) -> QPushButton:
        """
        Create a custom button with text and callback.

        Args:
            text: Button text
            callback: Function to call when button is clicked

        Returns:
            Configured custom button
        """
        button = QPushButton(text)
        button.setObjectName("primaryButton")
        button.clicked.connect(callback)
        return button

    def get_button_factory(self) -> ButtonFactory:
        """Get a button factory instance for this panel."""
        return ButtonFactory(self)
