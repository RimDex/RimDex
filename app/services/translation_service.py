"""Translation service abstraction and implementations.

Leaf service layer — depends only on ``app.models.translation`` for config,
cache, and language map.  Provides :class:`GoogleTranslateService`,
:class:`DeepLService`, and :class:`OpenAIService` behind a common
:class:`TranslationService` interface.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
from typing import Any, Optional

import aiohttp

from app.models.translation import (
    LANG_MAP,
    TranslationConfig,
    get_translation_cache,
    get_translation_config,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency probes
# ---------------------------------------------------------------------------

try:
    from googletrans import Translator as GoogleTranslator
except ImportError:
    GoogleTranslator = None

openai_module: Any = None
try:
    openai_module = importlib.import_module("openai")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class TranslationService:
    """Abstract base for translation service implementations."""

    _service_name: str = ""

    async def translate(
        self, text: str, target_lang: str, source_lang: str = "en_US"
    ) -> Optional[str]:
        resolved = self._resolve_langs(text, target_lang, source_lang)
        if resolved is None:
            return None
        config, target, source = resolved
        return await self._translate_with_retry(text, target, source, config)

    async def _translate_with_retry(
        self, text: str, target: str, source: str, config: TranslationConfig
    ) -> Optional[str]:
        for attempt in range(config.retry_config.max_retries):
            try:
                translation = await self._call_api(text, target, source)
                if translation is not None:
                    self._store_cache(text, target, source, translation)
                return translation
            except Exception as e:
                if attempt < config.retry_config.max_retries - 1:
                    delay = config.retry_config.get_delay(attempt)
                    logger.warning(
                        "%s attempt %d failed, retrying in %.1fs: %s",
                        self._service_name,
                        attempt + 1,
                        delay,
                        e,
                    )
                    await asyncio.sleep(delay)
                    await self._on_retry_error(e)
                else:
                    logger.error(
                        "%s failed after %d attempts: %s",
                        self._service_name,
                        config.retry_config.max_retries,
                        e,
                    )
                    return None
        return None

    async def _call_api(self, text: str, target: str, source: str) -> Optional[str]:
        raise NotImplementedError

    async def _on_retry_error(self, exc: Exception) -> None:
        """Hook for subclass-specific error recovery (e.g. re-create transport)."""

    @staticmethod
    def _get_service_code(lang_code: str, service: str) -> str:
        entry = LANG_MAP.get(lang_code)
        if entry:
            code = entry.get(service)
            if isinstance(code, str) and code:
                return code
        if service == "google":
            return lang_code.lower().replace("_", "-")
        elif service == "deepl":
            return lang_code.upper()
        return lang_code

    def _check_cache(
        self, text: str, target_lang: str, source_lang: str
    ) -> Optional[str]:
        config = get_translation_config()
        if config.use_cache:
            cached = get_translation_cache().get(
                text, target_lang, source_lang, self._service_name
            )
            if cached is not None:
                return cached
        return None

    def _store_cache(
        self, text: str, target_lang: str, source_lang: str, translation: str
    ) -> None:
        config = get_translation_config()
        if config.use_cache:
            get_translation_cache().set(
                text, target_lang, source_lang, self._service_name, translation
            )

    def _resolve_langs(
        self, text: str, target_lang: str, source_lang: str
    ) -> Optional[tuple[TranslationConfig, str, str]]:
        """Check cache; return ``(config, target, source)`` on miss, or ``None`` on cache hit."""
        cached = self._check_cache(text, target_lang, source_lang)
        if cached is not None:
            return None
        config = get_translation_config()
        return (
            config,
            self._get_service_code(target_lang, self._service_name),
            self._get_service_code(source_lang, self._service_name),
        )


# ---------------------------------------------------------------------------
# Google Translate
# ---------------------------------------------------------------------------


class GoogleTranslateService(TranslationService):
    """Google Translate via the free ``googletrans`` library."""

    _service_name = "google"

    def __init__(self) -> None:
        if GoogleTranslator is None:
            raise ImportError(
                "googletrans not available. Install with: pip install googletrans==4.0.0rc1"
            )
        self.translator = GoogleTranslator()
        self.config = get_translation_config()
        self._setup_translator()

    def _setup_translator(self) -> None:
        try:
            session = getattr(self.translator, "_session", None)
            if session:
                session.verify = False
        except AttributeError:
            pass

    async def _call_api(self, text: str, target: str, source: str) -> Optional[str]:
        result = self.translator.translate(text, dest=target, src=source)
        if inspect.iscoroutine(result):
            result = await result
        return result.text

    async def _on_retry_error(self, exc: Exception) -> None:
        if "ssl" in str(exc).lower() and GoogleTranslator is not None:
            self.translator = GoogleTranslator()
            self._setup_translator()


# ---------------------------------------------------------------------------
# DeepL
# ---------------------------------------------------------------------------


class DeepLService(TranslationService):
    """DeepL API translation service."""

    _service_name = "deepl"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2/translate"
        self.config = get_translation_config()

    async def _call_api(self, text: str, target: str, source: str) -> Optional[str]:
        config = get_translation_config()
        timeout = aiohttp.ClientTimeout(total=config.timeout_config.deepl_timeout)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                data={
                    "auth_key": self.api_key,
                    "text": text,
                    "target_lang": target,
                    "source_lang": source,
                },
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["translations"][0]["text"]


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------


class OpenAIService(TranslationService):
    """OpenAI GPT translation service."""

    _service_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo") -> None:
        if openai_module is None:
            raise ImportError("openai library not available")
        self.config = get_translation_config()
        self.client = openai_module.OpenAI(
            api_key=api_key,
            timeout=self.config.timeout_config.openai_timeout,
        )
        self.model = model

    async def _call_api(self, text: str, target: str, source: str) -> Optional[str]:
        if openai_module is None:
            raise ImportError("openai library not available")
        prompt = (
            f"Translate the following {source} text to {target}.\n"
            "This is UI text from a software application. Keep it concise and user-friendly.\n"
            f"Only return the translation, no explanation:\n\n{text}"
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_translation_service(service_name: str, **kwargs: Any) -> TranslationService:
    """Create a translation service by name.

    Args:
        service_name: ``"google"``, ``"deepl"``, or ``"openai"``.
        **kwargs: ``api_key`` for deepl/openai; ``model`` for openai.

    Raises:
        ImportError: Required library not installed.
        ValueError: Missing credentials or unknown service.
    """
    if service_name == "google":
        return GoogleTranslateService()
    elif service_name == "deepl":
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("DeepL requires api_key")
        return DeepLService(api_key)
    elif service_name == "openai":
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("OpenAI requires api_key")
        model = kwargs.get("model", "gpt-3.5-turbo")
        return OpenAIService(api_key, model)
    else:
        raise ValueError(f"Unsupported service: {service_name}")
