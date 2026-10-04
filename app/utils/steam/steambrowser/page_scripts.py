import json
from pathlib import Path
from typing import Any

from loguru import logger
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript

from app.core.app_info import AppInfo

from .badge_state import BadgeState


def _noop(*_: Any) -> None:
    """Shared no-op callback for ``runJavaScript``."""


def build_web_channel_script(
    *,
    installed_mods: list[str],
    added_mods: list[str],
    page_mode: str,
    script_path: Path,
    inject_delay_ms: int = 300,
) -> str:
    """Render ``setup_web_channel_script.js`` by marker replacement.

    Marker replacement (``@name@``) is used instead of ``string.Template``
    because the script contains JS template literals, whose ``${...}``
    sequences would be mistaken for placeholders.
    """
    raw_script = script_path.read_text(encoding="utf-8")
    js_badge_state = {member.name: member.value for member in BadgeState}
    replacements = {
        "@badge_state_js@": json.dumps(js_badge_state),
        "@page_mode@": page_mode,
        "@installed_mods@": json.dumps(installed_mods),
        "@added_mods@": json.dumps(added_mods),
        "@inject_delay_ms@": str(inject_delay_ms),
    }
    script = raw_script
    for marker, value in replacements.items():
        script = script.replace(marker, value)
    return script


# ---------------------------------------------------------------------------
# Inline script constants  (kept here so they are easy to find / test)
# ---------------------------------------------------------------------------

_REMOVE_INSTALL_BUTTON = """
var elements = document.getElementsByClassName("header_installsteam_btn header_installsteam_btn_green");
while (elements.length > 0) {
    elements[0].parentNode.removeChild(elements[0]);
}
"""

_CHANGE_TARGET_A = """
var linkSelectors = [
    ".workshopItem a",
    ".collectionItem a",
    'a[href*="filedetails/?id="]'
];
for (var s = 0; s < linkSelectors.length; s++) {
    var elements = document.querySelectorAll(linkSelectors[s]);
    for (var i = 0, l = elements.length; i < l; i++) {
        elements[i].target = "_self";
    }
}
"""

_REMOVE_SUBSCRIBE_AREA = """
var elements = document.getElementsByClassName("game_area_purchase_game");
while (elements.length > 0) {
    elements[0].parentNode.removeChild(elements[0]);
}
"""

_REMOVE_COLLECTION_SUBSCRIBE = """
var elements = document.getElementsByClassName("subscribeCollection");
while (elements.length > 0) {
    elements[0].parentNode.removeChild(elements[0]);
}
"""

_REMOVE_SUBSCRIBE_BUTTONS = """
var elements = document.getElementsByClassName("general_btn subscribe");
while (elements.length > 0) {
    elements[0].parentNode.removeChild(elements[0]);
}
"""

_ADD_COLLECTION_BUTTONS = """
(function(installedMods) {
    var collectionItems = document.getElementsByClassName('collectionItem');
    for (var i = 0; i < collectionItems.length; i++) {
        var item = collectionItems[i];
        var modId = item.id.replace('sharedfile_', '');
        var subscriptionControls = item.querySelector('.subscriptionControls');
        if (!subscriptionControls) continue;

        var isInstalled = installedMods && installedMods.indexOf(modId) !== -1;

        if (isInstalled) {
            var installedIndicator = document.createElement('div');
            installedIndicator.innerHTML = '\u2713';
            installedIndicator.style.backgroundColor = '#4CAF50';
            installedIndicator.style.color = 'white';
            installedIndicator.style.width = '24px';
            installedIndicator.style.height = '24px';
            installedIndicator.style.borderRadius = '4px';
            installedIndicator.style.display = 'flex';
            installedIndicator.style.alignItems = 'center';
            installedIndicator.style.justifyContent = 'center';
            installedIndicator.style.fontWeight = 'bold';
            installedIndicator.style.fontSize = '16px';
            subscriptionControls.innerHTML = '';
            subscriptionControls.appendChild(installedIndicator);
        } else {
            var linkButton = document.createElement('a');
            linkButton.innerHTML = '\u2192';
            linkButton.href = 'https://steamcommunity.com/sharedfiles/filedetails/?id=' + modId;
            linkButton.style.backgroundColor = '#2196F3';
            linkButton.style.color = 'white';
            linkButton.style.width = '24px';
            linkButton.style.height = '24px';
            linkButton.style.borderRadius = '4px';
            linkButton.style.display = 'flex';
            linkButton.style.alignItems = 'center';
            linkButton.style.justifyContent = 'center';
            linkButton.style.cursor = 'pointer';
            linkButton.style.fontWeight = 'bold';
            linkButton.style.fontSize = '20px';
            linkButton.style.textDecoration = 'none';
            subscriptionControls.innerHTML = '';
            subscriptionControls.appendChild(linkButton);
        }
    }
})(window.installedMods);
"""

