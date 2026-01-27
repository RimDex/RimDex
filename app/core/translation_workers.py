"""QThread workers for blocking translation operations.

Each worker wraps a blocking or async operation (subprocess calls, translation
API batches) and exposes Qt signals for progress/result/error reporting.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, Optional

from loguru import logger
from PySide6.QtCore import QThread, Signal

from app.core.translation_utils import (
    translate_language_batch,
    validate_translation,
)
from app.services.translation_service import create_translation_service

# ---------------------------------------------------------------------------
# SubprocessWorker (lupdate / lrelease)
# ---------------------------------------------------------------------------


class SubprocessWorker(QThread):
    """Generic worker that runs a blocking callable (e.g. lupdate/lrelease)."""

    progress = Signal(str)
    finished = Signal(bool)

    def __init__(
        self,
        func: Callable[[Optional[str]], bool],
        label: str,
        language: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._func = func
        self._label = label
        self._language = language

    def run(self) -> None:
        lang_label = self._language or "all"
        self.progress.emit(f"{self._label} for {lang_label}...")
        ok = self._func(self._language)
        self.finished.emit(ok)


# ---------------------------------------------------------------------------
# ValidateWorker
# ---------------------------------------------------------------------------


class ValidateWorker(QThread):
    """Validate translation files in a background thread."""

    progress = Signal(str)
    finished = Signal(list, int)  # list of issue strings, fixed_count

    def __init__(self, language: Optional[str] = None) -> None:
        super().__init__()
        self._language = language

    def run(self) -> None:
        self.progress.emit("Validating translation files...")
        issues, fixed_count = validate_translation(self._language)
        self.finished.emit(issues, fixed_count)


# ---------------------------------------------------------------------------
# TranslateBatchWorker
# ---------------------------------------------------------------------------


class TranslateBatchWorker(QThread):
    """Translate all unfinished entries for one language in a background thread.

    Runs the async translation loop inside ``asyncio.run()``.
    """

    progress = Signal(str)
    item_done = Signal(int, str, str)  # index, source, translation
    finished = Signal(bool, int, int)  # success, translated_count, failed_count
    error = Signal(str)

    def __init__(
        self,
        language: str,
        service_name: str = "google",
        service_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self._language = language
        self._service_name = service_name
        self._service_kwargs = service_kwargs or {}

    def run(self) -> None:
        try:
            ok = asyncio.run(self._do_translate())
            if ok:
                self.finished.emit(True, self._translated, self._failed)
            else:
                self.finished.emit(False, self._translated, self._failed)
        except Exception as e:
            logger.error("TranslateBatchWorker failed: %s", e)
            self.error.emit(str(e))
            self.finished.emit(False, 0, 0)

    async def _do_translate(self) -> bool:
        try:
            service = create_translation_service(
                self._service_name, **self._service_kwargs
            )

            def _progress(msg: str) -> None:
                self.progress.emit(msg)

            def _item_done(idx: int, src: str, tr: str) -> None:
                self.item_done.emit(idx, src, tr)

            def _error(msg: str) -> None:
                self.error.emit(msg)

            translated, failed = await translate_language_batch(
                self._language,
                service,
                on_progress=_progress,
                on_item_done=_item_done,
                on_error=_error,
            )
            self._translated = translated
            self._failed = failed
            return True

        except Exception as e:
            logger.error("TranslateBatchWorker failed: %s", e)
            self.error.emit(str(e))
            return False
