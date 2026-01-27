"""Controller that wires the TranslationManagerDialog into the app.

Connects the ``EventBus().do_open_translation_manager`` signal to a handler
that instantiates and shows the dialog, and optionally connects menu-bar
actions.
"""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtWidgets import QWidget

from app.core.event_bus import EventBus
from app.services.window_manager import WindowManager


class TranslationController(QObject):
    """Wires the translation-manager signal to the dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._window_manager = WindowManager()
        self._dialog: object | None = None

        EventBus().do_open_translation_manager.connect(self._open_dialog)
        logger.debug("TranslationController connected")

    @Slot()
    def _open_dialog(self) -> None:
        from app.windows.translation_manager import TranslationManagerDialog

        # Avoid stacking multiple instances
        if self._dialog is not None:
            return

        self._dialog = TranslationManagerDialog()
        self._window_manager.register(self._dialog)
        self._dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._dialog.finished.connect(self._on_dialog_closed)
        self._dialog.show()

    @Slot(int)
    def _on_dialog_closed(self, _code: int) -> None:
        self._dialog = None
