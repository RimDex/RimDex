"""Tests for RunnerPanel's per-mod SteamCMD success signal.

The signal backs preserving the Mod Downloader's wait-list: a mod that
SteamCMD confirms as downloaded should be droppable from it, while a failed
one must stay queued.
"""

from typing import Any
from unittest.mock import MagicMock

from app.core.event_bus import EventBus
from app.windows.runner_panel import RunnerPanel


def _make_panel_with_real_output_handler() -> Any:
    """Build a bare RunnerPanel that uses the real SteamCMD output handler."""
    panel = RunnerPanel.__new__(RunnerPanel)
    panel.steamcmd_current_pfid = "123"
    panel.steamcmd_download_tracking = ["123"]
    panel.login_error = False
    panel.progress_bar = MagicMock()
    panel.progress_bar.value.return_value = 0
    return panel


class TestSteamcmdDownloadSucceededSignal:
    def test_success_line_emits_signal_and_clears_tracking(
        self, fresh_event_bus: None
    ) -> None:
        panel = _make_panel_with_real_output_handler()
        received: list[str] = []
        EventBus().steamcmd_mod_download_succeeded.connect(received.append)

        panel._handle_steamcmd_output(
            'Success. Downloaded item 123 to "C:/mods/123" (1234 bytes)'
        )

        assert received == ["123"]
        assert panel.steamcmd_download_tracking == []

    def test_error_line_does_not_emit_signal(self, fresh_event_bus: None) -> None:
        panel = _make_panel_with_real_output_handler()
        received: list[str] = []
        EventBus().steamcmd_mod_download_succeeded.connect(received.append)

        panel._handle_steamcmd_output("ERROR! Download item 123 failed (Timeout).")

        assert received == []
        assert panel.steamcmd_download_tracking == ["123"]
