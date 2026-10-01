# TODO

Findings from a systematic comparison of RimDex against the local RimSort checkout
(`D:\Github\RimSort`, branch `main`). Every item was verified against real code in both
trees; items whose absence could not be confirmed were dropped rather than guessed.

**This list contains open items only.** Completed entries are removed as they land; the
last 12 (items 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 20, 26) are done. Item numbers are
therefore **stable IDs from the original 32-item audit**, and the gaps in the numbering
are intentional — do not renumber, because commit messages cite them.

These 20 gaps are *pre-existing* divergences from the fork point, not un-absorbed upstream
commits. Upstream commit tracking is separate: RimDex has absorbed every RimSort `app/`
change through **`88e9d295`** (2026-10-01). See [`AGENTS.md`](AGENTS.md) § "RimSort sync
tracking" for the baseline, the deferred infra/dependency items, and the command to diff
the next upstream range.

## How this list was produced

- **AST symbol inventory** of every class/function/method in both `app/` trees, diffed
  after normalising the `RimSort` — `RimDex` rename and Python's `_private` name mangling.
  This isolates real gaps from the refactor's renames and moves.

- **Area-by-area behavioural comparison** of every subsystem, cross-checked with
  CocoIndex semantic search (`ccc search`) against *RimDex* — searching for the concept,
  not the identifier, so renames don't produce false negatives.

- Spot-verification of the highest-impact claims by reading both sides directly.

## Verified as equivalent (do not "fix" these)

These looked like gaps but are intentional or already better in RimDex. Recorded so they
are not re-investigated:

- **Settings model is complete.** RimSort's 102 settings attributes and `Instance`'s 13
  fields are identical in name, type and default. All 9 tab controllers are present.

- **No missing dialogs.** Every window class in RimSort's `app/windows/` exists in RimDex
  and is reachable. (Names like `play_config_window` / `apikey_window` predate the 2023
  `base_mods_panel` rewrite and exist in neither tree.)

- **`_do_notify_no_git` is dead code upstream.** RimSort defines it
  (`app/views/main_content_panel.py:2883`) but never calls it. Its absence in RimDex is not
  a gap — do not port it.

- RimDex is strictly better in `runner_panel.py` (continuous cross-phase progress bar,
  SteamCMD `console_log.txt` tail), the Advanced-tab `database_expiry` int parse guard,
  `dependency_resolver.py` as a reusable service, `translation_manager.py`, and the
  `base_mods_panel` — `app/windows/mixins/*` split (all 40 methods preserved 1:1).

- RimSort has no TODDS binary download/verify and no HTTP proxy support, so those are not
  RimDex regressions.

---

## P0 — User-facing breakage

### 6. Workshop page modes are not detected — hub and browse pages get no add controls

- **RimSort:** `app/utils/steam/steambrowser/browser.py:94` (`resolve_workshop_page_mode`)
  classifies `hub` / `browse` / `detail` and substitutes `@page_mode@` into the script.

- **RimDex:** `browser.py:542` requires the literal substring `"section="`;
  `page_scripts.py:133` substitutes only `installed_mods` / `added_mods`.

- **Impact:** `steamcommunity.com/workshop/browse/?appid=294100`, `/myworkshopfiles/`, and
  the `/app/294100/workshop/` hub all fail the substring test and return before the toolbar is
  configured. Browsing the catalogue by category — the primary Workshop entry point, and
  RimDex's own `WORKSHOP_BROWSE_URL` — yields no way to queue anything.

- **Fix:** Port `resolve_workshop_page_mode` and branch the injected JS on the page mode.

### 10. No History-API URL sync — SPA navigation leaves state stale

- **RimSort:** `js_bridge.py:37` exposes `@Slot(str) on_url_changed`, plus
  `_on_web_view_url_changed`, `_sync_location_from_js`, `_get_effective_page_url`,
  `_normalize_browse_url`, `_update_toolbar_add_to_list_button`, and
  `toolbar_add_to_list_visible()`; the script wraps `history.pushState`/`replaceState`.

- **RimDex:** `js_bridge.py` exposes only `add_mod_from_js` / `remove_mod_from_js`;
  `browser.py:518` assigns `current_url` only inside `_web_view_load_finished`; `:174-176`
  connects only `loadStarted`/`loadProgress`/`loadFinished`.

- **Impact:** Steam's Workshop is a React SPA that routes without a page load. The location
  bar and window title go stale, the toolbar button desyncs, and `_parse_pfid_from_url`
  resolves the **previously visited** mod — so "Add to list" can queue the wrong mod.

