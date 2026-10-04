# TODO

Findings from a systematic comparison of RimDex against the local RimSort checkout
(`D:\Github\RimSort`, branch `main`). Every item was verified against real code in both
trees; items whose absence could not be confirmed were dropped rather than guessed.

**This list is complete — all 32 items are closed.** Item numbers are **stable IDs from the
original 32-item audit**, so gaps in the numbering are intentional; do not renumber, because
commit messages cite them. Items 31 and 32 were closed by a deliberate accept rather than a
code change — see their rows below and `AGENTS.md` § "Known divergences from upstream".

These gaps were *pre-existing* divergences from the fork point, not un-absorbed upstream
commits. Upstream commit tracking is separate: RimDex had absorbed every RimSort `app/`
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

## P0 — User-facing breakage (all closed)

- [x] **6. Workshop page modes are not detected — hub and browse pages get no add controls.**
  Ported `resolve_workshop_page_mode` to `app/utils/steam/steambrowser/browser.py`;
  `page_scripts.py` substitutes `@page_mode@` and the injected JS branches on it
  (`hub` / `browse` / `detail` / `other`).
- [x] **10. No History-API URL sync — SPA navigation leaves state stale.** Added the
  `@Slot(str) on_url_changed` bridge slot and `SteamBrowser._sync_location_from_js`; the
  script wraps `pushState`/`replaceState` and listens for `popstate`.
- [x] **13. No per-card add buttons on the Workshop hub page.** Ported the hub-card block
  (`rimdexFindQuickViewButtons`, `rimdexInjectHubAddButtons`, `rimdexUpdateHubAddButton`)
  into `setup_web_channel_script.js`.
- [x] **14. Badge updates do not re-sync the visible grid.** `_update_badge_js` re-syncs
  per page mode via `refresh_badge_scripts` / `refresh_hub_buttons`.
- [x] **15. Grid pages keep the add badge hidden until hover.** Browse mode tags
  `<body>` with `rimdex-grid-page`; the stylesheet forces `.rimdex-mod-default` visible.
- [x] **16. "Recently updated" indicator is not clickable and its tooltip is static.**
  `mod_list_item_inner.py` uses `ClickableQLabel` opening the Workshop changelog, with a
  `get_relative_time` tooltip.
- [x] **17. No bulk `repolish_all_items`.** Added to
  `app/views/mixins/list_item_mixin.py`, called by `main_content_panel.py` after a rebuild.
- [x] **18. `GetPublishedFileDetails` does not retry read timeouts.** `wrapper.py` retries
  `Timeout`/`ConnectionError`/`ChunkedEncodingError` via `_RETRYABLE_REQUEST_ERRORS`.
- [x] **19. Steam database not persisted when the Steamworks phase is skipped.** `wrapper.py`
  dumps the result before the `get_appid_deps` branch.
- [x] **21. Instance backup no longer reports compression failures.** `instance_service.py`
  guards the emit and calls `show_fatal_error` with `format_exc()`.
- [x] **22. Missing-mod-properties panel exposes delete-and-unsubscribe actions.**
  `columns_mixin.py` takes `include_delete` / `enable_delete_and_unsubscribe`; the panel
  disables both Steam delete variants.
- [x] **23. Database Builder settings are silently discarded.** `database_builder_dialog.py`
  gained a Save button wired to `_save_settings`.
- [x] **24. "Remove mod from list" is the only untranslated downloader string.**
  `download_list.py` uses `QCoreApplication.translate("DownloadListManager", ...)` and a
  parented `QMenu`; the string was added to all 10 `.ts`.
- [x] **25. Badge-script injection has no exception handling.** `inject_badge_scripts` wraps
  the build in `try/except` + `logger.error`.
- [x] **27. Toolbar "Add to list" appears on grid pages and always errors.** Gated on
  `toolbar_add_to_list_visible`, applied on every load *and* on History-API navigation.
- [x] **28. pfid parsing does not normalize.** Extracted `parse_publishedfileid_from_url`
  (split `#`/`&`/`?`/`/`, `strip()`, `or None`).
- [x] **29. No regression tests for the diverged dialogs.** Added
  `tests/windows/test_missing_dependencies_dialog.py` (15 tests: selection, `show_dialog`,
  `workshop_restore_target` handoff, download button).

## P2 — Minor, parity or discoverability only (all closed)

- [x] **30. `_get_selected_mod_count` helper absent.** Added to `app/views/deletion_menu.py`
  for API parity.
- [x] **31. Database expiry moved to the Advanced tab.** Accepted, no code change. Field,
  default (`0`) and label are identical; RimDex's `int()` parse falls back to `0` where
  RimSort's raises `ValueError`, so RimDex is the more robust placement. Discoverability only.
- [x] **32. Missing-dependencies dialog is application-modal.** Accepted, no code change.
  RimDex's `self.exec()` is the conventional modal choice; the `workshop_restore_target`
  handoff and download-button enablement it depends on are now covered by tests. Recorded in
  `AGENTS.md` § "Known divergences from upstream".

## Regression tests added

- [x] `tests/utils/steam/test_setup_web_channel_script.py` — rewritten against
  `build_web_channel_script` (15 QWebEngine tests: browse badges, hub add-buttons,
  grid-page class, badge visibility, idempotency, no-badges-outside-browse).
- [x] `tests/utils/steam/test_steam_browser_page_modes.py` — 30 tests for
  `parse_publishedfileid_from_url`, `resolve_workshop_page_mode`,
  `toolbar_add_to_list_visible`.
- [x] `tests/windows/test_missing_dependencies_dialog.py` — 15 tests (item 29).
- [x] `tests/data/new_workshop_hub_page.html` — hub fixture for the add-button tests.

## Notes for future syncs

- `setup_web_channel_script.js` now uses `@marker@` substitution, **not** `string.Template`
  — the script contains JS template literals, whose `${...}` sequences `Template` would
  misread. Diff this file first when porting upstream browser changes.
- The committed `locales/*.ts` files have no `<location>` elements, so running
  `just i18n-update` in place rewrites all 11 files (~17k-line diff). To add a string,
  extract to a scratch copy and splice only the new `<message>` blocks, or normalise the
  `.ts` files to carry locations in a separate change.
- Working rules for any new work: match surrounding style; no explanatory comments; no
  wholesale reformatting; full type annotations; no new `# type: ignore`; new user-facing
  strings go through `QCoreApplication.translate(...)`; leaf layers must not import
  `views`/`controllers`/`windows`; run `just fix`, `just check`, and `just test`.
