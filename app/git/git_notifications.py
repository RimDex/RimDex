"""UI/status reporting layer for git operations.

This module is the "UI" half of the ``git_utils`` split recommended in
``TODO.md`` (P1 — split ``git/git_utils.py`` (operations vs. UI/status
reporting)).  It owns:

* the user-facing exception type (:class:`GitError`),
* the operation enum used for categorisation (:class:`GitOperationType`),
* the notification ``Protocol`` + default Qt-based implementation,
* the configuration dataclass :class:`GitOperationConfig` (which holds the
  notification handler and timeouts — strictly UI/UX concerns), and
* the centralised :func:`_handle_git_error` helper that delegates to the
  configured handler.

The "operations" half (the actual pygit2 wrappers) lives in
:mod:`app.git.git_operations`.  :mod:`app.git.git_utils` remains as a
backward-compatible re-export shim.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Protocol

from loguru import logger
from PySide6.QtWidgets import QMessageBox

from app.ui.dialogue import InformationBox


class GitError(Exception):
    """Base exception for git operations."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class GitOperationType(Enum):
    """Types of git operations for better error categorization."""

    DISCOVER = "discover"
    CLONE = "clone"
    PULL = "pull"
    PUSH = "push"
    STAGE_COMMIT = "stage_commit"
    STASH = "stash"
    STATUS = "status"
    COMMIT_INFO = "commit_info"


class GitNotificationHandler(Protocol):
    """Protocol for handling git operation notifications."""

    def show_error(
        self, title: str, message: str, details: Optional[str] = None
    ) -> None:
        """Show error notification to user."""
        ...


class DefaultNotificationHandler:
    """Default implementation using QMessageBox for notifications."""

    def show_error(
        self, title: str, message: str, details: Optional[str] = None
    ) -> None:
        """Show error notification using InformationBox."""
        InformationBox(
            title=title,
            text=message,
            icon=QMessageBox.Icon.Critical,
            details=details,
        ).exec()


@dataclass
class GitOperationConfig:
    """Configuration for git operations (UI/UX concerns only).

    The configuration holds the notification handler and the network/fetch
    timeouts.  The notification handler is a UI concern and therefore lives
    with the rest of the UI/status reporting code in this module.
    """

    notify_errors: bool = True
    notification_handler: Optional[GitNotificationHandler] = None
    fetch_timeout: int = 30  # Timeout for fetch operations in seconds
    connection_timeout: int = 10  # Timeout for connection checks in seconds

    def __post_init__(self) -> None:
        if self.notification_handler is None:
            self.notification_handler = DefaultNotificationHandler()

    def get_handler(self) -> GitNotificationHandler:
        """Get the notification handler, ensuring it's not None."""
        return self.notification_handler or DefaultNotificationHandler()

    @classmethod
    def create_silent(cls) -> "GitOperationConfig":
        """Create a config that suppresses error notifications."""
        return cls(notify_errors=False)

    @classmethod
    def create_with_handler(
        cls, handler: GitNotificationHandler
    ) -> "GitOperationConfig":
        """Create a config with a specific notification handler."""
        return cls(notify_errors=True, notification_handler=handler)

    @classmethod
    def create_with_timeout(
        cls, fetch_timeout: int = 30, connection_timeout: int = 10
    ) -> "GitOperationConfig":
        """Create a config with custom timeout values."""
        return cls(fetch_timeout=fetch_timeout, connection_timeout=connection_timeout)


# Corruption indicators are shared by the centralised error handler and the
# corruption detection helper in :mod:`app.git.git_operations`.  Keeping the
# list here keeps the classification logic in one place.
CORRUPTION_INDICATORS: tuple[str, ...] = (
    "object not found",
    "missing object",
    "bad object",
    "corrupted",
    "fatal",
    "pack corruption",
)


def _handle_git_error(
    operation: GitOperationType,
    error: Exception,
    config: GitOperationConfig,
    context: str = "",
    repo_path: Optional[str | Any] = None,
    repo_url: Optional[str] = None,
    repo: Optional[Any] = None,
    repair_callback: Optional[Callable[..., bool]] = None,
    **kwargs: Any,
) -> bool:
    """Centralized error handling for git operations.

    Args:
        operation: The type of git operation that failed.
        error: The exception that occurred.
        config: Configuration for error handling.
        context: Additional context about the operation.
        repo_path: Path to the repository (used for corruption repair).
        repo_url: URL of the repository (used for re-cloning).
        repo: Repository object (used for cleanup before repair).
        repair_callback: Callable(repo_path, repo_url, repo) -> bool for
            corruption repair. Passed by callers in git_operations to avoid
            an import cycle.
        **kwargs: Additional context for error messages.

    Returns:
        True if the error was due to corruption and repair was attempted, False otherwise.
    """
    error_msg = str(error)
    logger.error(
        f"Git {operation.value} operation failed{f' ({context})' if context else ''}: {error_msg}"
    )

    is_corruption = any(
        indicator in error_msg.lower() for indicator in CORRUPTION_INDICATORS
    )

    if is_corruption and repo_path and repair_callback is not None:
        logger.warning(f"Detected repository corruption in: {repo_path}")
        if repair_callback(repo_path, repo_url, repo):
            logger.info(f"Repository corruption repair successful: {repo_path}")
            return True

    if config.notify_errors:
        title_map = {
            GitOperationType.DISCOVER: "Git Repository Discovery Error",
            GitOperationType.CLONE: "Git Clone Error",
            GitOperationType.PULL: "Git Pull Error",
            GitOperationType.PUSH: "Git Push Error",
            GitOperationType.STAGE_COMMIT: "Git Stage and Commit Error",
            GitOperationType.STASH: "Git Stash Error",
            GitOperationType.STATUS: "Git Status Error",
            GitOperationType.COMMIT_INFO: "Git Commit Info Error",
        }

        message = f"Failed to {operation.value} {context}".strip()
        if is_corruption:
            message += " (Repository corruption detected and repair attempted)"

        config.get_handler().show_error(
            title=title_map.get(operation, "Git Operation Error"),
            message=message,
            details=error_msg,
        )

    return False


__all__ = [
    "CORRUPTION_INDICATORS",
    "DefaultNotificationHandler",
    "GitError",
    "GitNotificationHandler",
    "GitOperationConfig",
    "GitOperationType",
    "_handle_git_error",
]
