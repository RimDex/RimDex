import pytest

from app.core.window_launch_state import apply_window_launch_state


class _FakeWindow:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def showMaximized(self) -> None:
        self.calls.append("maximized")

    def showNormal(self) -> None:
        self.calls.append("normal")

    def show(self) -> None:
        self.calls.append("show")

    def resize(self, width: int, height: int) -> None:
        self.calls.append(("resize", width, height))


@pytest.fixture
def fake_window() -> _FakeWindow:
    return _FakeWindow()


def test_maximized(fake_window: _FakeWindow) -> None:
    apply_window_launch_state(fake_window, "maximized", 0, 0)
    assert fake_window.calls == ["maximized"]


def test_normal(fake_window: _FakeWindow) -> None:
    apply_window_launch_state(fake_window, "normal", 0, 0)
    assert fake_window.calls == ["normal"]


def test_custom_resizes_and_shows(
    monkeypatch: pytest.MonkeyPatch, fake_window: _FakeWindow
) -> None:
    from app.models.settings import Settings

    monkeypatch.setattr(Settings, "validate_window_custom_size", lambda w, h: (w, h))
    apply_window_launch_state(fake_window, "custom", 800, 600)
    assert ("resize", 800, 600) in fake_window.calls
    assert "show" in fake_window.calls


def test_custom_validates_size(
    monkeypatch: pytest.MonkeyPatch, fake_window: _FakeWindow
) -> None:
    from app.models.settings import Settings

    monkeypatch.setattr(
        Settings, "validate_window_custom_size", lambda w, h: (1024, 768)
    )
    apply_window_launch_state(fake_window, "custom", -5, -5)
    assert ("resize", 1024, 768) in fake_window.calls


def test_unknown_state_is_ignored(fake_window: _FakeWindow) -> None:
    apply_window_launch_state(fake_window, "bogus", 0, 0)
    assert fake_window.calls == []
