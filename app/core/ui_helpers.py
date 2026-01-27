"""UI and platform helpers — clipboard, file openers, warnings, network checks.

Depends on ``app.ui.dialogue`` for user-facing dialogs. Not safe for leaf
layers that must avoid UI imports.
"""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any, Callable

import requests
from loguru import logger
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

import app.ui.dialogue as dialogue
from app.core.app_info import AppInfo
from app.net import http


def copy_to_clipboard_safely(text: str) -> None:
    """Safely copies text to clipboard."""
    try:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        dialogue.show_fatal_error(
            title=QCoreApplication.translate(
                "copy_to_clipboard_safely", "Failed to copy to clipboard."
            ),
            text=QCoreApplication.translate(
                "copy_to_clipboard_safely",
                "RimDex failed to copy the text to your clipboard. Please copy it manually.",
            ),
            details=str(e),
        )


def open_url_browser(url: str) -> None:
    """Open a url in a user's default web browser."""
    logger.info(f"USER ACTION: Opening url {url}")
    webbrowser.open(url)


def platform_specific_open(path: str | Path) -> None:
    """Open a folder in the platform-specific file-explorer or a file in the
    default application.
    """
    logger.info(f"USER ACTION: opening {path}")
    p = Path(path)
    path = str(path)
    if sys.platform == "darwin":
        logger.info(f"Opening {path} with subprocess open on MacOS")
        if p.is_dir() and p.suffix == ".app":
            subprocess.Popen(["open", path, "-R"])
        else:
            subprocess.Popen(["open", path])
    elif sys.platform == "win32":
        logger.info(f"Opening {path} with startfile on Windows")
        try:
            os.startfile(path)
        except OSError as e:
            if e.winerror == -2147221003:  # Application not found
                logger.warning(
                    f"No default application found for {path}, trying notepad"
                )
                try:
                    subprocess.Popen(["notepad.exe", path])
                except Exception as notepad_error:
                    logger.error(f"Failed to open with notepad: {notepad_error}")
                    dialogue.show_warning(
                        title="Failed to open file",
                        text="Could not open the file",
                        information=f"No default application is associated with this file type: {p.suffix}<br><br>Please manually associate an application with {p.suffix} files or open the file manually.",
                        details=str(e),
                    )
            else:
                raise
    elif sys.platform == "linux":
        logger.info(f"Opening {path} with xdg-open on Linux")
        subprocess.Popen(["xdg-open", path], env=dict(os.environ, LD_LIBRARY_PATH=""))
    else:
        logger.error("Attempting to open directory on an unknown system")


def restart_application() -> None:
    """Restart the application."""
    if getattr(sys, "frozen", False):
        cmd = [sys.executable] + sys.argv[1:]
    else:
        cmd = [sys.executable, "-m", "app"] + sys.argv[1:]

    subprocess.Popen(cmd)

    instance = QApplication.instance()
    if instance:
        logger.info("Restarting the application")
        instance.quit()
    else:
        logger.warning("No QApplication instance found, cannot restart the application")


def show_no_steam_warning() -> None:
    """Show warning that Steam is not detected."""
    dialogue.show_warning(
        title=QCoreApplication.translate("SteamworksInterface", "Steam Not Detected"),
        text=QCoreApplication.translate(
            "SteamworksInterface", "Steam Integration Unavailable"
        ),
        information=QCoreApplication.translate(
            "SteamworksInterface",
            "RimDex could not detect Steam client or it may be unresponsive.<br><br>"
            "Please make sure Steam is installed and running.<br><br>"
            "If you are a Steam user, please check that Steam is running and that you are logged in.<br><br>"
            "Try restarting Steam.",
        ),
        details=QCoreApplication.translate(
            "SteamworksInterface",
            "If you are still facing issues even after Steam is installed and running, please report this issue to https://github.com/RimDex/RimDex/issues",
        ),
    )


def show_snap_steam_warning() -> None:
    """Show snap steam warning in a thread-safe manner."""
    dialogue.show_warning(
        title=QCoreApplication.translate("SteamworksInterface", "Snap Steam Detected"),
        text=QCoreApplication.translate(
            "SteamworksInterface", "Steam Integration Unavailable"
        ),
        information=QCoreApplication.translate(
            "SteamworksInterface",
            "For full Steam support, please install native Steam "
            "from the official repository.",
        ),
        details=QCoreApplication.translate(
            "SteamworksInterface",
            "Snap Steam is sandboxed and incompatible with Steamworks API",
        ),
    )


def check_internet_connection(timeout: float = 10) -> bool:
    """Check if there is an active internet connection.

    :param timeout: Timeout in seconds for each connection attempt
    :return: True if at least one service is accessible, False otherwise
    """
    urls = [
        "https://steamcommunity.com",
        "https://github.com",
    ]

    failed_urls = []

    for url in urls:
        try:
            http.head(url, timeout=timeout)
            logger.debug(f"Internet connection verified via {url}")
            return True
        except requests.exceptions.RequestException as e:
            logger.debug(f"Connection to {url} failed: {e}")
            failed_urls.append(url)

    logger.error(
        f"No internet connection detected. Failed to reach: {', '.join(failed_urls)}"
    )
    dialogue.show_internet_connection_error(failed_urls=failed_urls)
    return False


def upload_data_to_0x0_st(path: str) -> tuple[bool, str]:
    """Upload data to https://0x0.st/

    :param path: a string path to a file containing data to upload
    :return: a tuple of (success, url_or_error)
    """
    logger.info(f"Uploading data to https://0x0.st/: {path}")
    try:
        with open(path, "rb") as f:
            headers = {"User-Agent": f"RimDex/{AppInfo().app_version}"}
            request = http.post(
                url="https://0x0.st/",
                files={"file": (Path(path).name, f)},
                headers=headers,
            )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error. Failed to upload data to https://0x0.st: {e}")
        return False, str(e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error. Failed to upload data to https://0x0.st: {e}")
        return False, str(e)

    if request.status_code == 200:
        url = request.text.strip()
        logger.info(f"Uploaded! Uploaded data can be found at: {url}")
        return True, url
    else:
        body_snippet = request.text.strip()
        logger.warning(
            f"Failed to upload data to https://0x0.st. Status code: {request.status_code}; body: {body_snippet[:200]}"
        )
        return False, f"Status code: {request.status_code}\n{body_snippet}"


def assign_event_handler(widget: Any, name: str, handler: Callable[..., Any]) -> None:
    """Assign a custom event handler (e.g. ``mousePressEvent`` / ``dropEvent``)
    to a Qt widget without a per-call ``# type: ignore[method-assign]``.

    Reassigning a widget's event method is a legitimate Qt pattern, but mypy
    flags the attribute assignment as ``method-assign``. The suppression is
    concentrated here so the many call sites stay clean. The runtime behavior
    is identical to a direct ``widget.<name> = handler`` assignment.
    """
    setattr(widget, name, handler)
