"""Tests for AdvancedTabController view-model sync."""

from unittest.mock import MagicMock

import pytest

from app.controllers.settings_tabs.advanced_tab_controller import AdvancedTabController
from app.models.settings import Settings


class TestAdvancedTabUpdateModel:
    """Test update_model_from_view reads dialog widget state into the model."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [("604800", 604800), ("0", 0), ("", 0), ("abc", 0)],
    )
    def test_database_expiry_parses_defensively(
        self, _mock_settings_deps: None, text: str, expected: int
    ) -> None:
        settings = Settings()
        dialog = MagicMock()
        dialog.database_expiry.text.return_value = text
        controller = AdvancedTabController(settings, dialog)

        controller.update_model_from_view()

        assert settings.database_expiry == expected
