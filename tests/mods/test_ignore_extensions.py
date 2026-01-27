from app.mods.ignore_extensions import IGNORE_EXTENSIONS


def test_ignore_extensions_is_non_empty_list() -> None:
    assert isinstance(IGNORE_EXTENSIONS, list)
    assert len(IGNORE_EXTENSIONS) > 0


def test_ignore_extensions_are_dot_prefixed_strings() -> None:
    assert all(
        isinstance(ext, str) and ext.startswith(".") and ext[1:]
        for ext in IGNORE_EXTENSIONS
    )


def test_ignore_extensions_contains_common_entries() -> None:
    # A sample of the platform/archive/media extensions the file search skips.
    for expected in (".exe", ".dll", ".zip", ".pyc", ".DS_Store", ".tmp"):
        assert expected in IGNORE_EXTENSIONS
