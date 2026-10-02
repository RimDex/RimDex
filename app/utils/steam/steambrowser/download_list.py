from collections.abc import Callable

from loguru import logger
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QMenu

from app.core.text_utils import extract_page_title_steam_browser

from .badge_state import BadgeState


class DownloadListManager:
    """Owns the mod download list UI widget, tracking, and dupe detection.

    Delegates badge updates and URL navigation back to the parent via
    callbacks so it stays decoupled from SteamBrowser.
    """

    def __init__(
        self,
        downloader_list: QListWidget,
        url_prefix_sharedfiles: str,
        get_current_title: Callable[[], str],
        get_current_url: Callable[[], str],
        update_badge_fn: Callable[[str, BadgeState], None],
        open_url_fn: Callable[[str], None],
    ) -> None:
        self._list = downloader_list
        self._url_prefix_sharedfiles = url_prefix_sharedfiles
        self._get_current_title = get_current_title
        self._get_current_url = get_current_url
        self._update_badge_fn = update_badge_fn
        self._open_url_fn = open_url_fn

        self.tracking: list[str] = []
        self._dupe_tracking: dict[str, str] = {}

        self._list.itemDoubleClicked.connect(self._open_mod_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_mod(self, publishedfileid: str, title: str | None = None) -> None:
        """Add a mod to the download list.  Sets *title* on the label and
        tooltip; when *title* is ``None`` it falls back to the browser's
        page title."""
        publishedfileid = str(publishedfileid)
        if publishedfileid in self.tracking:
            logger.debug(f"Duplicate PFID skipped: {publishedfileid}")
            page_title = self._resolve_page_title()
            self._dupe_tracking[publishedfileid] = title if title else page_title
            return

        logger.debug(f"Tracking PublishedFileId for download: {publishedfileid}")
        self.tracking.append(publishedfileid)

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, publishedfileid)

        if not title:
            page_title = self._resolve_page_title()
            label = QLabel(page_title)
            tooltip = f"{page_title}\n--> {self._get_current_url()}"
        else:
            label = QLabel(title)
            tooltip = f"{title}\n--> {self._url_prefix_sharedfiles}{publishedfileid}"

        item.setToolTip(tooltip)
        label.setToolTip(tooltip)
        label.setObjectName("ListItemLabel")
        item.setSizeHint(label.sizeHint())

        self._list.addItem(item)
        self._list.setItemWidget(item, label)
        self._update_badge_fn(publishedfileid, BadgeState.ADDED)

    def remove_mod(self, publishedfileid: str) -> None:
        """Remove a single mod from the download list and UI."""
        if publishedfileid not in self.tracking:
            logger.warning(f"Mod {publishedfileid} not found in tracking list")
            return

        self.tracking.remove(publishedfileid)

        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == publishedfileid:
                self._list.takeItem(i)
                break
        else:
            logger.warning(
                f"Mod {publishedfileid} removed from tracking, but UI item not found"
            )

        self._update_badge_fn(publishedfileid, BadgeState.DEFAULT)

    def clear(self) -> None:
        """Remove all mods from the download list and reset badges."""
        mods = list(self.tracking)
        self._list.clear()
        self.tracking.clear()
        self._dupe_tracking.clear()
        for mod_id in mods:
            self._update_badge_fn(mod_id, BadgeState.DEFAULT)

    def pop_dupe_report(self) -> dict[str, str]:
        """Return and clear the accumulated duplicate-tracking dictionary."""
        report = dict(self._dupe_tracking)
        self._dupe_tracking.clear()
        return report

    def get_mods(self) -> list[str]:
        """Return a snapshot of currently tracked published file IDs."""
        return [str(publishedfileid) for publishedfileid in self.tracking]

    def get_download_list_snapshot(self) -> dict[str, str]:
        """Return the queued mods as a PFID-to-title mapping."""
        snapshot: dict[str, str] = {}
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is None:
                continue
            raw_publishedfileid = item.data(Qt.ItemDataRole.UserRole)
            if raw_publishedfileid is None:
                continue
            publishedfileid = str(raw_publishedfileid)
            widget = self._list.itemWidget(item)
            title = widget.text() if isinstance(widget, QLabel) else publishedfileid
            snapshot[publishedfileid] = title
        return snapshot

    def restore_download_list(self, snapshot: dict[str, str]) -> None:
        """Restore queued mods from a PFID-to-title mapping."""
        for publishedfileid, title in dict(snapshot).items():
            self.add_mod(str(publishedfileid), title)

    def remove_mod_if_queued(self, publishedfileid: str) -> None:
        """Remove a queued mod when it is present."""
        normalized_publishedfileid = str(publishedfileid)
        if normalized_publishedfileid in self.tracking:
            self.remove_mod(normalized_publishedfileid)

    def context_menu(self, point: QPoint) -> None:
        """Show the right-click context menu for a download-list item."""
        item = self._list.itemAt(point)
        if not item:
            return

        pfid = item.data(Qt.ItemDataRole.UserRole)
        if pfid is None:
            return
        menu = QMenu()
        action = menu.addAction("Remove mod from list")
        action.triggered.connect(lambda pfid=pfid: self.remove_mod(str(pfid)))
        menu.exec_(self._list.mapToGlobal(point))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open_mod_url(self, item: QListWidgetItem) -> None:
        publishedfileid = item.data(Qt.ItemDataRole.UserRole)
        if publishedfileid:
            self._open_url_fn(str(publishedfileid))

    def _resolve_page_title(self) -> str:
        title = self._get_current_title()
        extracted = extract_page_title_steam_browser(title)
        return extracted if extracted else title
