import json
import os
import stat
import sys
import tempfile
import time
from typing import Any

from loguru import logger

_REPLACE_ATTEMPTS = 5
_REPLACE_RETRY_DELAY = 0.05


def _clear_read_only_flag(destination: str) -> bool:
    if sys.platform != "win32":
        return False

    try:
        mode = os.stat(destination).st_mode
        if mode & stat.S_IWRITE:
            return False
        os.chmod(destination, mode | stat.S_IWRITE)
    except OSError:
        return False

    logger.warning(
        f"Cleared the read-only attribute of {destination} so it can be written"
    )
    return True


def _replace_with_retry(source: str, destination: str) -> None:
    """Replace a file, tolerating short-lived Windows file locks."""
    attempt = 0
    cleared_read_only = False
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if not cleared_read_only and _clear_read_only_flag(destination):
                cleared_read_only = True
                continue
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(_REPLACE_RETRY_DELAY * 2**attempt)
            attempt += 1


def atomic_json_dump(data: Any, path: str, **kwargs: Any) -> None:
    dirpath = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(suffix=".json", dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, **kwargs)
            f.flush()
            os.fsync(fd)
        _replace_with_retry(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise
