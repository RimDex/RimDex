"""Backward-compatible re-export shim.

All functionality has moved to focused modules under ``app.core``:

- :mod:`app.core.fs_utils` — filesystem operations, path helpers, formatting
- :mod:`app.core.text_utils` — text/time parsing, URL utilities
- :mod:`app.core.ui_helpers` — clipboard, file openers, warnings, network
- :mod:`app.core.game_launch` — game executable detection and process spawning

New code should import from the specific modules directly.
"""
