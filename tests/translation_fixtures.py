"""Shared fixtures for the in-app translation unit tests.

Extracted so the (autouse) translation-state reset and the isolated ``locales``
tmp dir are defined once instead of being duplicated across the
``test_translation_*`` modules (the project's jscpd gate is strict).
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from app.models.translation import (
    TranslationConfig,
    get_translation_cache,
    set_translation_config,
)


@pytest.fixture(autouse=True)
def reset_translation_state() -> Generator[None, None, None]:
    """Keep the global translation config/cache singletons clean per test."""
    set_translation_config(TranslationConfig(use_cache=False))
    get_translation_cache()._cache = {}
    yield
    set_translation_config(TranslationConfig())
    get_translation_cache()._cache = {}


@pytest.fixture
def locales_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``LOCALES_DIR`` at an isolated temp dir for file-touching tests."""
    d = Path(tmp_path) / "locales"
    d.mkdir()
    import app.core.translation_utils as tu

    monkeypatch.setattr(tu, "LOCALES_DIR", d)
    monkeypatch.setattr("app.models.translation.LOCALES_DIR", d)
    return d
