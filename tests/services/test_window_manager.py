"""Tests for ``app.services.window_manager`` (leaf layer)."""

from app.services.window_manager import WindowManager


class _StubWindow:
    def __init__(self) -> None:
        self.closed = False
        self.child: _StubWindow | None = None

    def close(self) -> None:
        self.closed = True


def test_close_all_closes_registered_windows() -> None:
    mgr = WindowManager()
    w = _StubWindow()
    mgr.register(w)
    mgr.close_all()
    assert w.closed


def test_close_all_closes_tracked_attrs() -> None:
    mgr = WindowManager()
    owner = _StubWindow()
    owner.child = _StubWindow()
    mgr.register_attr(owner, "child")
    mgr.close_all()
    assert owner.child.closed


def test_close_all_recurses_into_sub_managers() -> None:
    root = WindowManager()
    sub = WindowManager()
    w = _StubWindow()
    sub.register(w)
    root.register_manager(sub)

    root.close_all()

    assert w.closed
    # Sub-manager tracking should be cleared after close_all.
    assert sub._child_windows == []


def test_register_manager_ignores_self_and_duplicates() -> None:
    root = WindowManager()
    root.register_manager(root)
    sub = WindowManager()
    root.register_manager(sub)
    root.register_manager(sub)
    assert root._sub_managers == [sub]


def test_close_all_clears_tracking_after_close() -> None:
    mgr = WindowManager()
    mgr.register(_StubWindow())
    mgr.close_all()
    assert mgr._child_windows == []
    assert mgr._tracked_attrs == []
