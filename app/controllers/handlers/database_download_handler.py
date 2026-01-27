"""Database download: HTTP download, startup auto-update, silent/interactive notifications.

Extracted from ``MainContentController`` to keep the facade slim.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from loguru import logger
from PySide6.QtCore import Slot

from app.core.app_info import AppInfo
from app.core.constants import DATABASE_DISPLAY_NAMES
from app.core.text_utils import extract_git_dir_name
from app.core.ui_helpers import check_internet_connection
from app.git.git_utils import GitOperationConfig
from app.git.git_worker import (
    GitBatchUpdateResults,
    GitBatchUpdateWorker,
)
from app.net.http_downloader import (
    DatabaseDownloadTask,
    DownloadResult,
    HttpDownloadWorker,
)
from app.ui.dialogue import InformationBox

if TYPE_CHECKING:
    from PySide6.QtCore import QThreadPool

    from app.controllers.handlers.git_ops_handler import GitOpsHandler
    from app.models.settings import Settings


class DatabaseDownloadHandler:
    """Handles HTTP database downloads and startup auto-update logic."""

    def __init__(
        self,
        settings: Settings,
        thread_pool: QThreadPool,
        tr: object,
        git_ops_handler: GitOpsHandler,
    ) -> None:
        self._settings = settings
        self._thread_pool = thread_pool
        self._tr = tr
        self._git_ops_handler = git_ops_handler

        self._http_download_worker: HttpDownloadWorker | None = None

    # ------------------------------------------------------------------
    # Startup auto-update (silent)
    # ------------------------------------------------------------------

    def update_databases_on_startup_if_enabled_silent(self) -> None:
        """Silently update databases on startup if enabled."""
        if not self._settings.update_databases_on_startup:
            logger.info("Update databases on startup is disabled.")
            return

        if not check_internet_connection():
            return

        settings = self._settings
        http_tasks: list[DatabaseDownloadTask] = []

        db_configs = [
            (
                settings.external_community_rules_metadata_source,
                settings.external_community_rules_repo,
                settings.external_community_rules_url,
                DATABASE_DISPLAY_NAMES["community_rules"],
            ),
            (
                settings.external_steam_metadata_source,
                settings.external_steam_metadata_repo,
                settings.external_steam_metadata_url,
                DATABASE_DISPLAY_NAMES["steam_workshop"],
            ),
            (
                settings.external_no_version_warning_metadata_source,
                settings.external_no_version_warning_repo_path,
                settings.external_no_version_warning_url,
                DATABASE_DISPLAY_NAMES["no_version_warning"],
            ),
            (
                settings.external_use_this_instead_metadata_source,
                settings.external_use_this_instead_repo_path,
                settings.external_use_this_instead_url,
                DATABASE_DISPLAY_NAMES["use_this_instead"],
            ),
        ]

        for source, repo_url, url, display_name in db_configs:
            if source == "Configured URL" and url:
                repo_name = (
                    extract_git_dir_name(repo_url)
                    if repo_url
                    else display_name.replace(" ", "-")
                )
                http_tasks.append(
                    DatabaseDownloadTask(
                        url=url,
                        target_dir=AppInfo().databases_folder,
                        repo_name=repo_name,
                        display_name=display_name,
                    )
                )
            elif source == "Configured git repository" and repo_url:
                logger.info(f"Auto-updating {display_name} database via git.")
                self._do_auto_database_update(
                    str(AppInfo().databases_folder), repo_url
                )

        if http_tasks:
            self._start_http_download(http_tasks, self._notify_http_result_silent)

    def _do_auto_database_update(self, base_path: str, repo_url: str) -> None:
        """Handle automatic database update: silently update existing or clone new."""
        from app.git import git_utils

        logger.info(f"Starting automatic database update: {repo_url}")

        parsed = git_utils.parse_git_url(repo_url)
        if parsed is None:
            logger.error(f"Invalid git URL for database update: {repo_url}")
            return

        full_repo_path = Path(base_path) / parsed.repo_name

        if full_repo_path.exists():
            logger.info(f"Updating existing database repository: {full_repo_path}")
            self._on_update_repos_silent([full_repo_path])
        else:
            logger.info(f"Cloning new database repository to: {full_repo_path}")
            self._git_ops_handler.start_git_clone_worker(
                parsed.clone_url,
                str(full_repo_path),
                force=False,
                checkout_branch=parsed.branch,
            )

    def _on_update_repos_silent(self, repos_paths: list[Path]) -> None:
        """Schedule concurrent batch pull for multiple repositories silently."""
        filtered_paths = self._git_ops_handler.filter_non_github_repos(repos_paths)
        if not filtered_paths:
            return
        logger.debug(
            f"Scheduling silent concurrent update for {len(filtered_paths)} repositories."
        )
        config = GitOperationConfig(notify_errors=False)
        worker = GitBatchUpdateWorker(filtered_paths, config=config)
        worker.signals.finished.connect(self._handle_batch_update_results_silent)
        self._thread_pool.start(worker)

    @Slot(object)
    def _handle_batch_update_results_silent(
        self, results: GitBatchUpdateResults
    ) -> None:
        """Process results from GitBatchUpdateWorker silently."""
        successful = results.successful
        failed = results.failed

        if successful:
            logger.info(
                f"Silently updated {len(successful)} database repositories successfully"
            )

        if failed:
            logger.warning(
                f"Failed to update {len(failed)} database repositories: "
                + str([(str(p), e) for p, e in failed])
            )

    # ------------------------------------------------------------------
    # Interactive download (user-triggered)
    # ------------------------------------------------------------------

    def do_download_database(
        self, base_path: Path, repo_url: str, url: str, source: str, display_name: str
    ) -> None:
        """Dispatch a database download via HTTP or git based on the configured source."""
        if not check_internet_connection():
            return

        if source == "Configured URL" and url:
            repo_name = (
                extract_git_dir_name(repo_url)
                if repo_url
                else display_name.replace(" ", "-")
            )
            task = DatabaseDownloadTask(
                url=url,
                target_dir=base_path,
                repo_name=repo_name,
                display_name=display_name,
            )
            self._start_http_download([task], self._notify_http_result_interactive)
        elif source == "Configured git repository" and repo_url:
            self._git_ops_handler.do_git_clone(  # type: ignore[attr-defined]
                base_path=str(base_path), repo_url=repo_url
            )
        else:
            logger.debug(f"Download not applicable for source type: {source}")

    # ------------------------------------------------------------------
    # HTTP download worker management
    # ------------------------------------------------------------------

    def _cleanup_http_download_worker(self) -> None:
        """Disconnect signals, stop, and discard the current HTTP download worker."""
        if self._http_download_worker is not None:
            try:
                self._http_download_worker.download_finished.disconnect()
                self._http_download_worker.quit()
                self._http_download_worker.wait()
            except Exception as e:
                logger.debug(f"Error during HTTP worker cleanup: {e}")
            self._http_download_worker = None

    def _start_http_download(
        self,
        tasks: list[DatabaseDownloadTask],
        notify: Callable[[list[str], list[str], list[str]], None],
    ) -> None:
        """Start an HTTP download worker, calling *notify* with results."""
        self._cleanup_http_download_worker()

        self._http_download_worker = HttpDownloadWorker(tasks)
        self._http_download_worker.download_finished.connect(
            lambda results: self._on_http_download_finished(results, notify)
        )
        self._http_download_worker.progress.connect(
            lambda msg: logger.info(f"HTTP DB download: {msg}")
        )
        logger.info(f"Starting HTTP download for {len(tasks)} database(s)")
        self._http_download_worker.start()

    def _on_http_download_finished(
        self,
        results: dict[str, DownloadResult],
        notify: Callable[[list[str], list[str], list[str]], None],
    ) -> None:
        """Handle HTTP download completion."""
        updated = [name for name, r in results.items() if r == DownloadResult.UPDATED]
        up_to_date = [
            name for name, r in results.items() if r == DownloadResult.UP_TO_DATE
        ]
        failed = [name for name, r in results.items() if r == DownloadResult.FAILED]
        notify(updated, up_to_date, failed)
        self._cleanup_http_download_worker()

    # ------------------------------------------------------------------
    # Notification callbacks
    # ------------------------------------------------------------------

    def _notify_http_result_silent(
        self, updated: list[str], up_to_date: list[str], failed: list[str]
    ) -> None:
        """Log HTTP download results (silent mode)."""
        if updated:
            logger.info(
                f"HTTP DB update: {len(updated)} database(s) updated: {', '.join(updated)}"
            )
        if failed:
            logger.warning(
                f"HTTP DB update: {len(failed)} database(s) failed: {', '.join(failed)}"
            )

    def _notify_http_result_interactive(
        self, updated: list[str], up_to_date: list[str], failed: list[str]
    ) -> None:
        """Show HTTP download results via user-facing dialogs."""
        if failed:
            InformationBox(
                title=self._tr("Download failed"),
                text=self._tr("Failed to download database(s): {names}").format(
                    names=", ".join(failed)
                ),
                information=self._tr(
                    "Please check your internet connection and the configured URL."
                ),
            ).exec()
        elif updated:
            InformationBox(
                title=self._tr("Download complete"),
                text=self._tr("Database(s) downloaded successfully: {names}").format(
                    names=", ".join(updated)
                ),
            ).exec()
        elif up_to_date:
            InformationBox(
                title=self._tr("Already up to date"),
                text=self._tr("Database(s) are already up to date: {names}").format(
                    names=", ".join(up_to_date)
                ),
            ).exec()
