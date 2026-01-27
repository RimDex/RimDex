import json
import time
from pathlib import Path
from string import Template
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "setup_web_channel_script.js"
DATA_DIR = PROJECT_ROOT / "tests" / "data"

BADGE_STATE_JS_STR = json.dumps(
    {
        "INSTALLED": "installed",
        "ADDED": "added",
        "DEFAULT": "default",
    }
)


def _substitute_script(
    installed_mods: list[str] | None = None,
    added_mods: list[str] | None = None,
) -> str:
    """Substitute template variables so the JS is valid to inject."""
    raw = SCRIPT_PATH.read_text(encoding="utf-8")
    tmpl = Template(raw)
    return tmpl.substitute(
        badge_state_js=BADGE_STATE_JS_STR,
        installed_mods=json.dumps(installed_mods or []),
        added_mods=json.dumps(added_mods or []),
    )


def _page_eval(page: QWebEnginePage, js: str, timeout: float = 5.0) -> Any | None:
    """Run a JS expression and return its evaluated result (blocking)."""
    result: list[Any] = []

    def callback(value: Any) -> None:
        result.append(value)

    page.runJavaScript(js, QWebEngineScript.ScriptWorldId.MainWorld, callback)
    deadline = time.monotonic() + timeout
    while not result and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    return result[0] if result else None


@pytest.fixture
def html_page(qapp: Any, qtbot: Any) -> Any:
    """Load the React SSR workshop page fixture in QWebEnginePage."""
    html_file = DATA_DIR / "new_workshop_page.html"
    html_content = html_file.read_text(encoding="utf-8")

    page = QWebEnginePage()
    with qtbot.waitSignal(page.loadFinished, timeout=15000) as blocker:
        page.setHtml(html_content, baseUrl=QUrl("https://steamcommunity.com/"))

    assert blocker.args[0], "Page load failed"

    yield page
    page.deleteLater()


class TestSetupWebChannelScript:
    """Tests for setup_web_channel_script.js injected into Steam Workshop pages."""

    def _inject_and_run(
        self,
        page: QWebEnginePage,
        installed_mods: list[str] | None = None,
        added_mods: list[str] | None = None,
    ) -> None:
        """Inject the script and call updateAllModBadges()."""
        script = _substitute_script(
            installed_mods=installed_mods, added_mods=added_mods
        )
        page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda: None
        )
        page.runJavaScript(
            "updateAllModBadges()",
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda: None,
        )

    def test_badges_created_with_correct_states(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """3 badges should be created with one each of installed / added / default."""
        page = html_page
        self._inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
        qtbot.wait(500)

        count = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-modstatus-badge').length",
        )
        assert count == 3, f"Expected 3 badges, got {count}"

        installed = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-mod-installed').length",
        )
        assert installed == 1, f"Expected 1 installed badge, got {installed}"

        added = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-mod-added').length",
        )
        assert added == 1, f"Expected 1 added badge, got {added}"

        default = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-mod-default').length",
        )
        assert default == 1, f"Expected 1 default badge, got {default}"

    def test_badge_content_and_title(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """Badge innerHTML and title attribute should match the state."""
        page = html_page
        self._inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
        qtbot.wait(500)

        installed_html = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-installed')?.innerHTML",
        )
        assert installed_html == "\u2713", (
            f"Installed badge expected checkmark, got {installed_html!r}"
        )

        installed_title = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-installed')?.title",
        )
        assert installed_title == "Already installed"

        added_html = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-added')?.innerHTML",
        )
        assert added_html == "-", f"Added badge expected '-', got {added_html!r}"

        added_title = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-added')?.title",
        )
        assert added_title == "Preparing to download"

        default_html = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-default')?.innerHTML",
        )
        assert default_html == "+", f"Default badge expected '+', got {default_html!r}"

        default_title = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-default')?.title",
        )
        assert default_title == "Add to list"

    def test_idempotent_badges(self, html_page: QWebEnginePage, qtbot: Any) -> None:
        """Calling updateAllModBadges multiple times should not duplicate badges."""
        page = html_page

        script = _substitute_script(installed_mods=["111111"], added_mods=["222222"])
        page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda: None
        )
        qtbot.wait(300)

        page.runJavaScript(
            "updateAllModBadges()",
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda: None,
        )
        qtbot.wait(300)

        count = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-modstatus-badge').length",
        )
        assert count == 3, f"Expected 3 badges after second call, got {count}"

    def test_findModTile_returns_container(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """_findModTile should return a non-null element for each mod ID."""
        page = html_page

        script = _substitute_script()
        page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda: None
        )
        qtbot.wait(500)

        for mod_id in ["111111", "222222", "333333"]:
            tile_exists = _page_eval(
                page,
                f"(function(){{ return _findModTile('{mod_id}') !== null; }})()",
            )
            assert tile_exists is True, f"_findModTile returned null for {mod_id}"

    def test_tile_position_set_to_relative(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """updateModBadge should set tile.style.position to 'relative'."""
        page = html_page
        self._inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
        qtbot.wait(500)

        position = _page_eval(
            page,
            "(function(){ var t = _findModTile('111111'); return t ? t.style.position : null; })()",
        )
        assert position == "relative"

    def test_css_injected(self, html_page: QWebEnginePage, qtbot: Any) -> None:
        """CSS should be injected into document.head."""
        page = html_page

        script = _substitute_script()
        page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda: None
        )
        qtbot.wait(500)

        has_style = _page_eval(
            page,
            "!!document.querySelector('style') && document.querySelector('style').textContent.includes('rimdex-modstatus-badge')",
        )
        assert has_style is True

    def test_mod_title_fallback_to_mod_id(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """_getModTitle should return the modId when no title element is found."""
        page = html_page

        script = _substitute_script()
        page.runJavaScript(
            script, QWebEngineScript.ScriptWorldId.MainWorld, lambda: None
        )
        qtbot.wait(500)

        title = _page_eval(
            page,
            "(function(){ var t = _findModTile('111111'); return _getModTitle(t, '111111'); })()",
        )
        assert title is not None
        assert isinstance(title, str)
        assert len(title) > 0
