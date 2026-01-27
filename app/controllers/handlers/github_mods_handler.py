"""GitHub mod management: install, version switch, auto-update queue.

Extracted from ``MainContentController`` to keep the facade slim.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol

from loguru import logger
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QInputDialog, QMessageBox

from app.controllers.metadata_db_controller import AuxMetadataController
from app.core.event_bus import EventBus
from app.core.ui_helpers import check_internet_connection
from app.models.metadata.metadata_db import Base
from app.ui.dialogue import (
    BinaryChoiceDialog,
    InformationBox,
    show_dialogue_conditional,
)
from app.utils.github.models import GitHubModEntry
from app.utils.github.provider import (
    GitHubRateLimitError,
    ReleaseAsset,
    ReleaseInfo,
    create_provider,
    parse_github_url,
)
from app.utils.github.worker import (
    GitHubInstallWorker,
    GitHubUpdateCheckWorker,
    GitHubVersionSwitchWorker,
)

if TYPE_CHECKING:
    from app.controllers.handlers.git_ops_handler import GitOpsHandler
    from app.controllers.metadata_controller import MetadataController
    from app.models.settings import Settings
    from app.services.window_manager import WindowManager
    from app.utils.github.updater import UpdateAvailable
    from app.views.mods_panel import ModsPanel
    from app.windows.github_mods_panel import GitHubModsPanel

    class HandlerViewProtocol(Protocol):
        """Structural view surface the handler depends on.

        The concrete ``MainContent`` panel exposes these; declaring them
        here lets mypy resolve ``self._view.window_manager`` /
        ``self._view.mods_panel`` without ``# type: ignore[attr-defined]``.
        """

        window_manager: WindowManager
        mods_panel: ModsPanel


class GitHubModsHandler:
    """Handles GitHub mod install, version switching, and auto-update queue."""

    def __init__(
        self,
        settings: Settings,
        metadata_controller: MetadataController,
        view: "HandlerViewProtocol",
        tr: Callable[..., str],
        git_ops_handler: GitOpsHandler,
    ) -> None:
        self._settings = settings
        self._metadata_controller = metadata_controller
        self._view = view
        self._tr = tr
        self._git_ops_handler = git_ops_handler

        self._github_install_worker: GitHubInstallWorker | None = None
        self._github_version_switch_worker: GitHubVersionSwitchWorker | None = None
        self._github_update_check_worker: GitHubUpdateCheckWorker | None = None
        self._github_mods_panel: GitHubModsPanel | None = None
        self._github_auto_update_queue: list[UpdateAvailable] = []
        self._github_auto_update_results: list[tuple[str, bool]] = []

    # ------------------------------------------------------------------
    # Background update check
    # ------------------------------------------------------------------

    def start_github_update_check(self) -> None:
        settings = self._settings
        if not settings.github_update_check_enabled:
            return

        try:
            aux_controller = AuxMetadataController.get_or_create_cached_instance(
                settings.aux_db_path
            )
            Base.metadata.create_all(aux_controller.engine)

            with aux_controller.Session() as session:
                count = session.query(GitHubModEntry).count()
            if count == 0:
                return
        except Exception:
            return

        provider = create_provider(settings)

        self._github_update_check_worker = GitHubUpdateCheckWorker(
            provider=provider,
            instance_session_factory=aux_controller.Session,
            check_interval_hours=settings.github_update_check_interval_hours,
        )
        self._github_update_check_worker.finished.connect(
            self._on_github_update_check_finished
        )
        self._github_update_check_worker.error.connect(
            lambda msg: logger.warning(f"GitHub update check failed: {msg}")
        )
        self._github_update_check_worker.start()
        logger.info(f"Started background GitHub update check for {count} mod(s)")

    def _on_github_update_check_finished(self, updates: list[UpdateAvailable]) -> None:
        if not updates:
            logger.info("All GitHub mods are up to date")
            return

        auto = [u for u in updates if u.auto_update]
        manual = [u for u in updates if not u.auto_update]

        if manual:
            names = ", ".join(u.owner_repo for u in manual[:5])
            suffix = f" and {len(manual) - 5} more" if len(manual) > 5 else ""
            logger.info(f"GitHub updates available (manual): {names}{suffix}")
            InformationBox(
                title=self._tr("GitHub Mod Updates Available"),
                text=self._tr("{count} GitHub mod(s) have updates available.").format(
                    count=len(manual)
                ),
                information=self._tr(
                    "Use Download → GitHub Mods to view and install updates."
                ),
            ).exec()

        if auto:
            logger.info(
                f"Auto-updating {len(auto)} GitHub mod(s): "
                + ", ".join(u.owner_repo for u in auto)
            )
            self._github_auto_update_queue = list(auto)
            self._github_auto_update_results = []
            self._process_next_auto_update()
        elif not manual:
            logger.info("All GitHub mods are up to date")

    def _process_next_auto_update(self) -> None:
        if not self._github_auto_update_queue:
            self._on_auto_updates_complete()
            return

        update = self._github_auto_update_queue.pop(0)
        release = update.latest_release
        if release is None:
            self._github_auto_update_results.append((update.owner_repo, False))
            self._process_next_auto_update()
            return

        target_asset = None
        custom_zips = release.get_custom_zip_assets()
        if len(custom_zips) >= 1:
            target_asset = custom_zips[0]

        repo_url = f"https://github.com/{update.owner_repo}.git"
        worker = GitHubVersionSwitchWorker(
            mod_path=update.mod_path,
            owner_repo=update.owner_repo,
            repo_url=repo_url,
            target_release=release if target_asset else None,
            target_asset=target_asset,
        )
        owner_repo = update.owner_repo
        worker.finished.connect(
            lambda ok, ver, path: self._on_auto_update_one_finished(
                ok, ver, path, owner_repo
            )
        )
        self._github_version_switch_worker = worker
        worker.start()

    def _on_auto_update_one_finished(
        self, success: bool, new_version: str, mod_path: str, owner_repo: str
    ) -> None:
        self._github_auto_update_results.append((owner_repo, success))

        if success:
            version = self._record_installed_version(owner_repo, mod_path, new_version)
            logger.info(f"Auto-updated {owner_repo} to {version}")
        else:
            logger.warning(f"Auto-update failed for {owner_repo}: {new_version}")

        self._process_next_auto_update()

    def _on_auto_updates_complete(self) -> None:
        results = self._github_auto_update_results
        succeeded = [r for r, ok in results if ok]
        failed = [r for r, ok in results if not ok]

        summary_parts = []
        if succeeded:
            summary_parts.append(
                self._tr("Updated: {mods}").format(mods=", ".join(succeeded))
            )
        if failed:
            summary_parts.append(
                self._tr("Failed: {mods}").format(mods=", ".join(failed))
            )

        refresh_now = show_dialogue_conditional(
            title=self._tr("GitHub Auto-Update Complete"),
            text=self._tr(
                "{count} mod(s) were auto-updated.<br><br>{summary}<br><br>"
                "The updated versions won't appear until you refresh. "
                "Refresh now?"
            ).format(count=len(succeeded), summary="<br>".join(summary_parts)),
        )
        if refresh_now == QMessageBox.StandardButton.Yes:
            EventBus().do_refresh_mods_lists.emit()

    # ------------------------------------------------------------------
    # Open GitHub Mods panel
    # ------------------------------------------------------------------

    def open_github_mods_panel(self) -> None:
        from app.windows.github_mods_panel import GitHubModsPanel

        if self._github_mods_panel is not None and self._github_mods_panel.isVisible():
            self._github_mods_panel.raise_()
            self._github_mods_panel.activateWindow()
            return

        if self._github_mods_panel is not None:
            self._github_mods_panel.close()
            self._github_mods_panel.deleteLater()

        self._github_mods_panel = GitHubModsPanel(
            metadata_controller=self._metadata_controller
        )
        self._view.window_manager.register(self._github_mods_panel)
        self._github_mods_panel.show()

    # ------------------------------------------------------------------
    # Install mod (entry point)
    # ------------------------------------------------------------------

    @Slot()
    def do_git_install_mod(self) -> None:
        args, ok = QInputDialog().getText(
            self._view.mods_panel,
            self._tr("Enter git repo"),
            self._tr("Enter a git repository url (http/https) to clone to local mods:"),
        )
        if not ok or not args:
            logger.debug("Cancelled git install mod.")
            return

        base_path = str(
            self._settings.instances[self._settings.current_instance].local_folder
        )

        parsed = parse_github_url(args)
        if parsed is not None:
            owner, repo = parsed
            self._do_github_install_flow(f"{owner}/{repo}", args, base_path)
        else:
            self._clone_callback(base_path=base_path, repo_url=args)

    def _clone_callback(self, base_path: str, repo_url: str) -> None:
        """Clone a plain git repository directly as a standard git mod."""
        self._git_ops_handler.do_git_clone(base_path=base_path, repo_url=repo_url)

    def _resolve_release_asset(
        self,
        target_release: ReleaseInfo | None,
        no_zip_prompt: str,
    ) -> tuple[ReleaseInfo | None, ReleaseAsset | None, bool]:
        """Resolve the ZIP asset for a release, prompting if multiple exist.

        Returns ``(release, asset, cancelled)``. ``cancelled`` is True when the
        user backs out of the asset-selection or "no ZIP" prompt; on a declined
        "no ZIP" prompt ``release`` is reset to ``None`` so the caller falls
        back to HEAD.
        """
        target_asset: ReleaseAsset | None = None
        cancelled = False
        if target_release is not None:
            custom_zips = target_release.get_custom_zip_assets()
            if len(custom_zips) == 1:
                target_asset = custom_zips[0]
            elif len(custom_zips) > 1:
                asset_names = [a.name for a in custom_zips]
                chosen_asset, ok = QInputDialog().getItem(
                    self._view.mods_panel,
                    self._tr("Select Asset"),
                    self._tr("Multiple release assets found. Choose one:"),
                    asset_names,
                    0,
                    False,
                )
                if not ok:
                    cancelled = True
                    return target_release, target_asset, cancelled
                target_asset = custom_zips[asset_names.index(chosen_asset)]
            else:
                answer = show_dialogue_conditional(
                    title=self._tr("No Release ZIP Found"),
                    text=no_zip_prompt.format(tag=target_release.tag),
                    information=self._tr(
                        "The release only contains source archives, which may "
                        "not work as a RimWorld mod."
                    ),
                )
                if answer != QMessageBox.StandardButton.Yes:
                    cancelled = True
                    return target_release, target_asset, cancelled
                target_release = None
        return target_release, target_asset, cancelled

    def _record_installed_version(
        self, owner_repo: str, mod_path: str, new_version: str
    ) -> str:
        """Persist the installed version of a GitHub mod into the aux DB."""
        settings = self._settings
        aux_controller = AuxMetadataController.get_or_create_cached_instance(
            settings.aux_db_path
        )
        version = "HEAD" if new_version.startswith("HEAD") else new_version
        with aux_controller.Session() as session:
            entry = (
                session.query(GitHubModEntry)
                .filter_by(owner_repo=owner_repo, mod_path=mod_path)
                .first()
            )
            if entry is not None:
                entry.installed_version = version
                session.commit()
        return version

    def _do_github_install_flow(
        self, owner_repo: str, repo_url: str, base_path: str
    ) -> None:
        if not check_internet_connection():
            return

        settings = self._settings
        provider = create_provider(settings)

        try:
            releases = provider.get_releases(owner_repo, force_refresh=True)
        except GitHubRateLimitError as e:
            InformationBox(
                title=self._tr("GitHub Rate Limit"),
                text=str(e),
            ).exec()
            releases = []
        except Exception as e:
            logger.error(f"Failed to query GitHub releases: {e}")
            releases = []

        if releases:
            dialog_text = self._tr(
                "This repository is hosted on GitHub. You can install it as a "
                "GitHub Mod to track releases and manage versions, or clone it "
                "directly as a standard git mod."
            )
        else:
            dialog_text = self._tr(
                "No releases found for this repository. You can install it as a "
                "GitHub Mod tracking the latest commit (you'll be notified if "
                "releases are published in the future), or clone it directly "
                "as a standard git mod."
            )

        choice = BinaryChoiceDialog(
            title=self._tr("GitHub Repository Detected"),
            text=dialog_text,
            information=self._tr("Repository: {owner_repo}").format(
                owner_repo=owner_repo
            ),
            positive_text=self._tr("Install as GitHub Mod"),
            negative_text=self._tr("Clone as Git Mod"),
        )

        if not choice.exec_is_positive():
            self._clone_callback(base_path=base_path, repo_url=repo_url)
            return

        version_labels: list[str] = []
        releases_by_label: dict[str, ReleaseInfo | None] = {}

        for r in releases:
            label = f"{r.tag} (pre-release)" if r.prerelease else r.tag
            version_labels.append(label)
            releases_by_label[label] = r

        version_labels.append("HEAD (latest commit)")
        releases_by_label["HEAD (latest commit)"] = None

        stable = [r for r in releases if not r.prerelease]
        if stable:
            default_label = stable[0].tag
        elif releases:
            default_label = version_labels[0]
        else:
            default_label = "HEAD (latest commit)"

        chosen_label, ok = QInputDialog().getItem(
            self._view.mods_panel,
            self._tr("Select Version"),
            self._tr("Choose a version to install:"),
            version_labels,
            version_labels.index(default_label),
            False,
        )
        if not ok:
            return

        target_release = releases_by_label.get(chosen_label)
        target_asset: ReleaseAsset | None = None

        target_release, target_asset, cancelled = self._resolve_release_asset(
            target_release,
            self._tr(
                "Release {tag} has no ZIP assets. "
                "Install from HEAD (latest commit) instead?"
            ),
        )
        if cancelled:
            return

        repo_name = owner_repo.split("/")[1]
        target_dir = str(Path(base_path) / repo_name)

        if Path(target_dir).exists():
            answer = show_dialogue_conditional(
                title=self._tr("Existing mod found"),
                text=self._tr(
                    "A mod folder already exists at this location: {path}"
                ).format(path=target_dir),
                information=self._tr("Replace it with the GitHub mod?"),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            import shutil

            shutil.rmtree(target_dir, ignore_errors=True)

        self._github_install_worker = GitHubInstallWorker(
            owner_repo=owner_repo,
            release=target_release,
            asset=target_asset,
            repo_url=repo_url,
            target_dir=target_dir,
        )
        self._github_install_worker.finished.connect(
            lambda ok, msg, path: self._on_github_install_finished(
                ok, msg, path, owner_repo, target_release, target_asset
            )
        )
        self._github_install_worker.start()

    def _on_github_install_finished(
        self,
        success: bool,
        message: str,
        mod_path: str,
        owner_repo: str,
        release: ReleaseInfo | None,
        asset: ReleaseAsset | None,
    ) -> None:
        if not success:
            InformationBox(
                title=self._tr("GitHub Install Failed"),
                text=self._tr("Failed to install GitHub mod: {error}").format(
                    error=message
                ),
            ).exec()
            return

        settings = self._settings
        aux_controller = AuxMetadataController.get_or_create_cached_instance(
            settings.aux_db_path
        )
        Base.metadata.create_all(aux_controller.engine)

        with aux_controller.Session() as session:
            AuxMetadataController.get_or_create(session, mod_path)
            session.commit()

            version = "HEAD" if release is None else release.tag
            asset_name = asset.name if asset else None

            existing = (
                session.query(GitHubModEntry)
                .filter_by(owner_repo=owner_repo, mod_path=mod_path)
                .first()
            )
            if existing is not None:
                existing.installed_version = version
                existing.installed_asset_name = asset_name
            else:
                entry = GitHubModEntry(
                    owner_repo=owner_repo,
                    mod_path=mod_path,
                    installed_version=version,
                    installed_asset_name=asset_name,
                )
                session.add(entry)
            session.commit()

        InformationBox(
            title=self._tr("GitHub Mod Installed"),
            text=self._tr("Successfully installed {owner_repo} ({version})").format(
                owner_repo=owner_repo, version=version
            ),
        ).exec()

        EventBus().do_refresh_mods_lists.emit()

    # ------------------------------------------------------------------
    # Version switch
    # ------------------------------------------------------------------

    @Slot(str, str)
    def on_github_version_switch(self, mod_path: str, selected_tag: str) -> None:
        settings = self._settings
        aux_controller = AuxMetadataController.get_or_create_cached_instance(
            settings.aux_db_path
        )
        Base.metadata.create_all(aux_controller.engine)

        with aux_controller.Session() as session:
            entry = session.query(GitHubModEntry).filter_by(mod_path=mod_path).first()
            if entry is None:
                logger.warning(f"No GitHub mod entry for {mod_path}")
                return
            owner_repo = entry.owner_repo

        provider = create_provider(settings)
        releases = provider.get_releases(owner_repo)

        target_release = None
        target_asset = None

        if selected_tag != "HEAD (latest commit)":
            target_release = next((r for r in releases if r.tag == selected_tag), None)
            target_release, target_asset, cancelled = self._resolve_release_asset(
                target_release,
                self._tr("Release {tag} has no ZIP assets. Switch to HEAD instead?"),
            )
            if cancelled:
                return

        repo_url = f"https://github.com/{owner_repo}.git"

        self._github_version_switch_worker = GitHubVersionSwitchWorker(
            mod_path=mod_path,
            owner_repo=owner_repo,
            repo_url=repo_url,
            target_release=target_release,
            target_asset=target_asset,
        )
        self._github_version_switch_worker.finished.connect(
            lambda ok, ver, path: self._on_github_version_switch_finished(
                ok, ver, path, owner_repo
            )
        )
        self._github_version_switch_worker.start()

    def _on_github_version_switch_finished(
        self, success: bool, new_version: str, mod_path: str, owner_repo: str
    ) -> None:
        if not success:
            InformationBox(
                title=self._tr("Version Switch Failed"),
                text=self._tr("Failed to switch version: {error}").format(
                    error=new_version
                ),
            ).exec()
            return

        version = self._record_installed_version(owner_repo, mod_path, new_version)

        InformationBox(
            title=self._tr("Version Switched"),
            text=self._tr("Switched {owner_repo} to {version}").format(
                owner_repo=owner_repo, version=version
            ),
        ).exec()

        EventBus().do_refresh_mods_lists.emit()
