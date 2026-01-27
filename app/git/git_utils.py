"""Backwards-compatible re-export shim for the split git modules.

Historically this module (1859 LOC at the time of the split) contained a mix
of three things:

1. The actual pygit2-backed operations (``git_clone``, ``git_pull``,
   ``git_push``, ``git_stage_commit``, ``git_stash`` family, …).
2. The UI/status reporting concerns (exception type, operation enum,
   notification ``Protocol`` and default handler, ``GitOperationConfig``,
   the centralised ``_handle_git_error`` helper).
3. URL parsing helpers (``parse_git_url``, ``git_get_repo_name``,
   ``ParsedGitUrl``).

The P1 task in ``TODO.md`` ("Split ``git/git_utils.py`` (operations vs.
UI/status reporting)") is now implemented by:

* :mod:`app.git.git_operations`  — the operations (1) and the pure URL
  parsing helpers (3); free of Qt dialogs and notification logic.
* :mod:`app.git.git_notifications` — the UI/status reporting concerns
  (2).  Owns the exception type, the operation enum, the notification
  ``Protocol`` and default handler, the configuration dataclass, and the
  centralised error-to-dialog helper.

This module remains so that the (many) existing imports of
``app.git.git_utils`` continue to work, but it is now a thin shim that
re-exports the public API from the two new modules.  New code should
import directly from ``app.git.git_operations`` or
``app.git.git_notifications``.
"""

from __future__ import annotations

from app.git.git_notifications import (  # noqa: F401 — re-export
    CORRUPTION_INDICATORS,
    DefaultNotificationHandler,
    GitError,
    GitNotificationHandler,
    GitOperationConfig,
    GitOperationType,
    _handle_git_error,
)
from app.git.git_operations import (  # noqa: F401 — re-export
    GitCloneResult,
    GitPullResult,
    GitPushResult,
    GitStageCommitResult,
    GitStashResult,
    ParsedGitUrl,
    _attempt_repository_repair,
    _fetch_with_timeout,
    _is_repository_corrupted,
    _parse_https_git_url,
    _parse_ssh_git_url,
    get_config,
    get_latest_commit_info,
    get_repository_latest_commit,
    git_check_updates,
    git_cleanup,
    git_clone,
    git_discover,
    git_get_commit_info,
    git_get_current_branch,
    git_get_remote_url,
    git_get_repo_name,
    git_get_status,
    git_has_uncommitted_changes,
    git_is_clean,
    git_is_repository,
    git_pull,
    git_push,
    git_repository,
    git_stage_commit,
    git_stash,
    git_stash_drop,
    git_stash_list,
    parse_git_url,
)

# ``pygit2`` was historically re-exported from here so callers could write
# ``from app.git.git_utils import pygit2``.  Preserve that for backwards
# compatibility by re-exporting it from the same source the operations use.
from app.git.pygit2_loader import pygit2  # noqa: E402, F401 — re-export

__all__ = [
    # notifications / UI
    "CORRUPTION_INDICATORS",
    "DefaultNotificationHandler",
    "GitError",
    "GitNotificationHandler",
    "GitOperationConfig",
    "GitOperationType",
    "_handle_git_error",
    # operations
    "GitCloneResult",
    "GitPullResult",
    "GitPushResult",
    "GitStageCommitResult",
    "GitStashResult",
    "ParsedGitUrl",
    "_attempt_repository_repair",
    "_fetch_with_timeout",
    "_is_repository_corrupted",
    "_parse_https_git_url",
    "_parse_ssh_git_url",
    "get_config",
    "get_latest_commit_info",
    "get_repository_latest_commit",
    "git_check_updates",
    "git_cleanup",
    "git_clone",
    "git_discover",
    "git_get_commit_info",
    "git_get_current_branch",
    "git_get_remote_url",
    "git_get_repo_name",
    "git_get_status",
    "git_has_uncommitted_changes",
    "git_is_clean",
    "git_is_repository",
    "git_pull",
    "git_push",
    "git_repository",
    "git_stage_commit",
    "git_stash",
    "git_stash_drop",
    "git_stash_list",
    "parse_git_url",
    # re-export
    "pygit2",
]
