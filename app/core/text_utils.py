"""Text, time, and URL parsing utilities.

No Qt dependencies. Safe for all layers.
"""

from __future__ import annotations

from datetime import datetime
from re import search
from time import localtime, strftime


def get_relative_time(timestamp: int) -> str:
    """Convert a timestamp to a relative time string (e.g. '2 days ago')."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        delta = now - dt

        if delta.days > 365:
            return f"{delta.days // 365} years ago"
        elif delta.days > 30:
            return f"{delta.days // 30} months ago"
        elif delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"
    except (ValueError, TypeError):
        return "Invalid timestamp"


def format_time_display(timestamp: int | None) -> tuple[str, int | None]:
    """Format a timestamp into absolute and relative time strings for display."""
    if timestamp is None or timestamp <= 0:
        return "Unknown", None

    try:
        abs_time = strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))
        rel_time = get_relative_time(timestamp)
        return f"{abs_time} | {rel_time}", timestamp
    except (ValueError, TypeError, OSError):
        return "Invalid timestamp", None


def extract_page_title_steam_browser(title: str) -> str | None:
    """Extract the page title from a Steam Workshop Browser page title."""
    if match := search(r"Steam (?:Community|Workshop)::(.*)", title):
        return match.group(1)
    else:
        return None


def extract_git_dir_name(url: str) -> str:
    """Extract the directory name from a git URL."""
    return url.rstrip("/").rsplit("/", maxsplit=1)[-1].removesuffix(".git")


def extract_git_user_or_org(url: str) -> str:
    """Extract the organization or user name from a git URL."""
    return url.rstrip("/").rsplit("/", maxsplit=2)[-2].removesuffix(".git")


def check_valid_http_git_url(url: str) -> bool:
    """Check if a given URL is a valid http/s git URL."""
    return url and url != "" and url.startswith("http://") or url.startswith("https://")
