import os
import platform
import re
from functools import partial
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QPixmap
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.core.app_info import AppInfo
from app.core.event_bus import EventBus
from app.core.window_launch_state import apply_window_launch_state
from app.models.mod_list import MetadataProvider
from app.models.settings import Settings
from app.ui.dialogue import show_dialogue_conditional, show_warning
from app.ui.widgets.image_label import ImageLabel
from app.utils.steam.steambrowser.badge_state import BadgeState
from app.utils.steam.steambrowser.download_list import DownloadListManager
from app.utils.steam.steambrowser.js_bridge import JavaScriptBridge
from app.utils.steam.steambrowser.page_scripts import PageScriptManager
from app.utils.steam.webapi.wrapper import (
    ISteamRemoteStorage_GetCollectionDetails,
    ISteamRemoteStorage_GetPublishedFileDetails,
)


class SteamBrowser(QWidget):
    """
    A generic panel used to browse Workshop content — downloader included.
    """

    web_view: QWebEngineView | None
    web_profile: QWebEngineProfile | None
    metadata_controller: MetadataProvider | None
    settings: Settings | None
    js_bridge: JavaScriptBridge | None
    download_list_mgr: DownloadListManager | None
    page_scripts: PageScriptManager | None

    def __init__(
        self,
        startpage: str,
        metadata_controller: MetadataProvider,
        settings: Settings,
    ):
        super().__init__()
        logger.debug("Initializing SteamBrowser")

        self.metadata_controller = metadata_controller
        self.settings = settings

        if platform.system() != "Windows":
            logger.info("Setting QTWEBENGINE_DISABLE_SANDBOX for non-Windows platform")
            os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

        # ------------------------------------------------------------------
        # Data
        # ------------------------------------------------------------------
        profile_dir = Path(AppInfo()._browser_profile_folder)
        profile_dir.mkdir(parents=True, exist_ok=True)
        self._web_profile_storage = str(profile_dir)

        self.current_html = ""
        self.current_title = "RimDex - Steam Browser"
        self.current_url = startpage

        self.searchtext_string = "&searchtext="
        self.url_prefix_steam = "https://steamcommunity.com"
        self.url_prefix_sharedfiles = (
            "https://steamcommunity.com/sharedfiles/filedetails/?id="
        )
        self.url_prefix_workshop = (
            "https://steamcommunity.com/workshop/filedetails/?id="
        )
        self.section_readytouseitems = "section=readytouseitems"
        self.section_collections = "section=collections"

        # ------------------------------------------------------------------
        # Persistent web profile
        # ------------------------------------------------------------------
        self.web_profile = QWebEngineProfile("SteamBrowserProfile", self)
        self.web_profile.setPersistentStoragePath(self._web_profile_storage)
        self.web_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # ------------------------------------------------------------------
        # Layouts
        # ------------------------------------------------------------------
        self.window_layout = QHBoxLayout()
        self.browser_layout = QVBoxLayout()
        self.downloader_layout = QVBoxLayout()

        # ------------------------------------------------------------------
        # Downloader widgets
        # ------------------------------------------------------------------
        self.downloader_label = QLabel(self.tr("Mod Downloader"))
        self.downloader_label.setObjectName("browserPaneldownloader_label")

        self.downloader_list = QListWidget()
        self.downloader_list.setFixedWidth(200)
        self.downloader_list.setItemAlignment(Qt.AlignmentFlag.AlignCenter)
        self.downloader_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.downloader_list.customContextMenuRequested.connect(
            self._on_downloader_context_menu
        )

        self.add_to_list2_button = QPushButton(self.tr("Add to List"))
        self.add_to_list2_button.clicked.connect(self._add_collection_or_mod_to_list)

        self.add_mods_by_id_button = QPushButton(self.tr("Add Mods by Workshop ID"))
        self.add_mods_by_id_button.setObjectName("browserPanelAddModsByID")
        self.add_mods_by_id_button.clicked.connect(self._show_add_mods_by_id_dialog)

        self.clear_list_button = QPushButton(self.tr("Clear List"))
        self.clear_list_button.setObjectName("browserPanelClearList")
        self.clear_list_button.clicked.connect(self._clear_downloader_list)

        self.download_steamcmd_button = QPushButton(
            self.tr("Download mod(s) (SteamCMD)")
        )
        self.download_steamworks_button = QPushButton(
            self.tr("Download mod(s) (Steam app)")
        )
        self.download_steamworks_button.clicked.connect(
            self._subscribe_to_mods_from_list
        )

        # ------------------------------------------------------------------
        # Browser widgets
        # ------------------------------------------------------------------
        self.web_view_loading_placeholder = ImageLabel()
        self.web_view_loading_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.web_view_loading_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.web_view_loading_placeholder.setPixmap(
            QPixmap(
                str(AppInfo().theme_data_folder / "default-icons" / "AppIcon_b.png")
            )
        )

        self.web_view = QWebEngineView()
        page = QWebEnginePage(self.web_profile, self.web_view)
        self.web_view.setPage(page)
        self.web_view.hide()
        self.web_view.loadStarted.connect(self._web_view_load_started)
        self.web_view.loadProgress.connect(self._web_view_load_progress)
        self.web_view.loadFinished.connect(self._web_view_load_finished)
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.startpage = QUrl(startpage)
        self.web_view.load(self.startpage)

        # QWebChannel setup
        self.channel = QWebChannel(self)
        self.js_bridge = JavaScriptBridge(self)
        self.channel.registerObject("browserBridge", self.js_bridge)
        self.web_view.page().setWebChannel(self.channel)

        _inject_qwebchannel_js(self.web_view.page())

        # Location box
        self.location = QLineEdit()
        self.location.setSizePolicy(
            QSizePolicy.Policy.Expanding, self.location.sizePolicy().verticalPolicy()
        )
        self.location.setText(self.startpage.url())
        self.location.returnPressed.connect(self._browse_to_location)

        # Nav bar
        self.add_to_list_button = QAction(self.tr("Add to list"))
        self.add_to_list_button.triggered.connect(self._add_collection_or_mod_to_list)
        self.nav_bar = QToolBar()
        self.nav_bar.setObjectName("browserPanelnav_bar")
        self.nav_bar.addAction(self.web_view.pageAction(QWebEnginePage.WebAction.Back))
        self.nav_bar.addAction(
            self.web_view.pageAction(QWebEnginePage.WebAction.Forward)
        )
        self.nav_bar.addAction(self.web_view.pageAction(QWebEnginePage.WebAction.Stop))
        self.nav_bar.addAction(
            self.web_view.pageAction(QWebEnginePage.WebAction.Reload)
        )
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("browser")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(True)

        # Build layouts
        self.downloader_layout.addWidget(self.downloader_label)
        self.downloader_layout.addWidget(self.downloader_list)
        self.downloader_layout.addWidget(self.add_to_list2_button)
        self.downloader_layout.addWidget(self.add_mods_by_id_button)
        self.downloader_layout.addWidget(self.download_steamcmd_button)
        self.downloader_layout.addWidget(self.download_steamworks_button)
        self.downloader_layout.addWidget(self.clear_list_button)

        self.browser_layout.addWidget(self.location)
        self.browser_layout.addWidget(self.nav_bar)
        self.browser_layout.addWidget(self.progress_bar)
        self.browser_layout.addWidget(self.web_view_loading_placeholder)
        self.browser_layout.addWidget(self.web_view)

        self.window_layout.addLayout(self.downloader_layout)
        self.window_layout.addLayout(self.browser_layout)

        self.setObjectName("browserPanel")
        self.setWindowTitle(self.current_title)
        self.setLayout(self.window_layout)

        # ------------------------------------------------------------------
        # DownloadListManager
        # ------------------------------------------------------------------
        self.download_list_mgr = DownloadListManager(
            downloader_list=self.downloader_list,
            url_prefix_sharedfiles=self.url_prefix_sharedfiles,
            get_current_title=lambda: self.current_title,
            get_current_url=lambda: self.current_url,
            update_badge_fn=self._update_badge_js,
            open_url_fn=self._open_mod_url,
        )

        # Keep a direct reference to the manager's tracking list so that
        # `partial(…, self.downloader_list_mods_tracking)` and other external
        # consumers see mutations made by the manager.
        self.downloader_list_mods_tracking = self.download_list_mgr.tracking

        # Wire SteamCMD button *after* tracking-list reference is live
        self.download_steamcmd_button.clicked.connect(
            partial(
                EventBus().do_steamcmd_download.emit,
                self.downloader_list_mods_tracking,
            )
        )

        self._launch_browser_window()
        logger.debug("Finished Browser Window initialization")

    # ------------------------------------------------------------------
    # Add Mods by Workshop ID dialog
    # ------------------------------------------------------------------

    def _show_add_mods_by_id_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Add Mods by Workshop ID"))
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            QLabel(
                self.tr(
                    "Enter one or more Workshop IDs (one per line or separated by commas):"
                )
            )
        )
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            ids = re.split(r"[\s,]+", text_edit.toPlainText().strip())
            ids = [id_.strip() for id_ in ids if id_.strip()]
            for workshop_id in ids:
                self._add_mod_to_list(publishedfileid=workshop_id)

    # ------------------------------------------------------------------
    # Window launch / navigation
    # ------------------------------------------------------------------

    def _launch_browser_window(self) -> None:
        assert self.settings is not None
        apply_window_launch_state(
            self,
            self.settings.browser_window_launch_state,
            self.settings.browser_window_custom_width,
            self.settings.browser_window_custom_height,
        )
        logger.info(
            f"Browser window started with launch state: {self.settings.browser_window_launch_state}"
        )

    def _browse_to_location(self) -> None:
        if self.web_view:
            self.web_view.load(QUrl(self.location.text()))

    # ------------------------------------------------------------------
    # Download-list public API  (called by JS bridge and others)
    # ------------------------------------------------------------------

    def _add_mod_to_list(self, publishedfileid: str, title: str | None = None) -> None:
        if self.download_list_mgr:
            self.download_list_mgr.add_mod(publishedfileid, title)

    def _remove_mod_from_list(self, publishedfileid: str) -> None:
        if self.download_list_mgr:
            self.download_list_mgr.remove_mod(publishedfileid)

    def _clear_downloader_list(self) -> None:
        if self.download_list_mgr:
            self.download_list_mgr.clear()

    def _open_mod_url(self, publishedfileid: str) -> None:
        if self.web_view:
            url = f"{self.url_prefix_sharedfiles}{publishedfileid}"
            self.web_view.load(QUrl(url))

    # ------------------------------------------------------------------
    # Add collection / mod (triggered by "Add to List" buttons)
    # ------------------------------------------------------------------

    def _add_collection_or_mod_to_list(self) -> None:
        publishedfileid = self._parse_pfid_from_url()
        if publishedfileid is None:
            return

        if "collectionItemDetails" not in self.current_html:
            self._add_mod_to_list(publishedfileid)
        else:
            self._add_collection(publishedfileid)

        # Report any duplicates that were detected during the calls above
        if self.download_list_mgr:
            dupes = self.download_list_mgr.pop_dupe_report()
            if dupes:
                dupe_report = "".join(
                    f"{name} | {pfid}<br>" for pfid, name in dupes.items()
                )
                show_warning(
                    title=self.tr("SteamCMD downloader"),
                    text=self.tr("You already have these mods in your download list!"),
                    information=self.tr(
                        "Skipping the following mods which are already present "
                        "in your download list!"
                    ),
                    details=dupe_report,
                )

    def _parse_pfid_from_url(self) -> str | None:
        if self.url_prefix_sharedfiles in self.current_url:
            pfid = self.current_url.split(self.url_prefix_sharedfiles, 1)[1]
        elif self.url_prefix_workshop in self.current_url:
            pfid = self.current_url.split(self.url_prefix_workshop, 1)[1]
        else:
            logger.error(
                f"Unable to parse publishedfileid from url: {self.current_url}"
            )
            show_warning(
                title=self.tr("No publishedfileid found"),
                text=self.tr(
                    "Unable to parse publishedfileid from url, "
                    "Please check if url is in the correct format"
                ),
                information=f"Url: {self.current_url}",
            )
            return None
        if self.searchtext_string in pfid:
            pfid = pfid.split(self.searchtext_string)[0]
        return pfid.split("#")[0].split("&")[0]

    def _add_collection(self, publishedfileid: str) -> None:
        collection_mods = self._compile_collection_datas(publishedfileid)
        if not collection_mods:
            collection_mods = self._scrape_collection_mods_from_html(self.current_html)

        if not collection_mods:
            logger.warning("Empty list of mods returned, unable to add collection!")
            show_warning(
                title=self.tr("SteamCMD downloader"),
                text=self.tr(
                    "Empty list of mods returned, unable to add collection to list!"
                ),
                information=self.tr(
                    "Please reach out to us on Github Issues page or "
                    "<br>#rimdex-testing on the Rocketman/CAI discord"
                ),
            )
            return

        answer = show_dialogue_conditional(
            title=self.tr("Add Collection"),
            text=self.tr("How would you like to add the collection?"),
            information=self.tr(
                "You can choose to add all mods from the collection "
                "or only the ones you don't have installed."
            ),
            button_text_override=[
                self.tr("Add All Mods"),
                self.tr("Add Missing Mods"),
            ],
        )

        if answer == self.tr("Add All Mods"):
            for pfid, title in collection_mods.items():
                self._add_mod_to_list(publishedfileid=pfid, title=title)
        elif answer == self.tr("Add Missing Mods"):
            for pfid, title in collection_mods.items():
                if not self._is_mod_installed(pfid):
                    self._add_mod_to_list(publishedfileid=pfid, title=title)

    def _compile_collection_datas(self, publishedfileid: str) -> dict[str, str]:
        result: dict[str, str] = {}
        webapi_result = ISteamRemoteStorage_GetCollectionDetails([publishedfileid])
        if not webapi_result:
            return result

        collection_pfids = [
            mod["publishedfileid"]
            for mod in webapi_result[0].get("children", [])
            if mod.get("publishedfileid")
        ]
        if not collection_pfids:
            return result

        mod_details, _, _ = ISteamRemoteStorage_GetPublishedFileDetails(
            collection_pfids
        )
        if not mod_details:
            return result

        for metadata in mod_details:
            pfid = metadata.get("publishedfileid")
            if pfid:
                result[pfid] = metadata.get("title", pfid)
        return result

    def _scrape_collection_mods_from_html(self, html: str) -> dict[str, str]:
        result: dict[str, str] = {}
        pattern = re.compile(
            r'<div[^>]+id="sharedfile_(\d+)"[^>]*'
            r'class="[^"]*collectionItem[^"]*"[^>]*>.*?'
            r'<a[^>]+href="https://steamcommunity.com/sharedfiles/filedetails/'
            r'\?id=\1"[^>]*>.*?'
            r'<div[^>]+class="[^"]*workshopItemTitle[^"]*"[^>]*>([^<]+)</div>',
            re.DOTALL | re.IGNORECASE,
        )
        matches = pattern.findall(html)
        logger.debug(
            f"Found {len(matches)} matches in fallback HTML scraping "
            f"for collection mods"
        )
        if matches:
            for pfid, title in matches:
                result[pfid] = title
        else:
            logger.warning("No matches found in fallback HTML scraping")
        return result

    # ------------------------------------------------------------------
    # WebView load lifecycle
    # ------------------------------------------------------------------

    def _web_view_load_started(self) -> None:
        self.progress_bar.setTextVisible(True)
        self.nav_bar.removeAction(self.add_to_list_button)

    def _web_view_load_progress(self, progress: int) -> None:
        self.progress_bar.setValue(progress)
        if progress > 25 and self.web_view:
            self.web_view_loading_placeholder.hide()
            self.web_view.show()

    def _web_view_load_finished(self) -> None:
        assert self.web_view is not None
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        # Cache page info
        self.current_title = self.web_view.title()
        self.web_view.page().toHtml(self._set_current_html)
        self.current_url = self.web_view.url().toString()

        # Update UI
        self.setWindowTitle(self.current_title)
        self.location.setText(self.current_url)

        # Only proceed with injections on Steam pages
        if self.url_prefix_steam not in self.current_url:
            return

        page = self.web_view.page()
        self.page_scripts = PageScriptManager(page)

        self.page_scripts.remove_install_button()
        self.page_scripts.change_target_to_self()

        installed_mods = self._get_installed_mods_list()
        added_mods = self._get_added_mods_list()
        self.page_scripts.inject_badge_scripts(installed_mods, added_mods)

        # Determine page type
        is_item_page = self.url_prefix_sharedfiles in self.current_url
        is_collection_page = self.url_prefix_workshop in self.current_url
        is_collections_page = self.section_collections in self.current_url
        is_items_page = self.section_readytouseitems in self.current_url or (
            not is_collections_page and "section=" in self.current_url
        )

        if not (is_item_page or is_collection_page or is_items_page):
            return

        self._setup_item_or_collection_page(is_item_page, is_collection_page)

    def _setup_item_or_collection_page(
        self, is_item_page: bool, is_collection_page: bool
    ) -> None:
        assert self.page_scripts is not None
        self.page_scripts.remove_subscribe_area()
        self.page_scripts.remove_collection_subscribe()
        self.page_scripts.remove_subscribe_buttons()
        self.page_scripts.inject_collection_buttons()

        self.nav_bar.addAction(self.add_to_list_button)

        if not (is_item_page or is_collection_page):
            return

        pfid = self._parse_pfid_from_url()
        if pfid is None:
            return

        if self._is_mod_installed(pfid):
            self.page_scripts.inject_installed_indicator()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_current_html(self, html: str) -> None:
        self.current_html = html

    def _is_mod_installed(self, publishedfileid: str) -> bool:
        assert self.metadata_controller is not None
        for mod in self.metadata_controller.mods_metadata.values():
            if mod.published_file_id == publishedfileid:
                return True
        return False

    def _get_installed_mods_list(self) -> list[str]:
        assert self.metadata_controller is not None
        return [
            pfid
            for mod in self.metadata_controller.mods_metadata.values()
            if (pfid := mod.published_file_id) is not None
        ]

    def _get_added_mods_list(self) -> list[str]:
        return list(self.downloader_list_mods_tracking)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _on_downloader_context_menu(self, point: QPoint) -> None:
        if self.download_list_mgr:
            self.download_list_mgr.context_menu(point)

    # ------------------------------------------------------------------
    # Download all (SteamCMD / Steamworks)
    # ------------------------------------------------------------------

    def _subscribe_to_mods_from_list(self) -> None:
        logger.debug(
            "Signaling Steamworks subscription handler with "
            f"{len(self.downloader_list_mods_tracking)} mods"
        )
        EventBus().do_steamworks_api_call.emit(
            [
                "subscribe",
                [int(pfid) for pfid in self.downloader_list_mods_tracking],
            ]
        )

    # ------------------------------------------------------------------
    # Badge JS update  (called by DownloadListManager)
    # ------------------------------------------------------------------

    def _update_badge_js(self, mod_id: str, status: BadgeState) -> None:
        assert self.web_view is not None
        script = (
            f"if (typeof window.updateModBadge === 'function') {{"
            f"  window.updateModBadge('{mod_id}', '{status.value}');"
            f"}} else {{"
            f"  console.warn('window.updateModBadge is not defined yet.');"
            f"}}"
        )
        self.web_view.page().runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda _: None
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.debug("Cleaning up SteamBrowser resources...")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        if self.web_view is not None:
            self.web_view.stop()
            for sig in ("loadStarted", "loadProgress", "loadFinished"):
                try:
                    getattr(self.web_view, sig).disconnect()
                except Exception:
                    pass

            if self.web_view.page():
                if self.js_bridge is not None:
                    self.channel.deregisterObject(self.js_bridge)
                    self.channel.deleteLater()
                self.web_view.page().profile().scripts().clear()
                self.web_view.page().deleteLater()

            self.web_view.deleteLater()
            self.web_view = None

        if self.web_profile is not None:
            self.web_profile.deleteLater()
            self.web_profile = None

        self.metadata_controller = None
        self.settings = None
        self.js_bridge = None
        self.download_list_mgr = None
        self.page_scripts = None

        self.clear_layout(self.window_layout)
        logger.debug("SteamBrowser cleanup completed")
        event.accept()

    def clear_layout(self, layout: QLayout | None) -> None:
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item is None:
                    break
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())


# ======================================================================
# Module-level helpers
# ======================================================================


def _inject_qwebchannel_js(page: QWebEnginePage) -> None:
    """Inject the Qt WebChannel JS bridge into *page*."""
    script = QWebEngineScript()
    script.setSourceUrl(QUrl("qrc:///qtwebchannel/qwebchannel.js"))
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(True)
    page.profile().scripts().insert(script)
