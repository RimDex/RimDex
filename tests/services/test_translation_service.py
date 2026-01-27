"""Unit tests for the in-app translation service layer (``app.services.translation_service``)."""

from __future__ import annotations

import pytest

from app.models.translation import (
    RetryConfig,
    TranslationConfig,
    set_translation_config,
)
from app.services.translation_service import (
    DeepLService,
    TranslationService,
    create_translation_service,
)

# ---------------------------------------------------------------------------
# _get_service_code (pure mapping)
# ---------------------------------------------------------------------------


def test_get_service_code_known() -> None:
    assert TranslationService._get_service_code("zh_CN", "google") == "zh-cn"
    assert TranslationService._get_service_code("zh_CN", "deepl") == "ZH"
    assert TranslationService._get_service_code("de_DE", "google") == "de"


def test_get_service_code_fallback() -> None:
    # Unknown service name falls back to the language code itself
    assert TranslationService._get_service_code("de_DE", "unknown_svc") == "de_DE"
    # Unknown language falls back to a derived code (lower + dash)
    assert TranslationService._get_service_code("xx_XX", "google") == "xx-xx"


# ---------------------------------------------------------------------------
# create_translation_service factory
# ---------------------------------------------------------------------------


def test_create_unknown_service_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported service"):
        create_translation_service("bogus")


def test_create_deepl_requires_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        create_translation_service("deepl")


def test_create_deepl_with_key() -> None:
    svc = create_translation_service("deepl", api_key="key123")
    assert isinstance(svc, DeepLService)
    assert svc.api_key == "key123"


# ---------------------------------------------------------------------------
# Base TranslationService: cache + retry logic (no external network)
# ---------------------------------------------------------------------------


class FakeService(TranslationService):
    _service_name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def _call_api(self, text: str, target: str, source: str) -> str:
        self.calls.append((text, target, source))
        return text.upper()


@pytest.mark.asyncio
async def test_base_translate_returns_translation() -> None:
    svc = FakeService()
    result = await svc.translate("hello", "de_DE", "en_US")
    assert result == "HELLO"
    # target/source resolved via _get_service_code for an unknown service name
    assert svc.calls == [("hello", "de_DE", "en_US")]


@pytest.mark.asyncio
async def test_base_translate_uses_cache() -> None:
    set_translation_config(TranslationConfig(use_cache=True))
    svc = FakeService()
    r1 = await svc.translate("hello", "de_DE", "en_US")
    r2 = await svc.translate("hello", "de_DE", "en_US")
    # First call hits the API; the cached second call short-circuits to None
    # (the base translate() returns None on a cache hit — see _resolve_langs).
    assert r1 == "HELLO"
    assert r2 is None
    assert len(svc.calls) == 1


class FlakyService(TranslationService):
    _service_name = "fake"

    def __init__(self) -> None:
        self.attempts = 0

    async def _call_api(self, text: str, target: str, source: str) -> str:
        self.attempts += 1
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_base_translate_retries_then_gives_up() -> None:
    cfg = TranslationConfig(
        retry_config=RetryConfig(max_retries=2, initial_delay=0.0, max_delay=0.0),
        use_cache=False,
    )
    set_translation_config(cfg)
    svc = FlakyService()
    result = await svc.translate("x", "de_DE", "en_US")
    assert result is None
    assert svc.attempts == 2  # tried twice, then gave up
