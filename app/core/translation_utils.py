"""TS file parsing, validation, and lupdate/lrelease subprocess wrappers.

Leaf utility layer — depends only on ``app.models.translation`` for paths,
constants, and config.  All functions are blocking (no Qt) and safe to call
from ``QThread`` workers.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import lxml.etree as ET
from loguru import logger

from app.models.translation import (
    HTML_TAG_RE,
    LOCALES_DIR,
    PLACEHOLDER_RE,
)

# ---------------------------------------------------------------------------
# TS file I/O
# ---------------------------------------------------------------------------


def save_ts_file(tree: Any, file_path: Path) -> None:
    """Write an lxml ElementTree to a .ts file, preserving the DOCTYPE.

    Uses ``tempfile.mkstemp`` + ``os.replace`` for atomic writes — avoids the
    Windows ``[Errno 22]`` that occurs when lxml holds a memory-mapped handle
    to the source file.
    """
    xml_bytes = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
    content = xml_bytes.decode("utf-8")
    if "<!DOCTYPE TS>" not in content:
        lines = content.splitlines()
        lines.insert(1, "<!DOCTYPE TS>")
        content = "\n".join(lines)

    dirpath = str(file_path.parent) or "."
    fd, tmp_path = tempfile.mkstemp(suffix=".ts", dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
            tmp_f.write(content)
            tmp_f.flush()
            os.fsync(fd)
        os.replace(tmp_path, file_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_translation_languages() -> List[str]:
    """Return sorted language codes from .ts files, excluding ``en_US``."""
    return sorted(f.stem for f in LOCALES_DIR.glob("*.ts") if f.stem != "en_US")


# ---------------------------------------------------------------------------
# Unfinished-translation detection
# ---------------------------------------------------------------------------


@dataclass
class UnfinishedItem:
    context: str
    source: str
    element: Any


def find_unfinished_translations(tree: Any) -> List[UnfinishedItem]:
    """Find all unfinished or empty translation entries in a .ts tree."""
    unfinished: list[UnfinishedItem] = []
    root = tree.getroot()
    if root is None:
        return []

    for context in root.findall("context"):
        context_name = context.findtext("name") or "Unknown"
        for msg in context.findall("message"):
            src_elem = msg.find("source")
            tr_elem = msg.find("translation")
            if src_elem is None or tr_elem is None:
                continue

            src_text = (src_elem.text or "").strip()
            tr_type = (tr_elem.get("type") or "").strip()
            is_plural = msg.get("numerus") == "yes"

            if is_plural:
                numerus_forms = tr_elem.findall("numerusform")
                all_empty = all(not (nf.text or "").strip() for nf in numerus_forms)
                if tr_type == "unfinished" or all_empty:
                    unfinished.append(
                        UnfinishedItem(
                            context=context_name, source=src_text, element=tr_elem
                        )
                    )
            else:
                tr_text = (tr_elem.text or "").strip()
                if tr_type == "unfinished" or not tr_text:
                    unfinished.append(
                        UnfinishedItem(
                            context=context_name, source=src_text, element=tr_elem
                        )
                    )
    return unfinished


def should_skip_translation(text: str) -> bool:
    """Return True for trivial strings that need no translation."""
    if not text.strip():
        return True
    if len(text.strip()) <= 1:
        return True
    if text.isdigit():
        return True
    if re.match(r"^[^\w\s]+$", text):
        return True
    return False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_translation(language: Optional[str] = None) -> tuple[List[str], int]:
    """Validate and repair a .ts file.  Returns ``(issues, fixed_count)``.

    Checks for: missing ``language`` attribute, placeholder mismatches,
    and HTML-tag mismatches.  Auto-fixes where possible and saves the file.
    """
    languages = [language] if language else get_translation_languages()
    all_issues: List[str] = []
    total_fixed = 0

    for lang in languages:
        ts_file = LOCALES_DIR / f"{lang}.ts"
        if not ts_file.exists():
            all_issues.append(f"File not found: {ts_file}")
            continue

        try:
            tree = ET.parse(str(ts_file))
            root = tree.getroot()
            issues: List[str] = []
            made_changes = False

            if root.tag != "TS":
                issues.append("Root element should be 'TS'")

            if not root.get("language"):
                root.set("language", lang)
                made_changes = True
                total_fixed += 1

            for context in root.findall("context"):
                for message in context.findall("message"):
                    source = message.find("source")
                    translation = message.find("translation")
                    if source is None or translation is None:
                        continue

                    source_text = source.text or ""
                    is_plural = message.get("numerus") == "yes"
                    targets = (
                        translation.findall("numerusform")
                        if is_plural
                        else [translation]
                    )

                    for target in targets:
                        trans_text = target.text or ""

                        # Placeholder mismatches
                        src_ph = set(PLACEHOLDER_RE.findall(source_text))
                        tr_ph = set(PLACEHOLDER_RE.findall(trans_text))
                        if src_ph != tr_ph and trans_text:
                            issues.append(f"Placeholder mismatch: {source_text[:40]}")
                            made_changes = True
                            total_fixed += 1
                            for ph in tr_ph - src_ph:
                                trans_text = trans_text.replace(ph, "")
                            for ph in src_ph - tr_ph:
                                trans_text += f" {ph}"
                            target.text = trans_text.strip()

                        # HTML tag mismatches
                        src_tags = Counter(HTML_TAG_RE.findall(source_text))
                        tr_tags = Counter(HTML_TAG_RE.findall(trans_text))
                        if src_tags != tr_tags and trans_text:
                            issues.append(f"HTML tag mismatch: {source_text[:40]}")
                            made_changes = True
                            total_fixed += 1
                            for tag, count in (tr_tags - src_tags).items():
                                trans_text = trans_text.replace(tag, "", count)
                            for tag, count in (src_tags - tr_tags).items():
                                trans_text += f" {tag}" * count
                            target.text = trans_text.strip()

            if made_changes:
                save_ts_file(tree, ts_file)

            all_issues.extend(issues)
        except Exception as e:
            all_issues.append(f"Error validating {lang}: {e}")

    return all_issues, total_fixed


# ---------------------------------------------------------------------------
# subprocess wrappers
# ---------------------------------------------------------------------------


def run_lupdate(language: Optional[str] = None) -> bool:
    """Run ``pyside6-lupdate`` to sync .ts files with source strings."""
    try:
        cmd = ["pyside6-lupdate"]
        py_files = list(Path("app").rglob("*.py"))
        if not py_files:
            logger.warning("No Python source files found under app/")
            return False

        cmd.extend(str(f) for f in py_files)

        if language:
            ts_file = LOCALES_DIR / f"{language}.ts"
            cmd.extend(["-ts", str(ts_file), "-no-obsolete", "-locations", "none"])
        else:
            ts_files = list(LOCALES_DIR.glob("*.ts"))
            if not ts_files:
                logger.warning("No .ts files found in locales/")
                return False
            cmd.extend(
                [
                    "-ts",
                    *[str(f) for f in ts_files],
                    "-no-obsolete",
                    "-locations",
                    "none",
                ]
            )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("lupdate succeeded for %s", language or "all")
            return True
        logger.error("lupdate failed: %s", result.stderr)
        return False
    except FileNotFoundError:
        logger.error("pyside6-lupdate not found")
        return False
    except Exception as e:
        logger.error("lupdate error: %s", e)
        return False


def run_lrelease(language: Optional[str] = None) -> bool:
    """Run ``pyside6-lrelease`` to compile .ts → .qm."""
    try:
        if not LOCALES_DIR.exists():
            logger.error("Locales directory not found")
            return False

        if language:
            ts_file = LOCALES_DIR / f"{language}.ts"
            if not ts_file.exists():
                logger.error("Translation file not found: %s", ts_file)
                return False
            result = subprocess.run(
                ["pyside6-lrelease", str(ts_file)], capture_output=True, text=True
            )
            return result.returncode == 0

        ts_files = list(LOCALES_DIR.glob("*.ts"))
        success = 0
        for ts_file in ts_files:
            result = subprocess.run(
                ["pyside6-lrelease", str(ts_file)], capture_output=True, text=True
            )
            if result.returncode == 0:
                success += 1
        logger.info("lrelease compiled %d/%d files", success, len(ts_files))
        return success > 0
    except FileNotFoundError:
        logger.error("pyside6-lrelease not found")
        return False
    except Exception as e:
        logger.error("lrelease error: %s", e)
        return False
