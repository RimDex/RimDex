"""QThread workers for blocking translation operations.

Each worker wraps a blocking or async operation (subprocess calls, translation
API batches) and exposes Qt signals for progress/result/error reporting.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import Callable
from typing import Any, Optional

import lxml.etree as ET
from loguru import logger
from PySide6.QtCore import QThread, Signal

from app.core.translation_utils import (
    UnfinishedItem,
    find_unfinished_translations,
    save_ts_file,
    should_skip_translation,
    validate_translation,
)
from app.models.translation import (
    LOCALES_DIR,
    get_translation_cache,
    get_translation_config,
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
        ts_file = LOCALES_DIR / f"{self._language}.ts"
        backup_file = ts_file.with_suffix(".ts.backup")

        if not ts_file.exists():
            self.error.emit(f"File not found: {ts_file}")
            return False

        # Backup
        shutil.copy2(ts_file, backup_file)
        self.progress.emit(f"Backup created: {backup_file}")

        self._translated = 0
        self._failed = 0

        try:
            service = create_translation_service(
                self._service_name, **self._service_kwargs
            )
            tree = ET.parse(str(ts_file))
            unfinished = find_unfinished_translations(tree)

            if not unfinished:
                self.progress.emit(f"No unfinished translations for {self._language}")
                if backup_file.exists():
                    backup_file.unlink()
                return True

            self.progress.emit(f"Found {len(unfinished)} unfinished translations")
            config = get_translation_config()
            cache = get_translation_cache()
            semaphore = asyncio.Semaphore(config.max_concurrent_requests)

            async def _translate_one(i: int, item: UnfinishedItem) -> tuple[int, str]:
                if should_skip_translation(item.source):
                    return i, ""
                async with semaphore:
                    try:
                        result = await asyncio.wait_for(
                            service.translate(item.source, self._language, "en_US"),
                            timeout=config.timeout_config.default_timeout,
                        )
                        return i, result or ""
                    except Exception as e:
                        logger.warning("Translation failed for [%d]: %s", i, e)
                        return i, ""

            tasks = [_translate_one(i, item) for i, item in enumerate(unfinished)]
            results = await asyncio.gather(*tasks)

            for i, translated in results:
                item = unfinished[i]
                if not translated:
                    self._failed += 1
                    continue
                self._translated += 1
                is_plural = item.element.getparent().getparent().get("numerus") == "yes"
                if is_plural:
                    forms = item.element.findall("numerusform")
                    if forms:
                        forms[0].text = translated
                else:
                    item.element.text = translated
                item.element.attrib.pop("type", None)
                self.item_done.emit(i, item.source, translated)

            if self._failed == 0 or config.use_cache:
                save_ts_file(tree, ts_file)
                cache.save()
                self.progress.emit(
                    f"Saved {self._translated} translations to {ts_file}"
                )
                if backup_file.exists():
                    backup_file.unlink()

            return True

        except Exception as e:
            logger.error("Translation batch failed: %s", e)
            if backup_file.exists():
                shutil.copy2(backup_file, ts_file)
                self.progress.emit("Restored from backup")
            return False
