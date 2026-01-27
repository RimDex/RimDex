"""Thin facade delegating to handler modules.

Extracted from the former 2000-line monolith to keep orchestration slim
and move domain logic into focused handler classes.
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QObject, QThreadPool, Slot

from app.controllers.handlers.database_download_handler import (
    DatabaseDownloadHandler,
)
from app.controllers.handlers.database_upload_handler import DatabaseUploadHandler
from app.controllers.handlers.git_ops_handler import GitOpsHandler
from app.controllers.handlers.github_mods_handler import GitHubModsHandler
from app.controllers.metadata_controller import MetadataController
from app.core.app_info import AppInfo
from app.core.constants import DATABASE_DISPLAY_NAMES
from app.core.event_bus import EventBus
from app.models.settings import Settings
from app.views.main_content_panel import MainContent


class MainContentController(QObject):
    """Controller with concurrent checking/updating and improved structure."""

    def __init__(
        self,
        view: MainContent,
        settings: Settings,
        metadata_controller: MetadataController,
    ) -> None:
        super().__init__()
        self.view = view
        self.settings = settings
        self.metadata_controller = metadata_controller

        # Thread pool for concurrent tasks
        self.thread_pool = QThreadPool.globalInstance()

        # --- handlers ---------------------------------------------------
        self._git_ops = GitOpsHandler(
            settings=settings,
            thread_pool=self.thread_pool,
            view=view,
            tr=self.tr,
        )

        self._github_mods = GitHubModsHandler(
            settings=settings,
            metadata_controller=metadata_controller,
            view=view,
            tr=self.tr,
        )

        self._db_upload = DatabaseUploadHandler(
            settings=settings,
            tr=self.tr,
        )

        self._db_download = DatabaseDownloadHandler(
            settings=settings,
            thread_pool=self.thread_pool,
            tr=self.tr,
            git_ops_handler=self._git_ops,
        )

        # Map download signals to (base_path, repo_getter, url_getter, source_getter, display_name)
        self.download_signals = {
            EventBus().do_download_community_rules_db_from_github: (
                AppInfo().databases_folder,
                lambda: self.settings.external_community_rules_repo,
                lambda: self.settings.external_community_rules_url,
                lambda: self.settings.external_community_rules_metadata_source,
                DATABASE_DISPLAY_NAMES["community_rules"],
            ),
            EventBus().do_download_steam_workshop_db_from_github: (
                AppInfo().databases_folder,
                lambda: self.settings.external_steam_metadata_repo,
                lambda: self.settings.external_steam_metadata_url,
                lambda: self.settings.external_steam_metadata_source,
                DATABASE_DISPLAY_NAMES["steam_workshop"],
            ),
            EventBus().do_download_use_this_instead_db_from_github: (
                AppInfo().databases_folder,
                lambda: self.settings.external_use_this_instead_repo_path,
                lambda: self.settings.external_use_this_instead_url,
                lambda: self.settings.external_use_this_instead_metadata_source,
                DATABASE_DISPLAY_NAMES["use_this_instead"],
            ),
            EventBus().do_download_no_version_warning_db_from_github: (
                AppInfo().databases_folder,
                lambda: self.settings.external_no_version_warning_repo_path,
                lambda: self.settings.external_no_version_warning_url,
                lambda: self.settings.external_no_version_warning_metadata_source,
                DATABASE_DISPLAY_NAMES["no_version_warning"],
            ),
        }

        self._connect_signals()
        self._github_mods.start_github_update_check()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # GitHub mods
        EventBus().do_add_git_mod.connect(self._github_mods.do_git_install_mod)
        EventBus().do_open_github_mods_panel.connect(
            self._github_mods.open_github_mods_panel
        )
        EventBus().github_version_switch_requested.connect(
            self._github_mods.on_github_version_switch
        )

        # Git update-check signals
        update_targets = [
            self.view.mods_panel.active_mods_list.update_git_mods_signal,
            self.view.mods_panel.inactive_mods_list.update_git_mods_signal,
        ]
        for signal in update_targets:
            signal.connect(self._git_ops.on_check_updates_requested)

        # Download signals
        for event_signal, (
            base_path_obj,
            repo_getter,
            url_getter,
            source_getter,
            display_name,
        ) in self.download_signals.items():
            event_signal.connect(
                lambda repo_getter=repo_getter, url_getter=url_getter, source_getter=source_getter, base_path_obj=base_path_obj, display_name=display_name: (
                    self._db_download.do_download_database(
                        base_path=base_path_obj,
                        repo_url=repo_getter(),
                        url=url_getter(),
                        source=source_getter(),
                        display_name=display_name,
                    )
                )
            )

        # Upload signals
        EventBus().do_upload_steam_workshop_db_to_github.connect(
            self._db_upload.on_upload_steam_workshop_db
        )
        EventBus().do_upload_community_rules_db_to_github.connect(
            self._db_upload.on_upload_community_db
        )

    # ------------------------------------------------------------------
    # Public API — kept for backward compatibility (main_window, EventBus)
    # ------------------------------------------------------------------

    @Slot()
    def _update_databases_on_startup_if_enabled_silent(self) -> None:
        self._db_download.update_databases_on_startup_if_enabled_silent()

    @Slot(list)
    def _on_push_requested(self, repos_paths: List) -> None:
        self._git_ops.on_push_requested(repos_paths)
