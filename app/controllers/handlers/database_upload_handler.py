"""Database upload to GitHub: fork → stash → pull → commit → push → PR.

Extracted from ``MainContentController`` to keep the facade slim.
All methods were previously ``_do_upload_db_to_repo``,
``_perform_git_upload_operations``, ``_create_pull_request``,
``_on_do_upload_steam_workshop_db_to_github``,
``_on_do_upload_community_db_to_github``, and ``_confirm_and_upload_db``.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, cast

from github import Github, Repository
from loguru import logger
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox

from app.core.app_info import AppInfo
from app.core.text_utils import (
    extract_git_dir_name,
    extract_git_user_or_org,
)
from app.core.ui_helpers import check_internet_connection
from app.git import git_utils
from app.git.git_utils import GitOperationConfig, pygit2
from app.ui.dialogue import (
    BinaryChoiceDialog,
    InformationBox,
    show_dialogue_conditional,
)

if TYPE_CHECKING:
    from app.models.settings import Settings


class DatabaseUploadHandler:
    """Handles uploading database JSON files to GitHub via fork→PR flow."""

    def __init__(self, settings: Settings, tr: object) -> None:
        self._settings = settings
        self._tr = tr

    # ------------------------------------------------------------------
    # Public entry points (connected via EventBus in the facade)
    # ------------------------------------------------------------------

    @Slot()
    def on_upload_steam_workshop_db(self) -> None:
        self._confirm_and_upload_db(
            title=self._tr("Upload Steam Workshop Database"),
            text=self._tr(
                "Are you sure you want to upload the Steam Workshop database to GitHub?"
            ),
            repo_url=self._settings.external_steam_metadata_repo,
            file_name="steamDB.json",
            log_label="Steam Workshop",
        )

    @Slot()
    def on_upload_community_db(self) -> None:
        self._confirm_and_upload_db(
            title=self._tr("Upload Community Rules Database"),
            text=self._tr(
                "Are you sure you want to upload the Community Rules database to GitHub?"
            ),
            repo_url=self._settings.external_community_rules_repo,
            file_name="communityRules.json",
            log_label="Community Rules",
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _confirm_and_upload_db(
        self,
        title: str,
        text: str,
        repo_url: str,
        file_name: str,
        log_label: str,
    ) -> None:
        binary_diag = BinaryChoiceDialog(
            title=title,
            text=text,
            information=self._tr(
                "This will create a pull request with your local database changes."
            ),
            positive_text=self._tr("Upload"),
            negative_text=self._tr("Cancel"),
        )

        if binary_diag.exec_is_positive():
            self.upload_db_to_repo(repo_url=repo_url, file_name=file_name)
        else:
            logger.debug(f"User cancelled {log_label} database upload.")

    def upload_db_to_repo(self, repo_url: str, file_name: str) -> None:
        if not check_internet_connection():
            return

        if not repo_url or not repo_url.strip():
            InformationBox(
                title=self._tr("Invalid repository"),
                text=self._tr("Repository URL is empty or invalid."),
                information=self._tr(
                    "Please configure a valid repository URL in settings."
                ),
            ).exec()
            return

        if not (repo_url.startswith("http://") or repo_url.startswith("https://")):
            InformationBox(
                title=self._tr("Invalid repository"),
                text=self._tr("An invalid repository was detected!"),
                information=self._tr(
                    "Please reconfigure a repository in settings!<br>"
                    + 'A valid repository is a repository URL which is not empty and is prefixed with "http://" or "https://"'
                ),
            ).exec()
            return

        try:
            repo_user_or_org = extract_git_user_or_org(repo_url)
            repo_folder_name = extract_git_dir_name(repo_url)
        except Exception as e:
            logger.error(f"Failed to parse repository URL: {e}")
            InformationBox(
                title=self._tr("Invalid repository URL"),
                text=self._tr("Failed to parse repository information from URL."),
                information=self._tr("URL: {repo_url}<br>Error: {error}").format(
                    repo_url=repo_url, error=str(e)
                ),
            ).exec()
            return

        github_username = self._settings.github_username
        github_token = self._settings.github_token

        if not github_username or not github_token:
            InformationBox(
                title=self._tr("GitHub credentials missing"),
                text=self._tr(
                    "GitHub username and token are required for database upload."
                ),
                information=self._tr(
                    "Please configure your GitHub credentials in settings."
                ),
            ).exec()
            return

        repo_path = Path(AppInfo().databases_folder) / repo_folder_name

        if not repo_path.exists():
            answer = show_dialogue_conditional(
                title=self._tr("Repository not found"),
                text=self._tr("Local repository does not exist."),
                information=self._tr("Would you like to clone the repository first?"),
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._clone_callback(
                    base_path=str(AppInfo().databases_folder),
                    repo_url=repo_url,
                )
            return

        file_full_path = repo_path / file_name
        if not file_full_path.exists():
            InformationBox(
                title=self._tr("File does not exist"),
                text=self._tr(
                    "Please ensure the file exists and then try to upload again!"
                ),
                information=self._tr(
                    "File not found:<br>{file_full_path}<br>Repository:<br>{repo_url}"
                ).format(file_full_path=file_full_path, repo_url=repo_url),
            ).exec()
            return

        try:
            with open(file_full_path, encoding="utf-8") as f:
                database = json.loads(f.read())

            if database.get("version"):
                database_version = database["version"] - self._settings.database_expiry
            elif database.get("timestamp"):
                database_version = database["timestamp"]
            else:
                InformationBox(
                    title=self._tr("Invalid database"),
                    text=self._tr(
                        "Database file does not contain version or timestamp."
                    ),
                    information=self._tr("File: {file_path}").format(
                        file_path=str(file_full_path)
                    ),
                ).exec()
                return
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse database file: {e}")
            InformationBox(
                title=self._tr("Database parse error"),
                text=self._tr("Failed to read or parse database file."),
                information=str(e),
            ).exec()
            return

        timezone_abbreviation = (
            datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        )
        database_version_human_readable = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(database_version))
            + f" {timezone_abbreviation}"
        )

        try:
            g = Github(github_username, github_token)
            original_repo = g.get_repo(f"{repo_user_or_org}/{repo_folder_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub API: {e}")
            InformationBox(
                title=self._tr("GitHub API error"),
                text=self._tr("Failed to connect to GitHub API."),
                information=str(e),
            ).exec()
            return

        fork_repo = None
        try:
            fork_repo = g.get_repo(f"{github_username}/{repo_folder_name}")
            logger.info(f"Found existing fork: {fork_repo.full_name}")
        except Exception:
            try:
                logger.info(f"Creating fork of {original_repo.full_name}")
                fork_repo = original_repo.create_fork()
                logger.info(f"Created fork: {fork_repo.full_name}")

                InformationBox(
                    title=self._tr("Fork created"),
                    text=self._tr("Created fork of repository."),
                    information=self._tr(
                        "Fork: {fork_name}<br>Please wait a moment for GitHub to set up the fork."
                    ).format(fork_name=fork_repo.full_name),
                ).exec()
            except Exception as e:
                logger.error(f"Failed to create fork: {e}")
                InformationBox(
                    title=self._tr("Fork creation failed"),
                    text=self._tr("Failed to create fork of repository."),
                    information=str(e),
                ).exec()
                return

        if not fork_repo:
            InformationBox(
                title=self._tr("Fork error"),
                text=self._tr("Could not access or create fork repository."),
            ).exec()
            return

        fork_url = fork_repo.clone_url

        self._perform_git_upload_operations(
            repo_path=repo_path,
            file_name=file_name,
            fork_url=fork_url,
            database_version=database_version,
            database_version_human_readable=database_version_human_readable,
            original_repo=original_repo,
            fork_repo=fork_repo,
            github_username=github_username,
            github_token=github_token,
        )

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    def _perform_git_upload_operations(
        self,
        repo_path: Path,
        file_name: str,
        fork_url: str,
        database_version: int,
        database_version_human_readable: str,
        original_repo: Repository.Repository,
        fork_repo: Repository.Repository,
        github_username: str,
        github_token: str,
    ) -> None:
        config = GitOperationConfig(notify_errors=True)

        try:
            with git_utils.git_repository(repo_path, config) as repo:
                if repo is None:
                    InformationBox(
                        title=self._tr("Git repository error"),
                        text=self._tr("Invalid git repository."),
                        information=str(repo_path),
                    ).exec()
                    return

                origin_remote = None
                for remote in repo.remotes:
                    if remote.name == "origin":
                        origin_remote = remote
                        break

                if origin_remote:
                    repo.remotes.delete("origin")

                repo.remotes.create("origin", fork_url)
                logger.info(f"Updated origin remote to fork: {fork_url}")

                stash_created = False

                if git_utils.git_has_uncommitted_changes(repo, config):
                    logger.info(
                        "Uncommitted changes detected, stashing them before pull"
                    )
                    stash_result = git_utils.git_stash(
                        repo,
                        message="Auto-stash before database upload pull",
                        config=config,
                    )
                    if (
                        stash_result.is_successful()
                        and stash_result == git_utils.GitStashResult.STASHED
                    ):
                        stash_created = True
                        logger.info("Successfully stashed uncommitted changes")
                    elif not stash_result.is_successful():
                        logger.error(f"Failed to stash changes: {stash_result}")
                        InformationBox(
                            title=self._tr("Stash failed"),
                            text=self._tr(
                                "Failed to stash uncommitted changes before pull."
                            ),
                            information=str(stash_result),
                        ).exec()
                        return
                else:
                    logger.info("No uncommitted changes detected")

                pull_result = git_utils.git_pull(
                    repo,
                    branch="main",
                    reset_working_tree=True,
                    force=True,
                    config=config,
                )
                if not pull_result.is_successful():
                    logger.warning(f"Pull operation result: {pull_result}")
                    if "conflict" in str(pull_result).lower():
                        logger.error("Merge conflicts detected during pull")
                        InformationBox(
                            title=self._tr("Pull conflict"),
                            text=self._tr(
                                "Merge conflicts encountered during pull operation."
                            ),
                            information=self._tr(
                                "Please manually resolve conflicts and try again."
                            ),
                        ).exec()
                        return
                    else:
                        logger.error(f"Pull failed: {pull_result}")
                        InformationBox(
                            title=self._tr("Pull failed"),
                            text=self._tr("Failed to pull latest changes from remote."),
                            information=str(pull_result),
                        ).exec()
                        return

                branch_name = f"{database_version}"
                commit_message = f"DB Update: {database_version_human_readable}"

                if stash_created:
                    logger.info(
                        "Restoring stashed changes on main branch after successful pull"
                    )
                    current_head_after_pull = repo.head.target

                    unstash_result = git_utils.git_stash(
                        repo, pop=True, config=config
                    )

                    if not unstash_result.is_successful():
                        logger.warning(
                            f"Failed to restore stashed changes: {unstash_result}"
                        )
                        conflict_detected = False
                        try:
                            status = repo.status()
                            conflict_files = []
                            for filepath, flags in status.items():
                                if flags & pygit2.GIT_STATUS_CONFLICTED:
                                    conflict_files.append(filepath)

                            if conflict_files:
                                conflict_detected = True
                                logger.error(
                                    f"Merge conflicts detected in files: {conflict_files}"
                                )
                                logger.info(
                                    "Automatically resolving conflicts by resetting to clean state"
                                )
                                repo.reset(
                                    current_head_after_pull,
                                    pygit2.enums.ResetMode.HARD,
                                )
                                repo.state_cleanup()
                                logger.info(
                                    "Repository reset to clean state after conflicts"
                                )
                                InformationBox(
                                    title=self._tr("Conflicts Auto-Resolved"),
                                    text=self._tr(
                                        "Merge conflicts were detected and automatically resolved."
                                    ),
                                    information=self._tr(
                                        "Your local changes conflicted with remote changes. "
                                        "The repository has been reset to a clean state with the latest remote changes. "
                                        "Your original changes are preserved in the database file and will be committed."
                                    ),
                                ).exec()
                        except Exception as e:
                            logger.warning(f"Could not check for merge conflicts: {e}")

                        if not conflict_detected:
                            logger.warning(
                                "Stash pop failed but no conflicts detected, continuing..."
                            )
                            InformationBox(
                                title=self._tr("Stash restore warning"),
                                text=self._tr(
                                    "Failed to restore stashed changes, but no conflicts detected."
                                ),
                                information=self._tr(
                                    "Continuing with current state. Your database changes should still be present."
                                ),
                            ).exec()

                try:
                    current_commit_oid = repo.head.target
                    current_commit = cast(pygit2.Commit, repo[current_commit_oid])

                    try:
                        existing_branch = repo.branches.local[branch_name]
                        if existing_branch:
                            logger.info(f"Deleting existing branch: {branch_name}")
                            existing_branch.delete()
                    except KeyError:
                        pass

                    branch_ref = repo.branches.local.create(
                        branch_name, current_commit
                    )
                    logger.info(
                        f"Created branch: {branch_name} (will switch after commit)"
                    )
                except Exception as e:
                    logger.error(f"Failed to create branch {branch_name}: {e}")
                    InformationBox(
                        title=self._tr("Branch creation failed"),
                        text=self._tr("Failed to create new branch for upload."),
                        information=f"Branch: {branch_name}",
                    ).exec()
                    return

                logger.info(
                    "Verifying changes are present in working directory before staging"
                )

                if git_utils.git_has_uncommitted_changes(repo, config):
                    logger.info("Uncommitted changes confirmed in working directory")
                else:
                    logger.warning(
                        "No uncommitted changes detected in working directory"
                    )

                logger.info(f"About to stage and commit file: {file_name}")

                try:
                    status = repo.status()
                    logger.info(f"Git status before staging: {dict(status)}")
                except Exception as e:
                    logger.warning(f"Could not get git status: {e}")

                stage_commit_result = git_utils.git_stage_commit(
                    repo=repo,
                    message=commit_message,
                    paths=[file_name],
                    config=config,
                )

                logger.info(f"Stage and commit result: {stage_commit_result}")

                if stage_commit_result == git_utils.GitStageCommitResult.COMMITTED:
                    logger.info(
                        "Successfully staged and committed changes on main branch"
                    )

                    try:
                        latest_commit_oid = repo.head.target
                        branch_ref.set_target(latest_commit_oid)
                        repo.head.set_target(branch_ref.target)
                        main_branch = repo.branches.local["main"]
                        main_branch.set_target(current_commit_oid)
                        logger.info(
                            f"Moved commit to branch: {branch_name} and reset main branch"
                        )
                    except Exception:
                        logger.exception("Failed to move commit to new branch")
                        repo.head.set_target(branch_ref.target)

                    push_result = git_utils.git_push(
                        repo=repo,
                        branch=branch_name,
                        username=github_username,
                        token=github_token,
                        config=config,
                    )

                    if push_result.is_successful():
                        logger.info("Successfully pushed to fork")
                        self._create_pull_request(
                            original_repo=original_repo,
                            fork_repo=fork_repo,
                            branch_name=branch_name,
                            database_version=database_version,
                            database_version_human_readable=database_version_human_readable,
                            commit_message=commit_message,
                        )
                    elif (
                        push_result
                        == git_utils.GitPushResult.REJECTED_NON_FAST_FORWARD
                    ):
                        logger.warning(
                            "Push rejected due to non-fast-forward. Attempting force push."
                        )
                        try:
                            push_result_force = git_utils.git_push(
                                repo=repo,
                                branch=branch_name,
                                username=github_username,
                                token=github_token,
                                config=config,
                                force=True,
                            )

                            if push_result_force.is_successful():
                                logger.info("Successfully force pushed to fork")
                                self._create_pull_request(
                                    original_repo=original_repo,
                                    fork_repo=fork_repo,
                                    branch_name=branch_name,
                                    database_version=database_version,
                                    database_version_human_readable=database_version_human_readable,
                                    commit_message=commit_message,
                                )
                            else:
                                InformationBox(
                                    title=self._tr("Force push failed"),
                                    text=self._tr(
                                        "Failed to force push changes to fork."
                                    ),
                                    information=str(push_result_force),
                                ).exec()

                        except Exception as e:
                            logger.exception("Error during force push")
                            InformationBox(
                                title=self._tr("Force push error"),
                                text=self._tr(
                                    "Error occurred while force pushing to remote."
                                ),
                                information=str(e),
                            ).exec()
                    else:
                        InformationBox(
                            title=self._tr("Push failed"),
                            text=self._tr("Failed to push changes to fork."),
                            information=str(push_result),
                        ).exec()
                elif stage_commit_result == git_utils.GitStageCommitResult.NO_CHANGES:
                    logger.info("No changes detected in database file after staging")
                    InformationBox(
                        title=self._tr("No changes"),
                        text=self._tr("No changes detected in database file."),
                        information=self._tr(
                            "The database appears to be up to date with the remote repository."
                        ),
                    ).exec()
                    return
                else:
                    InformationBox(
                        title=self._tr("Commit failed"),
                        text=self._tr("Failed to stage and commit changes."),
                        information=str(stage_commit_result),
                    ).exec()

        except Exception as e:
            logger.exception("Git operations failed")
            InformationBox(
                title=self._tr("Git operation error"),
                text=self._tr("Failed to perform git operations."),
                information=str(e),
            ).exec()
        finally:
            try:
                with git_utils.git_repository(repo_path, config) as repo:
                    if repo is not None:
                        try:
                            main_branch = repo.branches.local.get("main")  # type: ignore
                            if main_branch is not None:
                                repo.checkout(main_branch)
                                logger.info("Switched back to main branch")
                            else:
                                logger.warning(
                                    "Main branch not found, staying on current branch"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to switch to main branch: {e}")
            except Exception as e:
                logger.warning(f"Failed to switch back to main branch: {e}")

    def _create_pull_request(
        self,
        original_repo: Repository.Repository,
        fork_repo: Repository.Repository,
        branch_name: str,
        database_version: int,
        database_version_human_readable: str,
        commit_message: str,
    ) -> None:
        try:
            pr_title = f"DB update {database_version}"
            pr_body = f"Steam Workshop {commit_message}"
            base_branch = "main"
            head_branch = f"{fork_repo.owner.login}:{branch_name}"

            pull_request = original_repo.create_pull(
                title=pr_title,
                body=pr_body,
                base=base_branch,
                head=head_branch,
            )

            logger.info(f"Created pull request: {pull_request.html_url}")

            answer = show_dialogue_conditional(
                title=self._tr("Pull request created"),
                text=self._tr("Successfully created pull request!"),
                information=self._tr(
                    "Pull request created successfully.<br>Do you want to open it in your web browser?<br><br>URL: {url}"
                ).format(url=pull_request.html_url),
            )

            if answer == QMessageBox.StandardButton.Yes:
                try:
                    import webbrowser

                    webbrowser.open(pull_request.html_url)
                except Exception:
                    logger.exception("Failed to open browser")

        except Exception as e:
            logger.exception("Failed to create pull request")
            InformationBox(
                title=self._tr("Pull request failed"),
                text=self._tr("Failed to create pull request."),
                information=self._tr(
                    "The changes were pushed to your fork successfully, but the pull request creation failed.<br><br>"
                    + "You can manually create a pull request on GitHub.<br><br>Error: {error}"
                ).format(error=str(e)),
            ).exec()


