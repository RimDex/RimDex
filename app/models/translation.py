"""Translation configuration, cache, and language map.

Pure data layer — no Qt imports, no side-effectful I/O beyond the cache file.
Mirrors the configuration and cache system from the standalone
``translation_helper.py`` so the in-app UI and the CLI tool share the same
persistent cache and language mappings.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOCALES_DIR = Path("locales")
PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")
HTML_TAG_RE = re.compile(r"<[^>]+>")

# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RetryConfig:
    """Retry mechanism settings with exponential backoff."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

    def get_delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


@dataclass
class TimeoutConfig:
    """Per-service request timeouts in seconds."""

    default_timeout: float = 10.0
    deepl_timeout: float = 10.0
    openai_timeout: float = 10.0
    google_timeout: float = 10.0


@dataclass
class TranslationConfig:
    """Global translation configuration."""

    retry_config: RetryConfig = field(default_factory=RetryConfig)
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)
    max_concurrent_requests: int = 5
    use_cache: bool = True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> TranslationConfig:
        retry = RetryConfig(**config_dict.get("retry_config", {}))
        timeout = TimeoutConfig(**config_dict.get("timeout_config", {}))
        return cls(
            retry_config=retry,
            timeout_config=timeout,
            max_concurrent_requests=config_dict.get("max_concurrent_requests", 5),
            use_cache=config_dict.get("use_cache", True),
        )


# ---------------------------------------------------------------------------
# Language map
# ---------------------------------------------------------------------------


class LangMapEntry(TypedDict, total=False):
    google: Optional[str]
    deepl: Optional[str]
    openai: Optional[str]


LANG_MAP: Dict[str, LangMapEntry] = {
    "zh_CN": {"google": "zh-cn", "deepl": "ZH", "openai": "Simplified Chinese"},
    "zh_TW": {"google": "zh-tw", "deepl": "ZH", "openai": "Traditional Chinese"},
    "en_US": {"google": "en", "deepl": "EN", "openai": "English"},
    "ja_JP": {"google": "ja", "deepl": "JA", "openai": "Japanese"},
    "ko_KR": {"google": "ko", "deepl": "KO", "openai": "Korean"},
    "fr_FR": {"google": "fr", "deepl": "FR", "openai": "French"},
    "de_DE": {"google": "de", "deepl": "DE", "openai": "German"},
    "es_ES": {"google": "es", "deepl": "ES", "openai": "Spanish"},
    "ru_RU": {"google": "ru", "deepl": None, "openai": None},
    "tr_TR": {"google": "tr", "deepl": None, "openai": None},
    "pt_BR": {"google": "pt", "deepl": None, "openai": None},
}

# ---------------------------------------------------------------------------
# Translation cache
# ---------------------------------------------------------------------------

_CACHE_FILE = LOCALES_DIR / ".translation_cache.json"


@dataclass
class TranslationCache:
    """Hash-based translation cache persisted to a JSON file.

    Shared between the CLI tool and the in-app UI so results are reused.
    """

    _cache: Dict[str, str] = field(default_factory=dict)
    _cache_file: Path = field(default_factory=lambda: _CACHE_FILE)
    _loaded: bool = field(init=False, default=False)

    def _load_if_needed(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (IOError, json.JSONDecodeError):
                self._cache = {}

    def save(self) -> None:
        if not self._cache:
            return
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2)

    def _key(self, text: str, target_lang: str, source_lang: str, service: str) -> str:
        return hashlib.sha256(
            f"{text}:{target_lang}:{source_lang}:{service}".encode()
        ).hexdigest()

    def get(
        self, text: str, target_lang: str, source_lang: str, service: str
    ) -> Optional[str]:
        self._load_if_needed()
        return self._cache.get(self._key(text, target_lang, source_lang, service))

    def set(
        self,
        text: str,
        target_lang: str,
        source_lang: str,
        service: str,
        translation: str,
    ) -> None:
        self._load_if_needed()
        self._cache[self._key(text, target_lang, source_lang, service)] = translation

    def clear(self) -> None:
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()

    @property
    def size(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_translation_config = TranslationConfig()
_translation_cache = TranslationCache()


def get_translation_config() -> TranslationConfig:
    return _translation_config


def set_translation_config(config: TranslationConfig) -> None:
    global _translation_config
    _translation_config = config


def get_translation_cache() -> TranslationCache:
    return _translation_cache
