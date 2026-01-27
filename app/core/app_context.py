"""Application context holding shared runtime references.

Replaces the ad-hoc module-level mutable globals that previously lived in
``utils/globals.py`` (``MAIN_WINDOW`` / ``SETTINGS``). The context is a single
typed object constructed once and populated explicitly during
``AppController`` initialization — references are injected, not read from
loose module-level variables scattered across the codebase.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.settings import Settings
    from app.views.main_window import MainWindow


class AppContext:
    """Holds the long-lived application references.

    ``main_window`` and ``settings`` are set explicitly at startup via
    dependency injection. Reading them before they are populated is a
    programming error and returns ``None``.
    """

    def __init__(self) -> None:
        self.main_window: "MainWindow | None" = None
        self.settings: "Settings | None" = None


# Single process-wide instance, populated at startup via dependency injection
# (see ``AppController``). Keeping one typed holder avoids the previous pattern
# of independent mutable globals.
context = AppContext()