_ADD_INSTALLED_INDICATOR = """
var installedDiv = document.createElement('div');
installedDiv.style.backgroundColor = '#4CAF50';
installedDiv.style.color = 'white';
installedDiv.style.padding = '10px';
installedDiv.style.borderRadius = '5px';
installedDiv.style.marginBottom = '10px';
installedDiv.style.textAlign = 'center';
installedDiv.style.fontWeight = 'bold';
installedDiv.innerHTML = '\u2713 Already Installed';
var contentDiv = document.querySelector('.workshopItemDetailsHeader');
if (contentDiv) {
    contentDiv.parentNode.insertBefore(installedDiv, contentDiv);
}
"""


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class PageScriptManager:
    """Injects JavaScript into the Steam browser ``QWebEnginePage``.

    Each public method handles one concern (button removal, badge setup,
    etc.) so ``_web_view_load_finished`` in ``SteamBrowser`` can be
    decomposed into small, named calls.
    """

    def __init__(self, page: QWebEnginePage) -> None:
        self._page = page

    # -- Steam-chrome removals (always run on Steam pages) ----------------

    def remove_install_button(self) -> None:
        self._run(_REMOVE_INSTALL_BUTTON)

    def change_target_to_self(self) -> None:
        self._run(_CHANGE_TARGET_A)

    # -- Badge / QWebChannel script ---------------------------------------

    def inject_badge_scripts(
        self,
        installed_mods: list[str],
        added_mods: list[str],
        page_mode: str,
        inject_delay_ms: int = 300,
    ) -> None:
        """Read the external ``setup_web_channel_script.js`` template,
        substitute the current mod lists and page mode, and inject it."""
        try:
            script = build_web_channel_script(
                installed_mods=installed_mods,
                added_mods=added_mods,
                page_mode=page_mode,
                script_path=Path(AppInfo().setup_web_channel_script_file),
                inject_delay_ms=inject_delay_ms,
            )
        except Exception as exc:
            logger.error(f"Failed to inject workshop badge script: {exc}")
            return
        # Also make the list available on ``window`` so other inline
        # scripts (e.g. collection buttons) can reference it.
        self._run(f"window.installedMods = {json.dumps(installed_mods)};")
        self._run(script)

    def refresh_badge_scripts(self) -> None:
        """Re-badge the current grid after an in-page navigation."""
        self._run(
            "if (typeof window.updateAllModBadges === 'function') "
            "{ window.updateAllModBadges(); }"
        )

    def refresh_hub_buttons(self) -> None:
        """Re-inject the hub add-buttons after an in-page navigation."""
        self._run(
            "if (typeof window.rimdexInjectHubAddButtons === 'function') "
            "{ window.rimdexInjectHubAddButtons(); }"
        )

    # -- Item / collection page scripts -----------------------------------

    def remove_subscribe_area(self) -> None:
        self._run(_REMOVE_SUBSCRIBE_AREA)

    def remove_collection_subscribe(self) -> None:
        self._run(_REMOVE_COLLECTION_SUBSCRIBE)

    def remove_subscribe_buttons(self) -> None:
        self._run(_REMOVE_SUBSCRIBE_BUTTONS)

    def inject_collection_buttons(self) -> None:
        self._run(_ADD_COLLECTION_BUTTONS)

    def inject_installed_indicator(self) -> None:
        self._run(_ADD_INSTALLED_INDICATOR)

    # -- Generic helper ---------------------------------------------------

    def _run(self, script: str) -> None:
        self._page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, _noop
        )
