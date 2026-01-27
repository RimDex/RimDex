"""Column and button-configuration mixin for BaseModsPanel.

Holds the shared column definitions, standard button configurations,
and the Steam-client-action extension logic.
"""

from __future__ import annotations

from app.ui.widgets.button_factory import ButtonConfig, ButtonType
from app.windows.mixins._shared import ColumnIndex, HeaderColumn


class ColumnsMixin:
    """Column definitions and button configurations for BaseModsPanel."""

    settings: object

    def _get_steam_client_integration_enabled(
        self,
    ) -> bool:  # overridden by UIBaseMixin
        raise NotImplementedError()

    def _get_standard_mod_columns(self) -> list["HeaderColumn"]:
        """
        Get the standard list of columns for displaying mod information.

        Returns:
            List of standard column definitions.
        """
        return [
            self.tr("Name"),  # type: ignore[attr-defined]
            self.tr("Author"),  # type: ignore[attr-defined]
            self.tr("Package ID"),  # type: ignore[attr-defined]
            self.tr("Published File Id"),  # type: ignore[attr-defined]
            self.tr("Supported Versions"),  # type: ignore[attr-defined]
            self.tr("Mod Downloaded"),  # type: ignore[attr-defined]
            self.tr("Updated on Workshop"),  # type: ignore[attr-defined]
            self.tr("Source"),  # type: ignore[attr-defined]
            self.tr("Path"),  # type: ignore[attr-defined]
            self.tr("Workshop Page"),  # type: ignore[attr-defined]
        ]

    def _get_base_button_configs(self) -> list[ButtonConfig]:
        """
        Get base button configurations that are common across panels.

        Returns:
            List of base ButtonConfig objects for refresh and SteamCMD.
        """
        return [
            ButtonConfig(
                button_type=ButtonType.REFRESH,
                custom_callback=self._refresh_metadata_and_panel,  # type: ignore[attr-defined]
            ),
            ButtonConfig(
                button_type=ButtonType.STEAMCMD,
                pfid_column=ColumnIndex.PUBLISHED_FILE_ID.value,
            ),
        ]

    def _extend_button_configs_with_steam_actions(
        self, button_configs: list[ButtonConfig]
    ) -> list[ButtonConfig]:
        """
        Extend button configurations with Steam client actions if integration is enabled.

        Args:
            button_configs: List of button configurations to extend.

        Returns:
            Extended list of button configurations.
        """
        steam_client_integration_enabled = self._get_steam_client_integration_enabled()
        if steam_client_integration_enabled:
            button_configs.append(
                ButtonConfig(
                    button_type=ButtonType.STEAM,
                    pfid_column=ColumnIndex.PUBLISHED_FILE_ID.value,
                ),
            )
        button_configs.append(self._get_delete_button_config())
        return button_configs

    def _get_delete_button_config(self) -> ButtonConfig:
        """Return a standard delete button configuration used by all panels."""
        return ButtonConfig(button_type=ButtonType.DELETE)