- **Fix:** Add the `on_url_changed` slot and the history-wrapping JS.

### 13. No per-card add buttons on the Workshop hub page

- **RimSort:** `setup_web_channel_script.js` implements `rimsortFindQuickViewButtons`,
  `rimsortModIdFromHubCard`, `rimsortCreateHubAddButton`, `rimsortInjectHubAddButtons`,
  `rimsortUpdateHubAddButton`, with a `MutationObserver` for streamed-in cards.

- **RimDex:** the script starts at `var BADGE_STATE_JS` with no `PAGE_MODE` and no hub-card
  factories.

- **Impact:** Users landing on the RimWorld Workshop hub get neither a status badge nor an
  inline add control on any card, and cannot tell which entries are already installed.

- **Fix:** Port the hub-card block and route `_update_badge_js` to it in hub mode.

### 14. Badge updates do not re-sync the visible grid

- **RimSort:** `browser.py:1139-1156` calls `rimsortUpdateHubAddButton` in hub mode and
  `window.updateAllModBadges()` in browse mode.

- **RimDex:** `_update_badge_js` (`browser.py:625-636`) calls only
  `window.updateModBadge(modId, status)`.

- **Impact:** Tiles skipped by the `updateAllModBadges` querySelector guard stay stale after
  an add/remove.

- **Fix:** Re-sync the whole grid per page mode.

### 15. Grid pages keep the add badge hidden until hover

- **RimSort:** adds a `rimsort-grid-page` body class plus CSS forcing
  `.rimsort-mod-default { opacity:1; visibility:visible }` on grid pages.

- **RimDex:** `setup_web_channel_script.js:213-218` always hides `.rimdex-mod-default`
  until `mouseenter`.

- **Impact:** On a Workshop grid the add control is undiscoverable without hovering each tile.

- **Fix:** Drive the override from the page mode (depends on item 6).

### 16. "Recently updated" indicator is not clickable and its tooltip is static

- **RimSort:** `app/views/mods_panel.py:272-273` uses a `ClickableQLabel` wired to
  `__on_updated_icon_clicked` (`:400`), which opens
  `steamcommunity.com/sharedfiles/filedetails/changelog/{pfid}`; the repolish tooltip
  (`:695`) renders `get_relative_time(...)`.

- **RimDex:** `app/views/mod_list_item_inner.py:141` uses a plain `QLabel` with a static
  `"Recently updated on Workshop"` tooltip; `repolish` only shows/hides it.

- **Impact:** Users cannot open a mod's changelog from the list, and the tooltip never says
  how recent the update was — even though `get_relative_time` already exists unused at
  `app/core/text_utils.py:13`.

- **Fix:** Port the handler and the relative-time tooltip, guarding on a missing pfid.

### 17. No bulk `repolish_all_items`

- **RimSort:** `app/views/mods_panel.py:3011` iterates all items and repolishes each widget;
  called after a full list rebuild.

- **RimDex:** only per-item `repolish` (`app/views/mixins/list_item_mixin.py:180,220`);
  `app/views/mod_list_widget.py` has no bulk equivalent.

- **Impact:** Theme/visual refresh after a full rebuild relies on incremental per-row
  updates, which `recreate_mod_list` disconnects during the rebuild.

- **Fix:** Add `repolish_all_items()` to the mod list widget or list-item mixin.

### 18. `GetPublishedFileDetails` does not retry read timeouts

- **RimSort:** `app/utils/steam/webapi/wrapper.py:905-967` retries each 300-PFID chunk up to
  3 times on `Timeout`, `ConnectionError`, `ChunkedEncodingError` and `HTTPError` with
  `sleep(2**attempt)` backoff.

- **RimDex:** `wrapper.py:1004-1032` retries only `ChunkedEncodingError`; the shared adapter
  sets `read=0` (`app/net/http.py:35`), disabling urllib3 read retries, so a `ReadTimeout`
  falls through to the generic `except` and fails the whole chunk on the first slow response.

- **Impact:** One slow Steam response (timeout is `timeout=(5, 60)`) discards metadata for up
  to 300 mods instead of recovering.

- **Fix:** Catch `requests.exceptions.Timeout` and `ConnectionError` in the inner handler,
  keeping the existing backoff and `_MAX_CHUNK_ATTEMPTS` budget.

### 19. Steam database not persisted when the Steamworks phase is skipped

- **RimSort:** `app/utils/steam/webapi/wrapper.py:736` dumps the Web API result to
  `output_database_path` *before* the Steam availability check and pool launch.

- **RimDex:** `wrapper.py:581-596` writes only on the success path or when
  `get_appid_deps` is false; a pool-init failure returns without writing.

