"""Unit tests for the in-app translation CLI (``app.cli.translate``).

The CLI commands shell out to lupdate/lrelease and call the async batch
translator; those side-effecting pieces are mocked so only the CLI wiring
(argument resolution, config setup, pipeline orchestration) is exercised.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from click.testing import CliRunner

from app.cli import translate as cli_translate
from app.models.translation import (
    TranslationConfig,
    get_translation_config,
    set_translation_config,
)

# ---------------------------------------------------------------------------
# _resolve_languages
# ---------------------------------------------------------------------------


def test_resolve_languages_specific(locales_tmp: Path) -> None:
    assert cli_translate._resolve_languages("de_DE", False) == ["de_DE"]


def test_resolve_languages_all_excludes_source(locales_tmp: Path) -> None:
    (locales_tmp / "en_US.ts").write_text("<TS></TS>")
    (locales_tmp / "de_DE.ts").write_text("<TS></TS>")
    (locales_tmp / "fr_FR.ts").write_text("<TS></TS>")
    assert cli_translate._resolve_languages("all", False) == ["de_DE", "fr_FR"]


# ---------------------------------------------------------------------------
# _setup_translate
# ---------------------------------------------------------------------------


def test_setup_translate_requires_key_for_deepl(locales_tmp: Path) -> None:
    with pytest.raises(SystemExit):
        cli_translate._setup_translate("deepl", None, 5, False, None, False)


def test_setup_translate_google_ok(locales_tmp: Path) -> None:
    set_translation_config(TranslationConfig())
    langs, kwargs = cli_translate._setup_translate(
        "google", None, 7, False, "de_DE", False
    )
    assert langs == ["de_DE"]
    assert kwargs == {}
    assert get_translation_config().max_concurrent_requests == 7


# ---------------------------------------------------------------------------
# Command invocations (CliRunner)
# ---------------------------------------------------------------------------


def test_extract_cmd_success(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_translate, "run_lupdate", lambda lang: True)
    result = CliRunner().invoke(
        cli_translate.translate_group, ["extract", "--lang", "de_DE"]
    )
    assert result.exit_code == 0


def test_extract_cmd_failure(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_translate, "run_lupdate", lambda lang: False)
    result = CliRunner().invoke(
        cli_translate.translate_group, ["extract", "--lang", "de_DE"]
    )
    assert result.exit_code == 1


def test_compile_cmd_success(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_translate, "run_lrelease", lambda lang: True)
    result = CliRunner().invoke(cli_translate.translate_group, ["compile"])
    assert result.exit_code == 0


def test_validate_cmd_success(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_translate, "validate_translation", lambda lang: ([], 0))
    result = CliRunner().invoke(cli_translate.translate_group, ["validate"])
    assert result.exit_code == 0


def test_translate_cmd_success(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc = MagicMock()
    monkeypatch.setattr(cli_translate, "create_translation_service", lambda p, **k: svc)
    monkeypatch.setattr(
        cli_translate, "translate_language_batch", AsyncMock(return_value=(2, 0))
    )
    result = CliRunner().invoke(
        cli_translate.translate_group,
        ["translate", "--lang", "de_DE", "--provider", "google"],
    )
    assert result.exit_code == 0


def test_run_all_cmd_success(
    locales_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (locales_tmp / "de_DE.ts").write_text("<TS></TS>")
    monkeypatch.setattr(cli_translate, "run_lupdate", lambda lang: True)
    svc = MagicMock()
    monkeypatch.setattr(cli_translate, "create_translation_service", lambda p, **k: svc)
    monkeypatch.setattr(
        cli_translate, "translate_language_batch", AsyncMock(return_value=(1, 0))
    )
    monkeypatch.setattr(cli_translate, "run_lrelease", lambda lang: True)
    result = CliRunner().invoke(
        cli_translate.translate_group,
        ["run-all", "--lang", "de_DE", "--provider", "google", "--quiet"],
    )
    assert result.exit_code == 0
