"""Unit tests for the in-app translation data layer (``app.models.translation``)."""

from __future__ import annotations

from pathlib import Path

from app.models.translation import (
    LANG_MAP,
    RetryConfig,
    TimeoutConfig,
    TranslationCache,
    TranslationConfig,
)

# ---------------------------------------------------------------------------
# TranslationConfig
# ---------------------------------------------------------------------------


def test_translation_config_defaults() -> None:
    cfg = TranslationConfig()
    assert cfg.max_concurrent_requests == 5
    assert cfg.use_cache is True
    assert isinstance(cfg.retry_config, RetryConfig)
    assert isinstance(cfg.timeout_config, TimeoutConfig)


def test_translation_config_from_dict() -> None:
    cfg = TranslationConfig.from_dict(
        {
            "retry_config": {"max_retries": 7},
            "timeout_config": {"deepl_timeout": 20.0},
            "max_concurrent_requests": 9,
            "use_cache": False,
        }
    )
    assert cfg.max_concurrent_requests == 9
    assert cfg.retry_config.max_retries == 7
    assert cfg.timeout_config.deepl_timeout == 20.0
    assert cfg.use_cache is False


# ---------------------------------------------------------------------------
# RetryConfig / TimeoutConfig
# ---------------------------------------------------------------------------


def test_retry_get_delay_exponential() -> None:
    r = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=10.0)
    assert r.get_delay(0) == 1.0
    assert r.get_delay(1) == 2.0
    assert r.get_delay(3) == 8.0


def test_retry_get_delay_respects_cap() -> None:
    r = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=10.0)
    assert r.get_delay(10) == 10.0


def test_timeout_config_defaults() -> None:
    t = TimeoutConfig()
    assert t.default_timeout == 10.0
    assert t.deepl_timeout == 10.0
    assert t.openai_timeout == 10.0
    assert t.google_timeout == 10.0


# ---------------------------------------------------------------------------
# LANG_MAP
# ---------------------------------------------------------------------------


def test_lang_map_expected_locales() -> None:
    assert set(LANG_MAP) >= {
        "zh_CN",
        "zh_TW",
        "en_US",
        "ja_JP",
        "ko_KR",
        "fr_FR",
        "de_DE",
        "es_ES",
        "ru_RU",
        "tr_TR",
        "pt_BR",
    }


def test_lang_map_google_code() -> None:
    assert LANG_MAP["zh_CN"].get("google") == "zh-cn"
    assert LANG_MAP["en_US"].get("google") == "en"


# ---------------------------------------------------------------------------
# TranslationCache (isolated instances; never touch the real locales cache)
# ---------------------------------------------------------------------------


def test_cache_miss_when_empty(tmp_path: Path) -> None:
    cache = TranslationCache(_cache_file=tmp_path / ".tc.json")
    assert cache.get("Hello", "de_DE", "en_US", "google") is None


def test_cache_set_get(tmp_path: Path) -> None:
    cache = TranslationCache(_cache_file=tmp_path / ".tc.json")
    cache.set("Hello", "de_DE", "en_US", "google", "Hallo")
    assert cache.get("Hello", "de_DE", "en_US", "google") == "Hallo"
    # Different params are distinct keys
    assert cache.get("Hello", "fr_FR", "en_US", "google") is None
    assert cache.get("Hello", "de_DE", "en_US", "deepl") is None


def test_cache_size(tmp_path: Path) -> None:
    cache = TranslationCache(_cache_file=tmp_path / ".tc.json")
    assert cache.size == 0
    cache.set("a", "de_DE", "en_US", "google", "A")
    cache.set("b", "de_DE", "en_US", "google", "B")
    assert cache.size == 2


def test_cache_key_deterministic(tmp_path: Path) -> None:
    cache = TranslationCache(_cache_file=tmp_path / ".tc.json")
    k1 = cache._key("Hello", "de_DE", "en_US", "google")
    k2 = cache._key("Hello", "de_DE", "en_US", "google")
    assert k1 == k2
    assert isinstance(k1, str) and len(k1) == 64


def test_cache_save_reload(tmp_path: Path) -> None:
    f = tmp_path / ".tc.json"
    c1 = TranslationCache(_cache_file=f)
    c1.set("Hello", "de_DE", "en_US", "google", "Hallo")
    c1.save()
    assert f.exists()
    c2 = TranslationCache(_cache_file=f)
    assert c2.get("Hello", "de_DE", "en_US", "google") == "Hallo"


def test_cache_clear_removes_file(tmp_path: Path) -> None:
    f = tmp_path / ".tc.json"
    cache = TranslationCache(_cache_file=f)
    cache.set("Hello", "de_DE", "en_US", "google", "Hallo")
    cache.save()
    cache.clear()
    assert cache.size == 0
    assert not f.exists()
