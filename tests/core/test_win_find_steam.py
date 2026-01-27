import sys

import pytest

from app.core.win_find_steam import find_steam_folder


def test_find_steam_folder_off_windows_returns_empty() -> None:
    # On non-Windows platforms the function short-circuits without touching the
    # registry and returns ("", False).
    if sys.platform != "win32":
        assert find_steam_folder() == ("", False)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows registry only")
def test_find_steam_folder_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    import winreg

    class _FakeKey:
        def __enter__(self, *a: object) -> "_FakeKey":
            return self

        def __exit__(self, *a: object) -> None:
            return None

        def QueryValueEx(self, name: str) -> tuple[str, int]:  # noqa: N802
            return (r"C:\Program Files (x86)\Steam", 1)

    monkeypatch.setattr(winreg, "OpenKey", lambda *a, **k: _FakeKey())
    monkeypatch.setattr(
        winreg, "QueryValueEx", lambda key, name: (r"C:\Program Files (x86)\Steam", 1)
    )
    # steam.exe existence is checked via os.path.isfile; stub it true.
    monkeypatch.setattr("app.core.win_find_steam.os.path.isfile", lambda p: True)
    path, found = find_steam_folder()
    assert found is True
    assert path == r"C:\Program Files (x86)\Steam"
