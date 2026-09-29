"""Tests for SteamHandler's mod-downloader wait-list preservation.

The Mod Downloader's queued mods must survive the browser window being closed
(e.g. to start a SteamCMD download) so that mods which fail to download
reappear the next time the browser is opened, instead of being lost.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication, QListWidget

from app.models.settings import Settings
from app.utils.steam.steambrowser.download_list import DownloadListManager

# app.core.ui_helpers and app.ui.dialogue have a pre-existing import cycle that
# only resolves when dialogue is imported first; do that before pulling in the
# handler package so this module is importable on its own.
importlib.import_module("app.ui.dialogue")
from app.controllers.handlers.steam_handler import SteamHandler


def _make_browser_like_queue() -> Any:
    """A minimal stand-in for SteamBrowser's download-list surface."""
    list_widget = QListWidget()
    manager = DownloadListManager(
        downloader_list=list_widget,
        url_prefix_sharedfiles="https://steamcommunity.com/sharedfiles/filedetails/?id=",
        get_current_title=lambda: "RimDex - Steam Browser",
        get_current_url=lambda: "",
        update_badge_fn=MagicMock(),
        open_url_fn=MagicMock(),
    )
    browser = MagicMock()
    browser.download_list_mgr = manager
    browser.get_download_list_snapshot.side_effect = manager.get_download_list_snapshot
    browser.restore_download_list.side_effect = manager.restore_download_list
    browser.remove_mod_if_queued.side_effect = manager.remove_mod_if_queued
    return browser


@pytest.fixture
def panel(
    qapp: QApplication, mock_app_info: None, mock_steamcmd_interface: None
) -> Any:
    """A stub MainContent exposing only what SteamHandler touches."""
    instance = MagicMock()
    instance.steam_browser = None
    instance.pending_downloader_snapshot = {}
    instance.tr = lambda text: text
    return instance


@pytest.fixture
def handler(panel: Any) -> SteamHandler:
    return SteamHandler(Settings(), panel)


class TestSnapshotDownloaderList:
    def test_captures_the_live_browser_queue(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        browser = _make_browser_like_queue()
        browser.download_list_mgr.add_mod("111", "Mod A")
        browser.download_list_mgr.add_mod("222", "Mod B")
        panel.steam_browser = browser

        handler.snapshot_downloader_list()

        assert panel.pending_downloader_snapshot == {"111": "Mod A", "222": "Mod B"}

    def test_is_a_noop_without_a_browser(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        panel.steam_browser = None

        handler.snapshot_downloader_list()

        assert panel.pending_downloader_snapshot == {}

    def test_repeat_snapshots_accumulate_across_browsers(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        first = _make_browser_like_queue()
        first.download_list_mgr.add_mod("111", "Mod A")
        panel.steam_browser = first
        handler.snapshot_downloader_list()

        panel.steam_browser = None
        second = _make_browser_like_queue()
        second.download_list_mgr.add_mod("222", "Mod B")
        panel.steam_browser = second
        handler.snapshot_downloader_list()

        assert panel.pending_downloader_snapshot == {"111": "Mod A", "222": "Mod B"}


class TestOnSteamcmdModDownloadSucceeded:
    def test_removes_from_the_preserved_snapshot(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        panel.pending_downloader_snapshot = {"111": "Mod A", "222": "Mod B"}
        panel.steam_browser = None

        handler.on_steamcmd_mod_download_succeeded("111")

        assert panel.pending_downloader_snapshot == {"222": "Mod B"}

    def test_removes_from_a_reopened_browsers_live_list(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        browser = _make_browser_like_queue()
        browser.download_list_mgr.add_mod("111", "Mod A")
        browser.download_list_mgr.add_mod("222", "Mod B")
        panel.steam_browser = browser

        handler.on_steamcmd_mod_download_succeeded("111")

        assert browser.download_list_mgr.get_mods() == ["222"]

    def test_unknown_pfid_is_a_quiet_noop(
        self, handler: SteamHandler, panel: Any
    ) -> None:
        browser = _make_browser_like_queue()
        browser.download_list_mgr.add_mod("111", "Mod A")
        panel.pending_downloader_snapshot = {"111": "Mod A"}
        panel.steam_browser = browser

        handler.on_steamcmd_mod_download_succeeded("999")

        assert panel.pending_downloader_snapshot == {"111": "Mod A"}
        assert browser.download_list_mgr.get_mods() == ["111"]


class TestBrowseWorkshopRestoresPendingSnapshot:
    def test_snapshot_is_handed_to_a_fresh_browser(
        self,
        handler: SteamHandler,
        panel: Any,
        monkeypatch: pytest.MonkeyPatch,
        qapp: QApplication,
    ) -> None:
        panel.pending_downloader_snapshot = {"111": "Mod A", "222": "Mod B"}

        monkeypatch.setattr(
            "app.controllers.handlers.steam_handler.SteamBrowser",
            _FakeSteamBrowser,
        )

        handler.do_browse_workshop_url(
            "https://steamcommunity.com/app/294100/workshop/"
        )

        assert isinstance(panel.steam_browser, _FakeSteamBrowser)
        assert panel.steam_browser.download_list_mgr.get_mods() == ["111", "222"]
        assert panel.pending_downloader_snapshot == {}

    def test_empty_snapshot_leaves_a_fresh_browser_empty(
        self,
        handler: SteamHandler,
        panel: Any,
        monkeypatch: pytest.MonkeyPatch,
        qapp: QApplication,
    ) -> None:
        monkeypatch.setattr(
            "app.controllers.handlers.steam_handler.SteamBrowser",
            _FakeSteamBrowser,
        )

        handler.do_browse_workshop_url(
            "https://steamcommunity.com/app/294100/workshop/"
        )

        assert panel.steam_browser.download_list_mgr.get_mods() == []


class _FakeSteamBrowser:
    """Stands in for SteamBrowser with a real DownloadListManager."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.downloader_list = QListWidget()
        self.download_list_mgr = DownloadListManager(
            downloader_list=self.downloader_list,
            url_prefix_sharedfiles=(
                "https://steamcommunity.com/sharedfiles/filedetails/?id="
            ),
            get_current_title=lambda: "RimDex - Steam Browser",
            get_current_url=lambda: "",
            update_badge_fn=MagicMock(),
            open_url_fn=MagicMock(),
        )
        self._about_to_close = _FakeSignal()
        self.destroyed = _FakeSignal()

    @property
    def about_to_close(self) -> Any:
        return self._about_to_close

    def get_download_list_snapshot(self) -> dict[str, str]:
        return self.download_list_mgr.get_download_list_snapshot()

    def restore_download_list(self, snapshot: dict[str, str]) -> None:
        self.download_list_mgr.restore_download_list(snapshot)

    def remove_mod_if_queued(self, publishedfileid: str) -> None:
        self.download_list_mgr.remove_mod_if_queued(publishedfileid)

    def show(self) -> None:
        pass

    def close(self) -> None:
        pass

    def deleteLater(self) -> None:
        pass


class _FakeSignal:
    def __init__(self) -> None:
        self.slots: list[Any] = []

    def connect(self, slot: Any) -> None:
        self.slots.append(slot)
