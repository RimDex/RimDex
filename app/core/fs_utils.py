"""Filesystem utilities — directory traversal, deletion, permissions, and formatting.

No Qt dependencies. Safe for leaf layers (``services/``, ``utils/``).
"""

from __future__ import annotations

import os
import shutil
import sys
from errno import EACCES
from pathlib import Path
from re import sub
from stat import S_IRWXG, S_IRWXO, S_IRWXU
from typing import Any, Callable, Generator

import vdf  # type: ignore
from loguru import logger

import app.ui.dialogue as dialogue
from app.utils.platform.windows import scanpath_win32


def chunks(_list: list[Any], limit: int) -> Generator[list[Any], None, None]:
    """Split list into chunks no larger than the configured limit."""
    for i in range(0, len(_list), limit):
        yield _list[i : i + limit]


def rmtree(path: str | Path, **kwargs: Any) -> bool:
    """Wrapper for improved rmtree error handling.

    Checks if the path exists and is a directory before attempting to delete it.
    If any OSErrors occur, a warning dialog is shown to the user.

    :param path: Path to directory to be deleted.
    :type path: str | Path
    :param kwargs: Additional keyword arguments to pass to shutil.rmtree.
    :return: True if the directory was successfully deleted, False otherwise.
    """
    from PySide6.QtCore import QCoreApplication

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        logger.error(f"Tried to delete directory that does not exist: {path}")
        dialogue.show_warning(
            title=QCoreApplication.translate("rmtree", "Failed to remove directory"),
            text=QCoreApplication.translate(
                "rmtree", "RimDex tried to remove a directory that does not exist."
            ),
            details=QCoreApplication.translate(
                "rmtree", "Directory does not exist: {path}"
            ).format(path=path),
        )
        return False

    if not path.is_dir():
        logger.error(f"rmtree path is not a directory: {path}")
        dialogue.show_warning(
            title=QCoreApplication.translate("rmtree", "Failed to remove directory"),
            text=QCoreApplication.translate(
                "rmtree", "RimDex tried to remove a directory that is not a directory."
            ),
            details=QCoreApplication.translate(
                "rmtree", "Path is not a directory: {path}"
            ).format(path=path),
        )
        return False

    try:
        shutil.rmtree(path, **kwargs)
    except OSError as e:
        if sys.platform == "win32":
            error_code = e.winerror
        else:
            error_code = e.errno
        logger.error(f"Failed to remove directory: {e}")
        dialogue.show_warning(
            title=QCoreApplication.translate("rmtree", "Failed to remove directory"),
            text=QCoreApplication.translate(
                "rmtree", "An OSError occurred while trying to remove a directory."
            ),
            information=QCoreApplication.translate(
                "rmtree",
                "{e.strerror} occurred at {e.filename} with error code {error_code}.",
            ).format(
                e=e,
                error_code=error_code,
            ),
            details=str(e),
        )
        return False

    return True


def delete_files_with_condition(
    directory: Path | str, condition: Callable[[str], bool]
) -> bool:
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return False

    for root, dirs, files in os.walk(directory):
        for file in files:
            if condition(file):
                file_path = str((Path(root) / file))
                try:
                    os.remove(file_path)
                except OSError as e:
                    attempt_chmod(os.remove, file_path, e)
                finally:
                    logger.debug(f"Deleted: {file_path}")

    for root, dirs, _ in os.walk(directory, topdown=False):
        for _dir in dirs:
            dir_path = str((Path(root) / _dir))
            if not os.listdir(dir_path):
                shutil.rmtree(
                    dir_path,
                    ignore_errors=False,
                    onexc=attempt_chmod,
                )
                logger.debug(f"Deleted: {dir_path}")
    if not os.listdir(directory):
        shutil.rmtree(
            directory,
            ignore_errors=False,
            onexc=attempt_chmod,
        )
        logger.debug(f"Deleted: {directory}")
        return True
    else:
        return False


def delete_files_except_extension(directory: Path | str, extension: str) -> bool:
    return delete_files_with_condition(
        directory, lambda file: not file.endswith(extension)
    )


def delete_files_only_extension(directory: Path | str, extension: str) -> bool:
    return delete_files_with_condition(directory, lambda file: file.endswith(extension))


def scanpath(
    path: Path | str,
) -> Generator[os.DirEntry[str] | Any, None, None]:
    if sys.platform == "win32":
        try:
            yield from scanpath_win32(path)
        except OSError as e:
            logger.error(f"An unexpected Win32 API error for scanpath occurred: {e}")
    else:
        try:
            with os.scandir(path) as it:
                yield from it
        except OSError as e:
            logger.error(f"os.scandir failed for directory {path}: {e}")


