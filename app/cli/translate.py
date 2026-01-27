"""
translate subcommand for managing i18n translation workflow.

Headless version of the Translation Manager GUI. Runs the full pipeline
(extract → translate → validate → compile) or individual steps, with
configurable AI translation provider.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Optional

import click

from app.core.translation_utils import (
    get_translation_languages,
    run_lrelease,
    run_lupdate,
    translate_language_batch,
    validate_translation,
)
from app.models.translation import (
    TranslationConfig,
    set_translation_config,
)
from app.services.translation_service import (
    TranslationService,
    create_translation_service,
)


def _log(msg: str, quiet: bool) -> None:
    if not quiet:
        click.echo(msg, err=True)


def _log_green(msg: str, quiet: bool) -> None:
    if not quiet:
        click.secho(msg, fg="green", err=True)


def _log_red(msg: str, quiet: bool) -> None:
    click.secho(msg, fg="red", err=True)


def _resolve_languages(lang: Optional[str], quiet: bool) -> list[str]:
    if lang and lang != "all":
        return [lang]
    languages = get_translation_languages()
    if not languages:
        _log_red("No languages found.", quiet)
    return languages


# Shared click options for translate commands
_translate_options = [
    click.option(
        "--lang",
        default=None,
        help="Language code (e.g. de_DE). Omit or 'all' for all languages.",
    ),
    click.option(
        "--provider",
        type=click.Choice(["google", "deepl", "openai"]),
        default="google",
        show_default=True,
        help="Translation provider.",
    ),
    click.option("--api-key", default=None, help="API key for deepl/openai."),
    click.option(
        "--model",
        default="gpt-3.5-turbo",
        show_default=True,
        help="Model name (openai only).",
    ),
    click.option(
        "--concurrency",
        default=5,
        show_default=True,
        type=click.IntRange(1, 20),
        help="Max concurrent translation requests.",
    ),
    click.option("--no-cache", is_flag=True, help="Disable translation cache."),
    click.option("--quiet", is_flag=True, help="Suppress progress output."),
]


def _add_translate_options(func: Any) -> Any:
    for opt in reversed(_translate_options):
        func = opt(func)
    return func


def _setup_translate(
    provider: str,
    api_key: Optional[str],
    concurrency: int,
    no_cache: bool,
    lang: Optional[str],
    quiet: bool,
) -> tuple[list[str], dict[str, str]]:
    """Common setup for translate commands. Returns (languages, service_kwargs)."""
    if provider != "google" and not api_key:
        _log_red(f"Error: --api-key is required for provider '{provider}'.", quiet)
        sys.exit(1)

    set_translation_config(
        TranslationConfig(max_concurrent_requests=concurrency, use_cache=not no_cache)
    )

    languages = _resolve_languages(lang, quiet)
    if not languages:
        sys.exit(1)

    service_kwargs: dict[str, str] = {}
    if provider != "google" and api_key:
        service_kwargs["api_key"] = api_key
    if provider == "openai":
        service_kwargs["model"] = "gpt-3.5-turbo"

    return languages, service_kwargs


# ---------------------------------------------------------------------------
# Main command group
# ---------------------------------------------------------------------------


@click.group("translate")
def translate_group() -> None:
    """Manage RimDex translations (extract, translate, validate, compile)."""


# ---------------------------------------------------------------------------
# extract (lupdate)
# ---------------------------------------------------------------------------


@translate_group.command("extract")
@click.option(
    "--lang",
    default=None,
    help="Language code (e.g. de_DE). Omit or 'all' for all languages.",
)
@click.option("--quiet", is_flag=True, help="Suppress progress output.")
def extract_cmd(lang: Optional[str], quiet: bool) -> None:
    """Extract translatable strings from source via pyside6-lupdate."""
    target = lang if lang and lang != "all" else None
    label = target or "all"
    _log(f"Running lupdate for {label}…", quiet)
    ok = run_lupdate(target)
    if ok:
        _log_green("lupdate: success", quiet)
    else:
        _log_red("lupdate: failed", quiet)
        sys.exit(1)


# ---------------------------------------------------------------------------
# translate
# ---------------------------------------------------------------------------


@translate_group.command("translate")
@_add_translate_options
def translate_cmd(
    lang: Optional[str],
    provider: str,
    api_key: Optional[str],
    model: str,
    concurrency: int,
    no_cache: bool,
    quiet: bool,
) -> None:
    """Translate unfinished entries via AI provider."""
    languages, service_kwargs = _setup_translate(
        provider, api_key, concurrency, no_cache, lang, quiet
    )

    try:
        service = create_translation_service(provider, **service_kwargs)
    except (ImportError, ValueError) as e:
        _log_red(f"Error: {e}", quiet)
        sys.exit(1)

    total_translated = 0
    total_failed = 0

    for lang_code in languages:
        _log(f"Starting {lang_code}…", quiet)
        translated, failed = asyncio.run(_translate_language(lang_code, service, quiet))
        total_translated += translated
        total_failed += failed

    _log(f"All done — translated: {total_translated}, failed: {total_failed}", quiet)
    if total_failed > 0:
        sys.exit(1)


async def _translate_language(
    lang_code: str,
    service: TranslationService,
    quiet: bool,
) -> tuple[int, int]:
    """Translate all unfinished entries for one language. Returns (translated, failed)."""
    translated, failed = await translate_language_batch(
        lang_code,
        service,
        on_progress=lambda msg: _log(msg, quiet),
        on_item_done=lambda _i, src, tr: _log(f"  {src}  →  {tr}", quiet),
        on_error=lambda msg: _log_red(msg, quiet),
    )
    return translated, failed


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@translate_group.command("validate")
@click.option(
    "--lang",
    default=None,
    help="Language code (e.g. de_DE). Omit or 'all' for all languages.",
)
@click.option("--quiet", is_flag=True, help="Suppress progress output.")
def validate_cmd(lang: Optional[str], quiet: bool) -> None:
    """Validate translation files (check placeholders, HTML tags, language attrs)."""
    _log("Validating…", quiet)
    issues, fixed = validate_translation(lang)

    if issues:
        _log(f"Issues found: {len(issues)}", quiet)
        for issue in issues:
            _log(f"  • {issue}", quiet)
    else:
        _log_green("Validation passed.", quiet)

    if fixed > 0:
        _log(f"Auto-fixed {fixed} issue(s).", quiet)

    if issues and not fixed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# compile (lrelease)
# ---------------------------------------------------------------------------


@translate_group.command("compile")
@click.option(
    "--lang",
    default=None,
    help="Language code (e.g. de_DE). Omit or 'all' for all languages.",
)
@click.option("--quiet", is_flag=True, help="Suppress progress output.")
def compile_cmd(lang: Optional[str], quiet: bool) -> None:
    """Compile .ts files to .qm via pyside6-lrelease."""
    target = lang if lang and lang != "all" else None
    label = target or "all"
    _log(f"Compiling {label}…", quiet)
    ok = run_lrelease(target)
    if ok:
        _log_green("lrelease: success", quiet)
    else:
        _log_red("lrelease: failed", quiet)
        sys.exit(1)


# ---------------------------------------------------------------------------
# run-all (full pipeline)
# ---------------------------------------------------------------------------


@translate_group.command("run-all")
@_add_translate_options
def run_all_cmd(
    lang: Optional[str],
    provider: str,
    api_key: Optional[str],
    model: str,
    concurrency: int,
    no_cache: bool,
    quiet: bool,
) -> None:
    """Run full pipeline: extract → translate → validate → compile."""
    languages, service_kwargs = _setup_translate(
        provider, api_key, concurrency, no_cache, lang, quiet
    )

    steps = ["extract", "translate", "validate", "compile"]
    _log(f"▶ Running all steps for {len(languages)} language(s)…", quiet)

    for step in steps:
        _log(f"—— Step: {step} ——", quiet)

        if step == "extract":
            target = lang if lang and lang != "all" else None
            ok = run_lupdate(target)
            _log(
                f"lupdate: {'success' if ok else 'failed'}",
                quiet,
            )
            if not ok:
                _log_red("Pipeline stopped: lupdate failed.", quiet)
                sys.exit(1)

        elif step == "translate":
            try:
                service = create_translation_service(provider, **service_kwargs)
            except (ImportError, ValueError) as e:
                _log_red(f"Error: {e}", quiet)
                sys.exit(1)

            total_t = 0
            total_f = 0
            for lang_code in languages:
                _log(f"Starting {lang_code}…", quiet)
                t, f = asyncio.run(_translate_language(lang_code, service, quiet))
                total_t += t
                total_f += f
            _log(
                f"All done — translated: {total_t}, failed: {total_f}",
                quiet,
            )

        elif step == "validate":
            all_issues: list[str] = []
            all_fixed = 0
            for lang_code in languages:
                issues, fixed = validate_translation(lang_code)
                all_issues.extend(issues)
                all_fixed += fixed
            if all_issues:
                _log(f"validate: {len(all_issues)} issue(s)", quiet)
                for issue in all_issues:
                    _log(f"  • {issue}", quiet)
            else:
                _log_green("validate: passed", quiet)
            if all_fixed > 0:
                _log(
                    f"validate: auto-fixed {all_fixed} issue(s)",
                    quiet,
                )

        elif step == "compile":
            for lang_code in languages:
                ok = run_lrelease(lang_code)
                _log(
                    f"lrelease ({lang_code}): {'success' if ok else 'failed'}",
                    quiet,
                )

    _log_green("✓ All steps completed.", quiet)
