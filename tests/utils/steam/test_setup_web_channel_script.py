import time
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWidgets import QApplication

from app.utils.steam.steambrowser.page_scripts import build_web_channel_script

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "setup_web_channel_script.js"
DATA_DIR = PROJECT_ROOT / "tests" / "data"


def _build_script(
    installed_mods: list[str] | None = None,
    added_mods: list[str] | None = None,
    page_mode: str = "browse",
) -> str:
    """Substitute template variables so the JS is valid to inject."""
    return build_web_channel_script(
        installed_mods=installed_mods or [],
        added_mods=added_mods or [],
        page_mode=page_mode,
        script_path=SCRIPT_PATH,
        inject_delay_ms=0,
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


def _load_html(qtbot: Any, fixture_name: str) -> QWebEnginePage:
    html_content = (DATA_DIR / fixture_name).read_text(encoding="utf-8")
    page = QWebEnginePage()
    with qtbot.waitSignal(page.loadFinished, timeout=15000) as blocker:
        page.setHtml(html_content, baseUrl=QUrl("https://steamcommunity.com/"))
    assert blocker.args[0], "Page load failed"
    return page


@pytest.fixture
def html_page(qapp: Any, qtbot: Any) -> Any:
    """Load the React SSR workshop page fixture in QWebEnginePage."""
    page = _load_html(qtbot, "new_workshop_page.html")
    yield page
    page.deleteLater()


@pytest.fixture
def hub_page(qapp: Any, qtbot: Any) -> Any:
    """Load the workshop hub fixture in QWebEnginePage."""
    page = _load_html(qtbot, "new_workshop_hub_page.html")
    yield page
    page.deleteLater()


def _inject(page: QWebEnginePage, script: str) -> None:
    page.runJavaScript(
        script, QWebEngineScript.ScriptWorldId.MainWorld, lambda _=None: None
    )


def _inject_and_run(
    page: QWebEnginePage,
    installed_mods: list[str] | None = None,
    added_mods: list[str] | None = None,
    page_mode: str = "browse",
) -> None:
    """Inject the script and call the page-mode entry point."""
    _inject(
        page,
        _build_script(
            installed_mods=installed_mods,
            added_mods=added_mods,
            page_mode=page_mode,
        ),
    )
    if page_mode == "browse":
        _inject(page, "updateAllModBadges()")
    elif page_mode == "hub":
        _inject(page, "rimdexInjectHubAddButtons()")


class TestSetupWebChannelScript:
    """Tests for setup_web_channel_script.js injected into Steam Workshop pages."""

    def test_badges_created_with_correct_states(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """3 badges should be created with one each of installed / added / default."""
        page = html_page
        _inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
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
        _inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
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
        assert default_html == "Add to list", (
            f"Default badge expected 'Add to list', got {default_html!r}"
        )

        default_title = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-default')?.title",
        )
        assert default_title == "Add to list"

    def test_idempotent_badges(self, html_page: QWebEnginePage, qtbot: Any) -> None:
        """Calling updateAllModBadges multiple times should not duplicate badges."""
        page = html_page

        _inject(page, _build_script(installed_mods=["111111"], added_mods=["222222"]))
        qtbot.wait(300)

        _inject(page, "updateAllModBadges()")
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

        _inject(page, _build_script())
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
        _inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
        qtbot.wait(500)

        position = _page_eval(
            page,
            "(function(){ var t = _findModTile('111111'); return t ? t.style.position : null; })()",
        )
        assert position == "relative"

    def test_css_injected(self, html_page: QWebEnginePage, qtbot: Any) -> None:
        """CSS should be injected into document.head."""
        page = html_page

        _inject(page, _build_script())
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

        _inject(page, _build_script())
        qtbot.wait(500)

        title = _page_eval(
            page,
            "(function(){ var t = _findModTile('111111'); return _getModTitle(t, '111111'); })()",
        )
        assert title is not None
        assert isinstance(title, str)
        assert len(title) > 0

    def test_no_badges_outside_browse_mode(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """updateAllModBadges must be a no-op unless the page mode is 'browse'."""
        page = html_page

        _inject(page, _build_script(page_mode="detail"))
        _inject(page, "updateAllModBadges()")
        qtbot.wait(500)

        count = _page_eval(
            page,
            "document.querySelectorAll('.rimdex-modstatus-badge').length",
        )
        assert count == 0, f"Expected no badges in detail mode, got {count}"

    def test_grid_page_class_added_in_browse_mode(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """Browse mode should tag <body> so default badges are always visible."""
        page = html_page

        _inject(page, _build_script(page_mode="browse"))
        qtbot.wait(500)

        has_class = _page_eval(
            page, "document.body.classList.contains('rimdex-grid-page')"
        )
        assert has_class is True

    def test_default_badge_visible_on_grid(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """On the grid, a default badge should be visible without hover."""
        page = html_page

        _inject_and_run(page, installed_mods=["111111"], added_mods=["222222"])
        qtbot.wait(500)

        visibility = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-default')?.style.visibility",
        )
        assert visibility == "visible"

    def test_default_badge_hidden_outside_browse_mode(
        self, html_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """Outside browse mode a default badge starts hidden until hover."""
        page = html_page

        _inject(page, _build_script(page_mode="detail"))
        _inject(page, "updateModBadge('111111', 'default')")
        qtbot.wait(300)

        visibility = _page_eval(
            page,
            "document.querySelector('.rimdex-mod-default')?.style.visibility",
        )
        assert visibility == "hidden"


class TestHubAddButtons:
    """Tests for the workshop hub add-button injection."""

    def test_hub_buttons_created_with_correct_states(
        self, hub_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """One hub button per card, matching installed / added / default."""
        page = hub_page
        _inject_and_run(
            page, installed_mods=["111111"], added_mods=["222222"], page_mode="hub"
        )
        qtbot.wait(500)

        count = _page_eval(
            page, "document.querySelectorAll('.rimdex-hub-add-btn').length"
        )
        assert count == 3, f"Expected 3 hub buttons, got {count}"

        installed = _page_eval(
            page, "document.querySelectorAll('.rimdex-hub-installed').length"
        )
        assert installed == 1, f"Expected 1 installed hub button, got {installed}"

        added = _page_eval(
            page, "document.querySelectorAll('.rimdex-hub-added').length"
        )
        assert added == 1, f"Expected 1 added hub button, got {added}"

        default = _page_eval(
            page, "document.querySelectorAll('.rimdex-hub-default').length"
        )
        assert default == 1, f"Expected 1 default hub button, got {default}"

    def test_hub_buttons_carry_mod_id_and_title(
        self, hub_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """Buttons should record the mod ID and be labelled from the card title."""
        page = hub_page
        _inject_and_run(page, page_mode="hub")
        qtbot.wait(500)

        mod_id = _page_eval(
            page,
            "document.querySelector('.rimdex-hub-add-btn[data-mod-id=\"111111\"]') !== null",
        )
        assert mod_id is True

        text = _page_eval(
            page,
            "document.querySelector('.rimdex-hub-add-btn[data-mod-id=\"111111\"]')?.textContent",
        )
        assert text == "Add to list"

    def test_hub_buttons_idempotent(self, hub_page: QWebEnginePage, qtbot: Any) -> None:
        """Re-running the hub injection must not duplicate buttons."""
        page = hub_page

        _inject(page, _build_script(page_mode="hub"))
        qtbot.wait(300)
        _inject(page, "rimdexInjectHubAddButtons()")
        qtbot.wait(300)

        count = _page_eval(
            page, "document.querySelectorAll('.rimdex-hub-add-btn').length"
        )
        assert count == 3, f"Expected 3 hub buttons after second call, got {count}"

    def test_no_legacy_badges_in_hub_mode(
        self, hub_page: QWebEnginePage, qtbot: Any
    ) -> None:
        """Hub mode should use add-buttons, not tile badges."""
        page = hub_page

        _inject(page, _build_script(page_mode="hub"))
        qtbot.wait(500)

        count = _page_eval(
            page, "document.querySelectorAll('.rimdex-modstatus-badge').length"
        )
        assert count == 0, f"Expected no tile badges in hub mode, got {count}"
