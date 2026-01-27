"""Translation Manager dialog.

Provides a UI for: extracting source strings (``pyside6-lupdate``),
translating unfinished entries via Google/DeepL/OpenAI, validating
translation files, and compiling ``.ts`` → ``.qm`` (``pyside6-lrelease``).
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.translation_utils import (
    get_translation_languages,
    run_lrelease,
    run_lupdate,
)
from app.core.translation_workers import (
    SubprocessWorker,
    TranslateBatchWorker,
    ValidateWorker,
)


class TranslationManagerDialog(QDialog):
    """Modal dialog for managing RimDex translations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("RimDex — Translation Manager"))
        self.setMinimumSize(700, 520)

        self._workers: list[QThread] = []
        self._pending_langs: list[str] = []
        self._translated_total: int = 0
        self._failed_total: int = 0
        self._pipeline_steps: list[str] = []
        self._pipeline_kwargs: dict[str, str] = {}
        self._pipeline_lang: str | None = None

        self._init_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- Language selector ---
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(self.tr("Language:")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem(self.tr("All"))
        self.lang_combo.addItems(get_translation_languages())
        self.lang_combo.setMinimumWidth(120)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        root.addLayout(lang_row)

        # --- Service config ---
        svc_group = QGroupBox(self.tr("Translation Service"))
        svc_lay = QVBoxLayout(svc_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel(self.tr("Provider:")))
        self.service_combo = QComboBox()
        self.service_combo.addItems(["google", "deepl", "openai"])
        self.service_combo.currentTextChanged.connect(self._on_service_changed)
        row1.addWidget(self.service_combo)
        row1.addStretch()
        svc_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(self.tr("API Key:")))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText(self.tr("(not required for Google)"))
        row2.addWidget(self.api_key_edit)
        svc_lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel(self.tr("Model:")))
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-3.5-turbo")
        self.model_edit.setEnabled(False)
        row3.addWidget(self.model_edit)
        row3.addStretch()
        svc_lay.addLayout(row3)

        root.addWidget(svc_group)

        # --- Concurrency / cache ---
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel(self.tr("Concurrency:")))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 20)
        self.concurrency_spin.setValue(5)
        opt_row.addWidget(self.concurrency_spin)

        self.cache_check = QCheckBox(self.tr("Use cache"))
        self.cache_check.setChecked(True)
        opt_row.addWidget(self.cache_check)
        opt_row.addStretch()
        root.addLayout(opt_row)

        # --- Action buttons ---
        btn_row = QHBoxLayout()
        self.btn_run_all = QPushButton(self.tr("Run All"))
        self.btn_lupdate = QPushButton(self.tr("Extract (lupdate)"))
        self.btn_translate = QPushButton(self.tr("Translate"))
        self.btn_validate = QPushButton(self.tr("Validate"))
        self.btn_lrelease = QPushButton(self.tr("Compile (lrelease)"))
        self.btn_close = QPushButton(self.tr("Close"))

        for b in (
            self.btn_run_all,
            self.btn_lupdate,
            self.btn_translate,
            self.btn_validate,
            self.btn_lrelease,
            self.btn_close,
        ):
            btn_row.addWidget(b)

        root.addLayout(btn_row)

        # --- Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel()
        root.addWidget(self.status_label)

        # --- Log pane ---
        self.log_pane = QPlainTextEdit()
        self.log_pane.setReadOnly(True)
        self.log_pane.setMaximumBlockCount(500)
        root.addWidget(self.log_pane, 1)

        # --- Connections ---
        self.btn_run_all.clicked.connect(self._on_run_all)
        self.btn_lupdate.clicked.connect(self._on_lupdate)
        self.btn_translate.clicked.connect(self._on_translate)
        self.btn_validate.clicked.connect(self._on_validate)
        self.btn_lrelease.clicked.connect(self._on_lrelease)
        self.btn_close.clicked.connect(self.close)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _selected_lang(self) -> str | None:
        text = self.lang_combo.currentText()
        return None if text == self.tr("All") else text

    def _append_log(self, text: str) -> None:
        self.log_pane.appendPlainText(text)

    def _set_busy(self, busy: bool) -> None:
        self.progress_bar.setVisible(busy)
        self.progress_bar.setRange(0, 0 if busy else 1)
        for b in (
            self.btn_run_all,
            self.btn_lupdate,
            self.btn_translate,
            self.btn_validate,
            self.btn_lrelease,
        ):
            b.setEnabled(not busy)

    @Slot(str)
    def _on_service_changed(self, name: str) -> None:
        self.model_edit.setEnabled(name == "openai")
        self.api_key_edit.setEnabled(name != "google")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _service_kwargs(self) -> dict[str, str]:
        svc = self.service_combo.currentText()
        kwargs: dict[str, str] = {}
        if svc != "google":
            kwargs["api_key"] = self.api_key_edit.text().strip()
        if svc == "openai":
            kwargs["model"] = self.model_edit.text().strip() or "gpt-3.5-turbo"
        return kwargs

    @Slot()
    def _on_run_all(self) -> None:
        lang = self._selected_lang()
        kwargs = self._service_kwargs()

        self._pipeline_lang = lang
        self._pipeline_kwargs = kwargs
        self._pipeline_steps = ["lupdate", "translate", "validate", "lrelease"]
        self._append_log(self.tr("▶ Running all steps…"))
        self._set_busy(True)
        self._run_next_pipeline_step()

    def _run_next_pipeline_step(self) -> None:
        if not self._pipeline_steps:
            self._set_busy(False)
            self.status_label.setText(self.tr("All steps completed."))
            self._append_log(self.tr("✓ All steps completed."))
            return

        step = self._pipeline_steps.pop(0)
        self._append_log(self.tr("—— Step: {step} ——").format(step=step))

        if step == "lupdate":
            self._run_lupdate_for_pipeline()
        elif step == "translate":
            self._run_translate_for_pipeline()
        elif step == "validate":
            self._run_validate_for_pipeline()
        elif step == "lrelease":
            self._run_lrelease_for_pipeline()

    # -- pipeline step launchers --

    def _run_lupdate_for_pipeline(self) -> None:
        lang = self._pipeline_lang
        w = SubprocessWorker(func=run_lupdate, label="Extracting", language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_pipeline_lupdate_done)
        self._workers.append(w)
        w.start()

    @Slot(bool)
    def _on_pipeline_lupdate_done(self, ok: bool) -> None:
        self._append_log(
            self.tr("lupdate: {result}").format(
                result=self.tr("success") if ok else self.tr("failed")
            )
        )
        self._run_next_pipeline_step()

    def _run_translate_for_pipeline(self) -> None:
        lang = self._pipeline_lang
        svc = self.service_combo.currentText()
        kwargs = self._pipeline_kwargs

        if lang is None:
            self._pipeline_translate_done = False
            self._translated_total = 0
            self._failed_total = 0
            languages = get_translation_languages()
            if not languages:
                self._append_log(self.tr("No languages found."))
                self._run_next_pipeline_step()
                return
            self._pending_langs = list(languages)
            self._start_next_translate(svc, kwargs)
            self._poll_translate_done()
            return

        w = TranslateBatchWorker(language=lang, service_name=svc, service_kwargs=kwargs)
        w.progress.connect(self._append_log)
        w.item_done.connect(self._on_translate_item)
        w.finished.connect(self._on_pipeline_translate_done)
        w.error.connect(lambda e: self._append_log(f"ERROR: {e}"))
        self._workers.append(w)
        w.start()

    @Slot(bool, int, int)
    def _on_pipeline_translate_done(
        self, ok: bool, translated: int, failed: int
    ) -> None:
        self._append_log(
            self.tr("translate: done ({t} translated, {f} failed)").format(
                t=translated, f=failed
            )
        )
        self._run_next_pipeline_step()

    def _poll_translate_done(self) -> None:
        from PySide6.QtCore import QTimer

        if self._pipeline_translate_done:
            self._append_log(
                self.tr("translate: done ({t} translated, {f} failed)").format(
                    t=self._translated_total, f=self._failed_total
                )
            )
            self._run_next_pipeline_step()
            return
        QTimer.singleShot(200, self._poll_translate_done)

    def _run_validate_for_pipeline(self) -> None:
        lang = self._pipeline_lang
        w = ValidateWorker(language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_pipeline_validate_done)
        self._workers.append(w)
        w.start()

    @Slot(list, int)
    def _on_pipeline_validate_done(self, issues: list[str], fixed_count: int) -> None:
        if issues:
            self._append_log(self.tr("validate: {n} issue(s)").format(n=len(issues)))
            for i in issues:
                self._append_log(f"  • {i}")
        else:
            self._append_log(self.tr("validate: passed"))

        if fixed_count > 0:
            self._append_log(
                self.tr(
                    "validate: auto-fixed {n} issue(s), rerunning lupdate → translate → validate…"
                ).format(n=fixed_count)
            )
            self._pipeline_steps = [
                "lupdate",
                "translate",
                "validate",
            ] + self._pipeline_steps

        self._run_next_pipeline_step()

    def _run_lrelease_for_pipeline(self) -> None:
        lang = self._pipeline_lang
        w = SubprocessWorker(func=run_lrelease, label="Compiling", language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_pipeline_lrelease_done)
        self._workers.append(w)
        w.start()

    @Slot(bool)
    def _on_pipeline_lrelease_done(self, ok: bool) -> None:
        self._append_log(
            self.tr("lrelease: {result}").format(
                result=self.tr("success") if ok else self.tr("failed")
            )
        )
        self._run_next_pipeline_step()

    @Slot()
    def _on_lupdate(self) -> None:
        lang = self._selected_lang()
        label = self.tr("all") if lang is None else lang
        self._set_busy(True)
        self._append_log(self.tr("Running lupdate for {lang}…").format(lang=label))
        w = SubprocessWorker(func=run_lupdate, label="Extracting", language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_lupdate_done)
        self._workers.append(w)
        w.start()

    @Slot(bool)
    def _on_lupdate_done(self, ok: bool) -> None:
        self._set_busy(False)
        self.status_label.setText(
            self.tr("lupdate: success") if ok else self.tr("lupdate: failed")
        )
        self._append_log(self.status_label.text())

    @Slot()
    def _on_translate(self) -> None:
        lang = self._selected_lang()
        svc = self.service_combo.currentText()
        kwargs = self._service_kwargs()

        if lang is None:
            self._translate_all(svc, kwargs)
            return

        self._set_busy(True)
        self._append_log(
            self.tr("Translating {lang} via {svc}…").format(lang=lang, svc=svc)
        )
        w = TranslateBatchWorker(language=lang, service_name=svc, service_kwargs=kwargs)
        w.progress.connect(self._append_log)
        w.item_done.connect(self._on_translate_item)
        w.finished.connect(self._on_translate_done)
        w.error.connect(lambda e: self._append_log(f"ERROR: {e}"))
        self._workers.append(w)
        w.start()

    def _translate_all(self, svc: str, kwargs: dict[str, str]) -> None:
        languages = get_translation_languages()
        if not languages:
            self._append_log(self.tr("No languages found."))
            return
        self._set_busy(True)
        self._pending_langs = list(languages)
        self._translated_total = 0
        self._failed_total = 0
        self._append_log(
            self.tr("Translating all {n} languages via {svc}…").format(
                n=len(languages), svc=svc
            )
        )
        self._start_next_translate(svc, kwargs)

    def _start_next_translate(self, svc: str, kwargs: dict[str, str]) -> None:
        if not self._pending_langs:
            self._set_busy(False)
            self.status_label.setText(
                self.tr("All done — translated: {t}, failed: {f}").format(
                    t=self._translated_total, f=self._failed_total
                )
            )
            self._append_log(self.status_label.text())
            return
        lang = self._pending_langs.pop(0)
        self._append_log(self.tr("Starting {lang}…").format(lang=lang))
        w = TranslateBatchWorker(language=lang, service_name=svc, service_kwargs=kwargs)
        w.progress.connect(self._append_log)
        w.item_done.connect(self._on_translate_item)
        w.finished.connect(
            lambda ok, t, f: self._on_translate_batch_done(ok, t, f, svc, kwargs)
        )
        w.error.connect(lambda e: self._append_log(f"ERROR: {e}"))
        self._workers.append(w)
        w.start()

    @Slot(bool, int, int)
    def _on_translate_batch_done(
        self, ok: bool, translated: int, failed: int, svc: str, kwargs: dict[str, str]
    ) -> None:
        self._translated_total += translated
        self._failed_total += failed
        self._start_next_translate(svc, kwargs)

    @Slot(int, str, str)
    def _on_translate_item(self, _idx: int, src: str, tr: str) -> None:
        self._append_log(f"  {src}  →  {tr}")

    @Slot(bool, int, int)
    def _on_translate_done(self, ok: bool, translated: int, failed: int) -> None:
        self._set_busy(False)
        if ok:
            self.status_label.setText(
                self.tr("Translated: {t}, failed: {f}").format(t=translated, f=failed)
            )
        else:
            self.status_label.setText(self.tr("Translation batch failed"))
        self._append_log(self.status_label.text())

    @Slot()
    def _on_validate(self) -> None:
        lang = self._selected_lang()
        self._set_busy(True)
        self._append_log(self.tr("Validating…"))
        w = ValidateWorker(language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_validate_done)
        self._workers.append(w)
        w.start()

    @Slot(list, int)
    def _on_validate_done(self, issues: list[str], fixed_count: int) -> None:
        self._set_busy(False)
        if issues:
            self._append_log(self.tr("Issues found:"))
            for i in issues:
                self._append_log(f"  • {i}")
        else:
            self._append_log(self.tr("Validation passed."))
        if fixed_count > 0:
            self._append_log(self.tr("Auto-fixed {n} issue(s).").format(n=fixed_count))
        self.status_label.setText(
            self.tr("{n} issue(s), {f} fixed").format(n=len(issues), f=fixed_count)
        )

    @Slot()
    def _on_lrelease(self) -> None:
        lang = self._selected_lang()
        label = self.tr("all") if lang is None else lang
        self._set_busy(True)
        self._append_log(self.tr("Compiling {lang}…").format(lang=label))
        w = SubprocessWorker(func=run_lrelease, label="Compiling", language=lang)
        w.progress.connect(self._append_log)
        w.finished.connect(self._on_lrelease_done)
        self._workers.append(w)
        w.start()

    @Slot(bool)
    def _on_lrelease_done(self, ok: bool) -> None:
        self._set_busy(False)
        self.status_label.setText(
            self.tr("lrelease: success") if ok else self.tr("lrelease: failed")
        )
        self._append_log(self.status_label.text())

    def closeEvent(self, event: Any) -> None:
        for w in self._workers:
            if w.isRunning():
                w.wait(3000)
        event.accept()
