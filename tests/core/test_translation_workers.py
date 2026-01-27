"""Unit tests for the in-app translation workers (``app.core.translation_workers``).

The workers are QThread subclasses used by the Translation Manager UI to run
blocking subprocess / async translation work off the GUI thread. Their ``run``
methods are plain synchronous callables, so they can be invoked directly with a
real ``QApplication`` present (the ``qapp`` fixture) and the side-effecting
helpers mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.core.translation_workers import (
    SubprocessWorker,
    TranslateBatchWorker,
    ValidateWorker,
)


def test_subprocess_worker_emits_finished(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    results: list[bool] = []
    worker = SubprocessWorker(lambda lang: True, "lupdate", "de_DE")
    worker.finished.connect(lambda ok: results.append(ok))
    worker.run()
    assert results == [True]


def test_subprocess_worker_propagates_failure(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    results: list[bool] = []
    worker = SubprocessWorker(lambda lang: False, "lrelease", None)
    worker.finished.connect(lambda ok: results.append(ok))
    worker.run()
    assert results == [False]


def test_validate_worker_emits_result(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.core.translation_workers.validate_translation",
        lambda lang: (["issue1"], 2),
    )
    captured: list[tuple[list[str], int]] = []
    worker = ValidateWorker("de_DE")
    worker.finished.connect(lambda issues, fixed: captured.append((issues, fixed)))
    worker.run()
    assert captured == [(["issue1"], 2)]


def test_translate_batch_worker_emits_result(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc = MagicMock()
    monkeypatch.setattr(
        "app.core.translation_workers.create_translation_service",
        lambda name, **k: svc,
    )
    monkeypatch.setattr(
        "app.core.translation_workers.translate_language_batch",
        AsyncMock(return_value=(3, 1)),
    )
    captured: list[tuple[bool, int, int]] = []
    worker = TranslateBatchWorker("de_DE", "google")
    worker.finished.connect(lambda ok, t, f: captured.append((ok, t, f)))
    worker.run()
    assert captured == [(True, 3, 1)]