- **Impact:** Freshly downloaded Workshop metadata is handed back in memory and discarded,
  forcing a full re-query next time.

- **Fix:** Add an unconditional `atomic_json_dump(...)` before the `if self.get_appid_deps:`
  block.

### 21. Instance backup no longer reports compression failures

- **RimSort:** `app/services/instance_service.py:271-298` wraps the loading-animation emit
  in `try/except` and calls `show_fatal_error` with `details=format_exc()`.

- **RimDex:** `instance_service.py:305-316` emits with no guard, so the worker exception
  propagates uncaught (captured at `app/ui/widgets/animations.py:149-153`).

- **Impact:** A failed backup (disk full, permissions, locked files) yields a raw traceback
  instead of a fatal-error dialog. The identical guard on `restore_instance_from_archive`
  (`:348-356`) is still present, so only the backup path regressed.

- **Fix:** Restore the `try/except` + `show_fatal_error` around the emit.

### 22. Missing-mod-properties panel exposes delete-and-unsubscribe actions

- **RimSort:** `app/windows/base_mods_panel.py:1180-1208` builds this panel's delete config
  with `enable_delete_and_unsubscribe=False`, deliberately suppressing both Steam actions.

- **RimDex:** `app/windows/missing_mod_properties_panel.py:64` calls
  `_extend_button_configs_with_steam_actions`, which unconditionally appends
  `_get_delete_button_config()` (`app/windows/mixins/columns_mixin.py:88-90`) whose defaults
  are `True` (`app/ui/widgets/button_factory.py:43-44`).

- **Impact:** "Delete mod and unsubscribe from Steam" and "Delete mod and resubscribe using
  Steam" now appear and enable whenever Steam Client Integration is on — actions upstream
  intentionally suppressed for this panel. The panel also lost the ability to override any
  delete flag, since `menu_title` / `get_selected_mod_metadata` were removed from
  `ButtonConfig`.

- **Fix:** Give the panel an explicit delete config, or parameterise `_get_delete_button_config()`
  and stop appending DELETE inside `_extend_button_configs_with_steam_actions`.

### 23. Database Builder settings are silently discarded

- **RimSort:** the DB Builder is a settings tab, so `db_builder_include`,
  `build_steam_database_dlc_data`, `build_steam_database_update_toggle`, `steam_apikey` and
  `database_expiry` are committed by the global OK button and reverted by Cancel.

- **RimDex:** `DatabaseBuilderController._save_settings` is called only from the five action
  slots, each of which immediately `close()`s; `DatabaseBuilderDialog` has no Save/OK/Cancel
  and no `closeEvent`.

- **Impact:** Change any of those toggles, then close with X/Esc — the edits are lost with no
  warning. It is also reachable differently (Tools — Database Builder rather than a tab).

- **Fix:** Add a Save/OK button bound to `_save_settings`, or override `closeEvent`.

### 24. "Remove mod from list" is the only untranslated downloader string

- **RimSort:** `browser.py:744` uses `self.tr("Remove mod from list")`, present in all 10 `.ts`.

- **RimDex:** `app/utils/steam/steambrowser/download_list.py:154` uses a bare
  `menu.addAction("Remove mod from list")`; absent from every `locales/*.ts`.

- **Impact:** The only English-only string in the downloader, in all 10 locales. The same
  `QMenu()` is also created parentless, leaking a top-level window.

- **Fix:** Use `QCoreApplication.translate("DownloadListManager", "Remove mod from list")`
  and `QMenu(self._list)`, then run `just i18n-update`. (This is a new source string; the
  `.ts` files have now been repaired, so this step is unblocked.)

### 25. Badge-script injection has no exception handling

- **RimSort:** `browser.py:962-974` wraps script build + `runJavaScript` in `try/except` and
  logs "Failed to inject workshop badge script".

- **RimDex:** `page_scripts.py:148-167` calls `read_text()` and `Template.substitute()`
  unguarded, and `browser.py:510` has no `try/except`.

- **Impact:** A missing script file or an unexpected `$identifier` raises out of a Qt slot,
  aborting the rest of page setup with only a raw traceback.

- **Fix:** Wrap `inject_badge_scripts` in `try/except` with `logger.error(...)`.

### 27. Toolbar "Add to list" appears on grid pages and always errors

- **RimSort:** `browser.py:131-154,482` — the nav-bar action is shown only when the current
  URL is an item/collection **detail** page with a parseable pfid.

- **RimDex:** `browser.py:560` calls `nav_bar.addAction(...)` unconditionally inside
  `_setup_item_or_collection_page`, which is also entered when only `is_items_page` is true
  (`:546`).

