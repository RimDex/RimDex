"""Tests for MissingDependenciesDialog and its Workshop handoff."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QDialog, QPushButton

from app.core.event_bus import EventBus
from app.services.dependency_resolver import DepResolveResult
from app.windows.missing_dependencies_dialog import MissingDependenciesDialog

DEPS_SUMMARY: dict[str, dict[str, set[str]]] = {
    "aaa.ModA": {
        "satisfied": {"aaa.LibA"},
        "local": {"aaa.LibB"},
        "download": {"aaa.LibC"},
    },
    "bbb.ModB": {
        "satisfied": set(),
        "local": set(),
        "download": {"bbb.LibD"},
    },
}


@pytest.fixture(autouse=True)
def _reset_restore_target() -> Any:
    EventBus().workshop_restore_target = None
    yield
    EventBus().workshop_restore_target = None


@pytest.fixture
def metadata_controller() -> Any:
    controller = MagicMock()
    controller.get_mod_name_from_package_id.side_effect = lambda pid: f"Name {pid}"
    return controller


@pytest.fixture
def dialog(metadata_controller: Any, qtbot: Any) -> Any:
    widget = MissingDependenciesDialog(metadata_controller)
    qtbot.addWidget(widget)
    yield widget
    widget.deleteLater()


def _row_button(dialog: Any, dep_id: str, label: str) -> QPushButton | None:
    checkbox = dialog.checkboxes.get(dep_id)
    if checkbox is None:
        return None
    row = checkbox.parentWidget()
    if row is None:
        return None
    for button in row.findChildren(QPushButton):
        if button.text() == label:
            return button
    return None


def _resolve(**kwargs: Any) -> DepResolveResult:
    defaults: dict[str, Any] = {
        "package_id": "aaa.LibC",
        "workshop_id": None,
        "workshop_url": None,
        "source": "none",
    }
    defaults.update(kwargs)
    return DepResolveResult(**defaults)


class TestSelection:
    def test_populate_creates_checkboxes(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        assert set(dialog.checkboxes) == {"aaa.LibB", "aaa.LibC", "bbb.LibD"}

    def test_checking_adds_to_selection(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        dialog.checkboxes["aaa.LibB"].setChecked(True)
        assert "aaa.LibB" in dialog.get_selected_mods()

    def test_unchecking_removes_from_selection(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        dialog.checkboxes["aaa.LibC"].setChecked(True)
        assert "aaa.LibC" in dialog.get_selected_mods()
        dialog.checkboxes["aaa.LibC"].setChecked(False)
        assert "aaa.LibC" not in dialog.get_selected_mods()

    def test_select_all(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        dialog.select_all()
        assert dialog.get_selected_mods() == {"aaa.LibB", "aaa.LibC", "bbb.LibD"}

    def test_clear_dependencies_resets_state(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        dialog.select_all()
        dialog.clear_dependencies()
        assert dialog.checkboxes == {}
        assert dialog.get_selected_mods() == set()

    def test_repopulate_does_not_leak_previous_selection(self, dialog: Any) -> None:
        dialog._populate_dependencies(DEPS_SUMMARY)
        dialog.select_all()
        dialog._populate_dependencies(DEPS_SUMMARY)
        assert dialog.get_selected_mods() == set()

    def test_empty_summary_populates_placeholder(self, dialog: Any) -> None:
        dialog._populate_dependencies({})
        assert dialog.checkboxes == {}


class TestShowDialog:
    def test_accept_returns_selection(self, dialog: Any, monkeypatch: Any) -> None:
        def _exec() -> QDialog.DialogCode:
            dialog.checkboxes["aaa.LibB"].setChecked(True)
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(dialog, "exec", _exec)
        assert dialog.show_dialog(DEPS_SUMMARY, {}) == {"aaa.LibB"}

    def test_reject_returns_empty_set(self, dialog: Any, monkeypatch: Any) -> None:
        monkeypatch.setattr(dialog, "exec", lambda: QDialog.DialogCode.Rejected)
        assert dialog.show_dialog(DEPS_SUMMARY, {}) == set()


class TestWorkshopHandoff:
    def test_open_workshop_uses_resolved_url(self, dialog: Any, qtbot: Any) -> None:
        url = "https://steamcommunity.com/sharedfiles/filedetails/?id=12345"
        resolve = _resolve(workshop_id="12345", workshop_url=url, source="steam_db")

        with qtbot.waitSignal(EventBus().do_browse_workshop_url) as blocker:
            dialog._open_workshop("aaa.LibC", resolve)

        assert blocker.args[0] == url
        assert EventBus().workshop_restore_target is dialog

    def test_open_workshop_falls_back_to_text_search(
        self, dialog: Any, qtbot: Any
    ) -> None:
        resolve = _resolve()
        with qtbot.waitSignal(EventBus().do_browse_workshop_url) as blocker:
            dialog._open_workshop("aaa.LibC", resolve)

        assert "search" in blocker.args[0]

    def test_open_workshop_without_resolve_uses_text_search(
        self, dialog: Any, qtbot: Any
    ) -> None:
        with qtbot.waitSignal(EventBus().do_browse_workshop_url) as blocker:
            dialog._open_workshop("aaa.LibC", None)

        assert "search" in blocker.args[0]

    def test_open_workshop_hides_dialog(self, dialog: Any, qtbot: Any) -> None:
        dialog.show()
        qtbot.waitExposed(dialog)
        with qtbot.waitSignal(EventBus().do_browse_workshop_url):
            dialog._open_workshop("aaa.LibC", _resolve())
        assert dialog.isVisible() is False


class TestDownloadButton:
    def test_download_requested_emits_workshop_id(
        self, dialog: Any, qtbot: Any
    ) -> None:
        dialog._dep_resolve = {
            "aaa.LibC": _resolve(workshop_id="999", source="about_xml")
        }
        dialog._populate_dependencies(DEPS_SUMMARY)

        button = _row_button(dialog, "aaa.LibC", dialog.tr("Download"))
        assert button is not None
        assert button.isEnabled() is True

        with qtbot.waitSignal(dialog.download_requested) as blocker:
            button.click()
        assert blocker.args[0] == "999"

    def test_download_button_disabled_without_workshop_id(self, dialog: Any) -> None:
        dialog._dep_resolve = {"bbb.LibD": _resolve(package_id="bbb.LibD")}
        dialog._populate_dependencies(DEPS_SUMMARY)

        button = _row_button(dialog, "bbb.LibD", dialog.tr("Download"))
        assert button is not None
        assert button.isEnabled() is False