def directories(mods_path: Path | str) -> list[str]:
    try:
        return [entry.path for entry in scanpath(mods_path) if entry.is_dir()]
    except OSError as e:
        logger.error(f"Error reading directory {mods_path}: {e}")
        return []


def attempt_chmod(
    func: Callable[[str], Any], path: str, excinfo: BaseException
) -> bool:
    if excinfo is not None and isinstance(excinfo, OSError):
        if (
            func in (os.rmdir, os.remove, os.unlink, os.listdir)
            and excinfo.errno == EACCES
        ):
            os.chmod(path, S_IRWXU | S_IRWXG | S_IRWXO)  # 0777
            try:
                func(path)
                return True
            except Exception as e:
                logger.warning(
                    f"attempt_chmod for {func.__name__} double failure at {path}: {e}"
                )
                return False

    return False


def handle_remove_read_only(
    func: Callable[[str], Any],
    path: str,
    exc: tuple[type[BaseException], BaseException, Any] | tuple[None, None, None],
) -> None:
    """Legacy onerror callback for shutil.rmtree — prefer ``attempt_chmod``."""
    excvalue = exc[1]
    if excvalue is not None and isinstance(excvalue, OSError):
        if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == EACCES:
            os.chmod(path, S_IRWXU | S_IRWXG | S_IRWXO)  # 0777
            func(path)
        else:
            raise


def sanitize_filename(filename: str) -> str:
    forbidden_chars = r'[<>:"/\|?*\0]'
    sanitized_filename = sub(forbidden_chars, "", filename)
    sanitized_filename = sanitized_filename.rstrip(". ")
    return sanitized_filename


def flatten_to_list(obj: Any) -> list[Any] | dict[Any, Any] | Any:
    """Recursively flatten a nested object as much as possible.

    Converts all sets to lists. If the object is a dictionary, it maintains
    the keys and recurses on the values.
    """
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [flatten_to_list(e) for e in obj]
    elif isinstance(obj, tuple):
        return [flatten_to_list(e) for e in obj]
    elif isinstance(obj, dict):
        return {k: flatten_to_list(v) for k, v in obj.items()}
    else:
        return obj


def format_file_size(size_in_bytes: int) -> str:
    """Format bytes to a human-readable string."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_path_up_to_string(
    path: Path, stop_string: str, exclude: bool = False
) -> Path | str:
    """Returns a Path up to the stop_string."""
    parts = path.parts
    try:
        stop_idx = parts.index(stop_string)
        if exclude:
            return Path(*parts[:stop_idx])
        else:
            return Path(*parts[: stop_idx + 1])
    except ValueError:
        return ""


def find_steam_rimworld(steam_folder: Path | str) -> str:
    """Find RimWorld installation path via Steam's libraryfolders.vdf.

    :param steam_folder: Path to steam installation
    :return: RimWorld path if found, blank str otherwise
    """
    from io import TextIOWrapper

    def __load_data(f: TextIOWrapper) -> str:
        rimworld_path = ""
        data = vdf.load(f)
        library_folders = data.get("libraryfolders", None)
        if not library_folders:
            return ""
        for _, folder in library_folders.items():
            if "294100" in folder.get("apps", {}):
                rimworld_path = folder.get("path", "")
                break
        return rimworld_path

    rimworld_path = ""
    steam_folder = Path(steam_folder)

    primary_library = "config/libraryfolders.vdf"
    backup_library = "steamapps/libraryfolders.vdf"

    if os.path.exists(steam_folder / primary_library):
        logger.debug(f"Attempting to get RimWorld path from {primary_library}")
        try:
            with open(steam_folder / primary_library, "r") as f:
                rimworld_path = __load_data(f)
        except Exception:
            logger.warning(f"Failed to parse {primary_library}", exc_info=True)
            return rimworld_path
    elif os.path.exists(steam_folder / backup_library):
        logger.debug(f"Attempting to get RimWorld path from {backup_library}")
        try:
            with open(steam_folder / backup_library, "r") as f:
                rimworld_path = __load_data(f)
        except Exception:
            logger.warning(f"Failed to parse {backup_library}", exc_info=True)
            return rimworld_path
    else:
        logger.warning("Failed retrieving RimWorld path from libraryfolders.vdf")
        return rimworld_path

    full_rimworld_path = Path(rimworld_path) / "steamapps/common/RimWorld"

    return str(full_rimworld_path) if rimworld_path else rimworld_path
