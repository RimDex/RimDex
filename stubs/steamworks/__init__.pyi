"""Pyright type stubs for the SteamworksPy runtime package.

The real ``steamworks`` package lives in ``submodules/SteamworksPy`` and is a
ctypes-based runtime-only library with no type information. The RimDex code
only needs a small, well-known surface typed so pyright can resolve the
imports without ``reportMissingImports`` / ``reportAttributeAccessIssue``.
"""

from ctypes import Structure
from typing import Any

class STEAMWORKS:
    def __getattr__(self, name: str) -> Any: ...

class GetAppDependenciesResult(Structure): ...
