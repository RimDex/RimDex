"""Git operations: clone, batch update/push, check updates.

Extracted from ``MainContentController`` to keep the facade slim.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from loguru import logger
from PySide6.QtCore import Slot

from app.controllers.metadata_db_controller import AuxMetadataController
from app.core.ui_helpers import check_internet_connection
from app.git import git_utils
from app.git.git_utils import GitOperationConfig
from app.git.git_worker import (
    GitBatchPushResults,
    GitBatchPushWorker,
    GitBatchUpdateResults,
    GitBatchUpdateWorker,
    GitCheckResults,
    GitCheckUpdatesWorker,
    GitCloneWorker,
    GitPushWorker,
    GitStageCommitWorker,
    PushConfig,
)
from app.ui.dialogue import (
    BinaryChoiceDialog,
    InformationBox,
    show_dialogue_conditional,
)
from app.utils.github.models import GitHubModEntry

if TYPE_CHECKING:
    from PySide6.QtCore import QThreadPool

    from app.models.settings import Settings


class GitOpsHandler:
    """Handles git clone, batch update/push, and check updates operations."""

    def __init__(
        self,
        settings: Settings,
        thread_pool: QThreadPool,
        view: object,
        tr: Callable[..., str],
    ) -> None:
        self._settings = settings
        self._thread_pool = thread_pool
        self._view = view
        self._tr = tr

        self._git_clone_worker: GitCloneWorker | None = None
        self._git_push_worker: GitPushWorker | None = None
        self._git_stage_commit_worker: GitStageCommitWorker | None = None

    # ------------------------------------------------------------------
    # Filter GitHub mods from a list of paths
    # ------------------------------------------------------------------

    def filter_non_github_repos(self, repos_paths: list[Path]) -> list[Path]:
        """Filter out paths tracked as GitHub mods in the current instance."""
        settings = self._settings
        try:
            aux_controller = AuxMetadataController.get_or_create_cached_instance(
                settings.aux_db_path
            )
            with aux_controller.Session() as session:
                github_paths = {
                    entry.mod_path for entry in session.query(GitHubModEntry).all()
                }
        except Exception as e:
            logger.debug(f"Could not check GitHub mods table: {e}")
            return list(repos_paths)

        return [p for p in repos_paths if str(p) not in github_paths]

    # ------------------------------------------------------------------
    # Batch result dialog helper
    # ------------------------------------------------------------------

    def _show_batch_results(
        self,
        successful: list[Path],
        failed: list[tuple[Path, str]],
        *,
        success_title: str,
        success_text: str,
        success_information: str,
        success_details: str,
        failure_title: str,
        failure_text: str,
        failure_information: str,
        failure_details: str,
        partial_title: str,
        partial_text: str,
        partial_information: str,
        partial_details: str,
    ) -> None:
        """Show a three-branch InformationBox for batch operation results."""
        if not failed:
            InformationBox(
                title=success_title,
                text=success_text,
                information=success_information,
                details=success_details,
            ).exec()
        elif not successful:
            InformationBox(
                title=failure_title,
                text=failure_text,
                information=failure_information,
                details=failure_details,
            ).exec()
        else:
            InformationBox(
                title=partial_title,
                text=partial_text,
                information=partial_information,
                details=partial_details,
            ).exec()

    # ------------------------------------------------------------------
    # Check updates
    # ------------------------------------------------------------------

    @Slot(list)
    def on_check_updates_requested(self, repos_paths: list[Path]) -> None:
        """Schedule concurrent update checks for given repositories."""
        if not repos_paths:
            InformationBox(
                title=self._tr("No Repositories"),
                text=self._tr("No repositories provided for update check."),
                information=self._tr("Please select at least one repository to check."),
            ).exec()
            return
        logger.debug(
            f"Scheduling concurrent check for {len(repos_paths)} repositories."
        )
        config = GitOperationConfig(notify_errors=True)
        worker = GitCheckUpdatesWorker(repos_paths, config=config)
        worker.signals.finished.connect(self.handle_check_updates_results)
        self._thread_pool.start(worker)

    @Slot(object)
    def handle_check_updates_results(self, results: GitCheckResults) -> None:
        """Process results from GitCheckUpdatesWorker."""
        for invalid_path in results.invalid_paths:
            InformationBox(
                title=self._tr("Invalid git repository"),
                text=self._tr("Could not find a valid git repository."),
                information=str(invalid_path),
            ).exec()

        updates = results.updates
        logger.debug(f"Found {len(updates)} repositories with updates.")

        if results.errors:
            msg = "<br>".join(f"{path}: {err}" for path, err in results.errors.items())
            InformationBox(
                title=self._tr("Errors during update check"),
                text=self._tr("Some repositories encountered errors."),
                information=self._tr(
                    "Errors occurred while checking for updates:<br>{errors}"
                ).format(errors=msg),
            ).exec()
            return

        if not updates:
            InformationBox(
                title=self._tr("No updates found"),
                text=self._tr("All repositories are up to date."),
                information=self._tr("No new commits were found on remote branches."),
            ).exec()
            return

        details_msg = ""
        for repo_path, messages in updates.items():
            details_msg += f"{repo_path}<br>"
            for msg in messages:
                details_msg += f"\t{msg}<br>"

        binary_diag = BinaryChoiceDialog(
            title=self._tr("Git Updates Found"),
            text=self._tr("{len} repositories have updates available.").format(
                len=len(updates)
            ),
            information=self._tr("Would you like to update them now?"),
            details=details_msg,
            positive_text=self._tr("Update All"),
            negative_text=self._tr("Cancel"),
        )
        if binary_diag.exec_is_positive():
            self.on_update_repos(list(updates.keys()))
        else:
            logger.debug("User declined batch update.")

    # ------------------------------------------------------------------
    # Batch update
    # ------------------------------------------------------------------

    def on_update_repos(self, repos_paths: list[Path]) -> None:
        """Schedule concurrent batch pull for multiple repositories."""
        filtered_paths = self.filter_non_github_repos(repos_paths)
        if not filtered_paths:
            logger.debug("All repos are GitHub mods, skipping batch update.")
            return
        logger.debug(
            f"Scheduling concurrent update for {len(filtered_paths)} repositories "
            f"({len(repos_paths) - len(filtered_paths)} GitHub mods excluded)."
        )
        config = GitOperationConfig(notify_errors=True)
        worker = GitBatchUpdateWorker(filtered_paths, config=config)
        worker.signals.finished.connect(self.handle_batch_update_results)
        self._thread_pool.start(worker)

    @Slot(object)
    def handle_batch_update_results(self, results: GitBatchUpdateResults) -> None:
        """Process results from GitBatchUpdateWorker."""
        successful = results.successful
        failed = results.failed
        total = len(successful) + len(failed)
        commit_info = getattr(results, "commit_info", {})

        success_details = ""
        for repo_path in successful:
            repo_name = Path(repo_path).name
            info = commit_info.get(str(repo_path), "No commit info")
            success_details += f"✓ {repo_name}<br>  └─ {info}<br><br>"

        failure_details = ""
        for repo_path, err in failed:
            failure_details += f"{Path(repo_path).name}: {err}<br>"

        partial_details = self._tr("Successful updates:<br>")
        for repo_path in successful:
            repo_name = Path(repo_path).name
            info = commit_info.get(str(repo_path), "No commit info")
            partial_details += f"  ✓ {repo_name}<br>    └─ {info}<br>"
        partial_details += f"<br>{self._tr('Failed updates:')}<br>"
        for repo_path, err in failed:
            partial_details += f"  ✗ {Path(repo_path).name}: {err}<br>"

        self._show_batch_results(
            successful,
            failed,
            success_title=self._tr("Updates Completed"),
            success_text=self._tr("All repositories updated successfully!"),
            success_information=self._tr(
                "{count} repositories were updated with their latest commits:"
            ).format(count=len(successful)),
            success_details=success_details.strip(),
            failure_title=self._tr("Failed to update repo!"),
            failure_text=self._tr("All pull operations failed."),
            failure_information=self._tr(
                "{count} repositories could not be updated."
            ).format(count=len(failed)),
            failure_details=failure_details,
            partial_title=self._tr("Partial Updates Completed"),
            partial_text=self._tr("Some repositories updated successfully."),
            partial_information=self._tr(
                "{success} succeeded, {failed} failed out of {total}."
            ).format(success=len(successful), failed=len(failed), total=total),
            partial_details=partial_details,
        )

    # ------------------------------------------------------------------
    # Push
    # ------------------------------------------------------------------

    @Slot(list)
    def on_push_requested(self, repos_paths: list[Path]) -> None:
        """Handle push request for multiple repositories."""
        if not repos_paths:
            InformationBox(
                title=self._tr("No Repositories"),
                text=self._tr("No repositories provided for push operation."),
                information=self._tr("Please select at least one repository to push."),
            ).exec()
            return

        binary_diag = BinaryChoiceDialog(
            title=self._tr("Push Options"),
            text=self._tr("Push changes to remote repositories?"),
            information=self._tr(
                "This will push local commits to the remote repositories."
            ),
            details="\n".join([str(p) for p in repos_paths]),
            positive_text=self._tr("Push"),
            negative_text=self._tr("Cancel"),
        )

        if not binary_diag.exec_is_positive():
            logger.debug("User cancelled push operation.")
            return

        force_diag = BinaryChoiceDialog(
            title=self._tr("Force Push"),
            text=self._tr("Use force push?"),
            information=self._tr(
                "Force push will overwrite remote history. Use with caution!"
            ),
            positive_text=self._tr("Force Push"),
            negative_text=self._tr("Normal Push"),
        )
        force_push = force_diag.exec_is_positive()

        self.on_push_repos(repos_paths, force=force_push)

    def on_push_repos(self, repos_paths: list[Path], force: bool = False) -> None:
        """Schedule concurrent batch push for multiple repositories."""
        logger.debug(
            f"Scheduling concurrent push for {len(repos_paths)} repositories (force={force})."
        )
        config = GitOperationConfig(notify_errors=True)

        username = self._settings.github_username
        token = self._settings.github_token

        push_config = PushConfig(
            username=username,
            token=token,
            force=force,
        )

        worker = GitBatchPushWorker(repos_paths, push_config=push_config, config=config)
        worker.signals.finished.connect(self.handle_batch_push_results)
        self._thread_pool.start(worker)

    @Slot(object)
    def handle_batch_push_results(self, results: GitBatchPushResults) -> None:
        """Process results from GitBatchPushWorker."""
        successful = results.successful
        failed = results.failed
        total = len(successful) + len(failed)

        success_details = "\n".join([Path(p).name for p in successful])

        failure_details = ""
        for repo_path, err in failed:
            failure_details += f"{Path(repo_path).name}: {err}\n"

        partial_details = self._tr("Successful pushes:\n")
        for p in successful:
            partial_details += f"  \u2713 {Path(p).name}\n"
        partial_details += f"\n{self._tr('Failed pushes:')}\n"
        for repo_path, err in failed:
            partial_details += f"  \u2717 {Path(repo_path).name}: {err}\n"

        self._show_batch_results(
            successful,
            failed,
            success_title=self._tr("Push Completed"),
            success_text=self._tr("All repositories pushed successfully!"),
            success_information=self._tr("{count} repositories were pushed.").format(
                count=len(successful)
            ),
            success_details=success_details,
            failure_title=self._tr("Push Failed"),
            failure_text=self._tr("All push operations failed."),
            failure_information=self._tr(
                "{count} repositories could not be pushed."
            ).format(count=len(failed)),
            failure_details=failure_details,
            partial_title=self._tr("Partial Push Completed"),
            partial_text=self._tr("Some repositories pushed successfully."),
            partial_information=self._tr(
                "{success} succeeded, {failed} failed out of {total}."
            ).format(success=len(successful), failed=len(failed), total=total),
            partial_details=partial_details,
        )

    # ------------------------------------------------------------------
    # Git clone
    # ------------------------------------------------------------------

    @Slot(str, str)
    def do_git_clone(self, base_path: str, repo_url: str) -> None:
        """Handle clone request: ask user before starting."""
        if not check_internet_connection():
            return

        parsed = git_utils.parse_git_url(repo_url)
        if parsed is None:
            logger.error(f"Invalid git URL: {repo_url}")
            return

        clone_url = parsed.clone_url
        checkout_branch = parsed.branch
        full_repo_path = Path(base_path) / parsed.repo_name

        binary_diag = BinaryChoiceDialog(
            title=self._tr("Clone Repository"),
            text=self._tr("Do you want to clone this repository?"),
            information=self._tr(
                "Repository: {repo_url}<br>Destination: {dest}"
            ).format(repo_url=repo_url, dest=str(full_repo_path)),
            positive_text=self._tr("Clone"),
            negative_text=self._tr("Cancel"),
        )
        if not binary_diag.exec_is_positive():
            logger.debug("User cancelled clone operation.")
            return

        if full_repo_path.exists():
            answer = show_dialogue_conditional(
                title=self._tr("Existing repository found"),
                text=self._tr(
                    "An existing local repo that matches this repository was found:"
                ),
                information=self._tr(
                    "{repo_folder}<br/>"
                    + "How would you like to handle? Choose option:<br/>"
                    + "<br/>1) Clone new repository (deletes existing and replaces)"
                    + "<br/>2) Update existing repository (in-place force-update)"
                ).format(repo_folder=full_repo_path.name),
                button_text_override=[
                    self._tr("Clone new"),
                    self._tr("Update existing"),
                ],
            )
            if answer == self._tr("Clone new"):
                self.start_git_clone_worker(
                    clone_url,
                    str(full_repo_path),
                    force=True,
                    checkout_branch=checkout_branch,
                )
            elif answer == self._tr("Update existing"):
                self.on_update_repos([full_repo_path])
            else:
                logger.debug("User cancelled clone operation.")
        else:
            self.start_git_clone_worker(
                clone_url,
                str(full_repo_path),
                force=False,
                checkout_branch=checkout_branch,
            )

    def start_git_clone_worker(
        self,
        repo_url: str,
        base_path: str,
        force: bool,
        checkout_branch: str | None = None,
    ) -> None:
        """Initialize and start GitCloneWorker."""
        if self._git_clone_worker is not None:
            try:
                self._git_clone_worker.finished.disconnect()
                self._git_clone_worker.progress.disconnect()
                self._git_clone_worker.error.disconnect()
                self._git_clone_worker.quit()
                self._git_clone_worker.wait()
            except Exception:
                pass
            self._git_clone_worker = None

        config = GitOperationConfig(notify_errors=False)
        self._git_clone_worker = GitCloneWorker(
            repo_url=repo_url,
            repo_path=base_path,
            checkout_branch=checkout_branch,
            force=force,
            config=config,
        )
        self._git_clone_worker.finished.connect(self._on_git_clone_finished)
        self._git_clone_worker.progress.connect(self._on_git_clone_progress)
        self._git_clone_worker.error.connect(self._on_git_clone_error)
        logger.info(f"Starting git clone worker for: {repo_url}")
        self._git_clone_worker.start()

    @Slot(str)
    def _on_git_clone_progress(self, message: str) -> None:
        logger.debug(f"Git clone progress: {message}")

    @Slot(bool, str, str)
    def _on_git_clone_finished(self, success: bool, message: str, path: str) -> None:
        logger.info(
            f"Git clone finished: success={success}, message={message}, path={path}"
        )
        if success:
            InformationBox(
                title=self._tr("Repo retrieved"),
                text=self._tr("The configured repository was cloned!"),
                information=self._tr("Cloned to: {path}").format(path=path),
            ).exec()
        if self._git_clone_worker:
            try:
                self._git_clone_worker.finished.disconnect()
                self._git_clone_worker.progress.disconnect()
                self._git_clone_worker.error.disconnect()
            except Exception:
                pass
            self._git_clone_worker = None

    @Slot(str)
    def _on_git_clone_error(self, error_message: str) -> None:
        logger.error(f"Git clone error: {error_message}")
        InformationBox(
            title=self._tr("Failed to clone repo!"),
            text=self._tr(
                "The configured repo failed to clone/initialize!<br><br>"
                + "Are you connected to the Internet?<br><br>"
                + "Is your configured repo valid?"
            ),
            information=error_message,
        ).exec()