- **Impact:** On any `section=readytouseitems` grid the button shows but always fails,
  popping "No publishedfileid found / Please check if url is in the correct format".

- **Fix:** Gate the `addAction` on a successful pfid parse (a
  `toolbar_add_to_list_visible`-style predicate), not on `is_items_page`.

### 28. pfid parsing does not normalize

- **RimSort:** `browser.py:63-85` strips `—`, then `/`, then whitespace, returning `None`
  when empty.

- **RimDex:** `browser.py:386-406` splits on `#`/`&` and returns the raw remainder.

- **Impact:** A trailing slash or whitespace yields a non-empty string, so the guard never
  fires and a bogus pfid is pushed into the download list and handed to SteamCMD.

- **Fix:** Extract a shared helper with the `—`/`/`/`strip()`/`or None` handling.

### 29. No regression tests for the diverged dialogs

- **RimSort:** `tests/windows/test_missing_dependencies_dialog.py`,
  `tests/windows/test_missing_dependencies_workshop.py` (covers `workshop_restore_target`
  and `_on_steam_browser_restore`), `tests/windows/test_use_this_instead_panel_button.py`,
  `tests/controllers/test_main_window_controller.py`.

- **RimDex:** no test for `MissingDependenciesDialog`, the `workshop_restore_target`
  handoff, or `UseThisInsteadPanel._create_custom_select_button`.

- **Impact:** This is exactly why the dead restore protocol (item 4) and the disabled
  Download buttons (item 3) went unnoticed.

- **Fix:** Port `test_missing_dependencies_workshop.py` and
  `test_use_this_instead_panel_button.py`; add a sort-path test asserting
  `download_requested` is connected and `dep_resolve` reaches the dialog.

---

## P2 — Minor, parity or discoverability only

### 30. `_get_selected_mod_count` helper absent

`app/views/deletion_menu.py` computes counts inline instead. No behavioral regression; add
for API parity if other callers need it.

### 31. Database expiry moved to the Advanced tab

The field, default (`0`) and label are identical; RimSort renders it under the DB Builder
controls (`app/views/settings_dialog.py:1099`). Discoverability only — and RimDex's `int()`
parse is wrapped in a `0` fallback where RimSort's raises `ValueError`, so RimDex is the more
robust one. No code change needed.

### 32. Missing-dependencies dialog is application-modal

RimSort uses `Qt.WindowModality.NonModal` with a local `QEventLoop` so the main window stays
usable; RimDex uses `self.exec()`. A real UX divergence, but RimDex's is the conventional
choice. Accept deliberately or restore upstream's non-blocking loop.

---

## Suggested ordering

1. **Item 6 first** - page-mode detection. It gates items 13 and 15, and together with
   item 10 is the root cause of the whole remaining Workshop-browser cluster: RimDex's
   browser was simplified without the page-mode/URL-sync layer.
2. **Items 10, 13, 14, 15, 25, 27** - the rest of the browser cluster. These are only
   reachable once item 6 lands, so treat them as one batch with regression tests.
3. **Items 18, 19** - Steam metadata durability. Both are small and independent of the
   browser work, so they make a good parallel track.
4. **Items 21, 22, 23, 28** - small, self-contained correctness fixes (compression
   failure reporting, delete/unsubscribe actions, discarded Database Builder settings,
   pfid normalisation). No dependencies; safe to pick up individually.
5. **Items 16, 17** - "Recently updated" click-through and bulk `repolish_all_items`.
   Self-contained, but they read better once item 14's badge re-sync exists.
6. **Item 29** - regression tests for the diverged dialogs. Add these before or alongside
   items 22 and 23 so the ported behaviour stays fixed.
7. **Items 30, 31, 32** - P2 discoverability and polish. Lowest value; take last.
8. **Item 24** — now unblocked: the `.ts` files have been repaired, so the new
   source string `"Remove mod from list"` can be extracted via `just i18n-update`.

## Working rules for any of these

- Match the surrounding code style; no explanatory comments; no wholesale reformatting.
- Full type annotations; no new `# type: ignore` (budget is 22, see `RESTRUCTURING.md` §8.7).
- New user-facing strings go through `QCoreApplication.translate(...)`, then
  `just i18n-update` — the `.ts` files have been repaired, so this workflow now works.
- Leaf layers (`models/`, `services/`, `utils/*`) must not import
  `views`/`controllers`/`windows`; `just layer-check` guards this and several items above
  touch that boundary.
- Run `just fix`, `just check`, and `just test` before opening a PR.
