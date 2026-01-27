"""Structural interface for the runner panel used by leaf layers.

Declared here (a leaf-safe ``ui/widgets`` module) so adapters in ``utils/*``
can type against the runner without importing ``app/windows/runner_panel``.
Only the members actually used by those adapters are declared.
"""

from typing import Any, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class RunnerPanelProtocol(Protocol):
    """Minimal structural view of ``RunnerPanel`` needed by steamcmd/worker code."""

    def message(self, line: str) -> None: ...

    def execute(
        self,
        command: str,
        args: Sequence[str],
        progress_bar: Optional[int] = None,
    ) -> None: ...

    def close(self) -> bool: ...

    # Populated by SteamcmdInterface.download_mods via the runner instance.
    _pending_steamcmd_batches: list[list[str]]
    _steamcmd_executable: str
    _steamcmd_wrapper: Any
