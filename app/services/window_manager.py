"""Service for tracking and managing MainContent child windows."""

from __future__ import annotations

from typing import Any, Protocol


class _Closeable(Protocol):
    """Anything with a ``close()`` method (real ``QWidget`` or test stubs)."""

    def close(self) -> Any: ...


class WindowManager:
    """Tracks child windows owned by MainContent and provides cleanup.

    Handles both instance-attribute windows (e.g. ``self.rule_editor``)
    and list-tracked windows (created as local variables).
    """

    def __init__(self) -> None:
        self._child_windows: list[_Closeable] = []
        self._tracked_attrs: list[tuple[Any, str]] = []
        self._sub_managers: list[WindowManager] = []

    def register(self, window: _Closeable) -> None:
        """Track a window that was created as a local variable."""
        self._child_windows.append(window)

    def register_attr(self, instance: Any, attr_name: str) -> None:
        """Track an instance attribute that holds a window reference."""
        self._tracked_attrs.append((instance, attr_name))

    def register_manager(self, manager: WindowManager) -> None:
        """Track a child WindowManager so its windows are closed too.

        Controllers (e.g. TranslationController, DatabaseBuilderController)
        own their own dialogs via a separate WindowManager. Registering those
        sub-managers into the MainContent root manager ensures a single
        ``close_all()`` (driven from MainWindow.closeEvent) tears down every
        child window, so background worker threads they own cannot keep the
        application from exiting.
        """
        if manager is not self and manager not in self._sub_managers:
            self._sub_managers.append(manager)

    def close_all(self) -> None:
        """Close all tracked windows and clear tracking lists.

        Recurses into any registered sub-managers first, so windows owned by
        other controllers are closed as well.
        """
        for sub in self._sub_managers:
            try:
                sub.close_all()
            except Exception:
                pass
        for instance, attr_name in self._tracked_attrs:
            window = getattr(instance, attr_name, None)
            if window is not None:
                try:
                    window.close()
                except Exception:
                    # Avoid RuntimeError: libshiboken: Internal C++ object (Panel) already deleted.
                    pass
        for window in self._child_windows:
            if window is not None:
                try:
                    window.close()
                except Exception:
                    # Avoid RuntimeError: libshiboken: Internal C++ object (Panel) already deleted.
                    pass
        self._child_windows.clear()
        self._tracked_attrs.clear()
        self._sub_managers.clear()
