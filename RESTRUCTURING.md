# RimDex `app/` — Restructuring & Improvement Plan

> This file is the detailed plan/backlog for the `app/` restructuring effort.
> Moved out of `AGENTS.md` on 2026-09-23 so the agent instruction file stays
> concise (RimSort-style). `AGENTS.md` is the index; the authoritative debt
> catalogs (§8.6 Todo / §8.7 `# type: ignore` / §8.9 actionable) live here.
> Scope: ongoing restructuring/quality improvements for `app/`
> (PySide6 RimWorld mod manager, MVC-ish layout, Python 3.12).
> Last updated: 2026-09-23 (moderate cleanup of the 2026-09-13 baseline).
> §0/§7 numbers are as measured on the 2026-09-13 run (`just stats`, `just test`);
> the `# type: ignore` and `TODO` counts in §8.7/§8.6 were re-verified on 2026-09-23.
> Re-run `just stats` to re-sync the file/LOC numbers. Counts exclude everything
> in the `.gitignore` exclusion map (see §6).
>
> Static reference lives in root files (moved 2026-09-23): full `just` recipe
> index → `CONTRIBUTING.md`; `.gitignore` exclusion map → `EXCLUSION_MAP.md`;
> platform-specific CI fixes → `CI_PLATFORM_FACTS.md`. §6/§8.8 here are pointers.

## 0. Current Snapshot

- `app/` = **222** `.py` files / 66,639 raw LOC / **54,483 curated LOC**.
- `tests/` = **133** `.py` files / 22,329 raw LOC / **17,376 curated LOC**.
- Test suite: **1492 collected → 1478 passed, 14 skipped, 0 failed** (see §7).

Layering is enforced by CI guards (`check_deferred_imports.py`,
`check_layer_violations.py`, `check_i18n_extraction.py`) plus mypy/pyright/jscpd.
`models/` → `controllers`/`views` is forbidden; `services/` and `utils/*` are
leaf layers that may not import UI/orchestration (see §2 P0). Mutable globals
were removed from `utils/globals.py` in favour of `core/app_context.py` DI.

Largest areas (curated / raw LOC, file count):
`views/` 14,627 / 17,779 / 30 · `controllers/` 9,160 / 10,921 / 36 ·
`windows/` 6,080 / 7,402 / 22 · `utils/` 5,383 / 6,587 / 34 ·
`core/` 4,653 / 5,859 / 24 · `models/` 3,048 / 3,801 / 13 ·
`services/` 2,528 / 2,927 / 11 · `git/` 2,153 / 2,734 / 6 ·
`mods/` 2,011 / 2,436 / 9 · `ui/` 1,548 / 1,949 / 12 ·
`io/` 1,503 / 1,919 / 9 · `sort/` 612 / 765 / 5 · `cli/` 478 / 621 / 4 ·
`net/` 505 / 631 / 5.

Biggest single files (raw / curated): `core/update_apply.py` (2127/1677),
`views/main_content_panel.py` (1968/1643), `git/git_operations.py` (1767/1376),
`views/mods_panel.py` (1703/1379), `views/settings_dialog.py` (1689/1345),
`views/mixins/context_menu_mixin.py` (1648/1417), `views/player_log_panel.py`
(1591/1368), `windows/rule_editor_panel.py` (1449/1241),
`views/mod_info_panel.py` (1160/1001), `controllers/file_search_controller.py`
(1147/848). `controllers/main_content_controller.py` is 165 curated LOC (211 raw).

## 1. Findings

### Status at a glance

- **P0 — leaf-layer boundary enforced:** all 12 seeded violations resolved (§2 P0).
- **P1 — mega-module splits:** `base_mods_panel.py`, `mod_list_widget.py`,
  `git_utils.py`, `update_utils.py` split; `main_content` controller + view
  handler extraction done. *Remaining:* sub-feature split of
  `main_content_panel.py`.
- **P2 — typing & debt:** `Any` 613→434, `# type: ignore` 59→17, 17 debt
  markers tracked (§8.6), `generic.py` split, handler typing.
- **P3 — testing & tooling:** Translation Manager UI + CLI, i18n pass (477
  strings), ~90 leaf-layer tests added, `just cov-gate` (45% floor) + EventBus
  docs. *Remaining:* the last untested leaf modules (§2 P3).

### Open work

- Split `views/main_content_panel.py` by sub-feature (mod lists, settings,
  GitHub updates) — still the largest view (see §2 P1 / §8.1).
- Split `views/mixins/context_menu_mixin.py` (1648/1417) and `views/mods_panel.py`
  (1703/1379) — §8.1.
- Finish remaining leaf-layer tests (`ui/widgets/`, rest of `cli/`, `core/*`,
  `git/` repo ops, `mods/db_builder*`) — §2 P3.
- Re-audit the 3 un-audited `# type: ignore` suppressions
  (`app/net/privatebin.py:44,48`, `app/git/git_operations.py:398`,
  `app/io/xml.py:9`) — §8.7 G / §8.9.

### Test results (last full run — 2026-09-13)

`pytest --doctest-modules --no-qt-log`: **1492 collected → 1478 passed, 14
skipped, 0 failed** (~39 s). These counts supersede every earlier figure recorded
in this doc.

### Layering smells (beyond the enforced `models/` rule)

`services/` and `utils/*` are leaf layers: they may not import anything inside
`app` except other leaf modules. Enforced by `check_layer_violations.py` (scans
`app/services` + `app/utils`); any _new_ violation fails `just layer-check`. Of
the 12 original seeded violations, all are fixed (6 by relocating
`views/dialogue` → `app/ui/dialogue`, 4 by retyping against leaf-defined
Protocols, 2 by dependency injection in `InstanceService`).

### Mega-modules (hard to read / test / review)

Files > 1.4k LOC still concentrate logic that should be decomposed (raw/curated):

- `core/update_apply.py` (2127/1677 — self-update apply layer)
- `views/main_content_panel.py` (1968/1643 — down from 2701 via handler extraction)
- `git/git_operations.py` (1767/1376), `views/mods_panel.py` (1703/1379)
- `views/settings_dialog.py` (1689/1345), `views/mixins/context_menu_mixin.py` (1648/1417)
- `views/player_log_panel.py` (1591/1368), `windows/rule_editor_panel.py` (1449/1241)
- `views/mod_info_panel.py` (1160/1001), `controllers/file_search_controller.py` (1147/848)

Completed splits (all backward-compatible; re-export shims retained where noted):

- `windows/base_mods_panel.py` (1191 → 48 LOC) → mixins in `app/windows/mixins/`
  (`UIBaseMixin`, `TableMixin`, `ModRowsMixin`, `SelectionMixin`, `ButtonsMixin`,
  `ColumnsMixin`).
- `views/mod_list_widget.py` (3011 → ~317 LOC) → mixins in `app/views/mixins/`
  (`ContextMenuMixin`, `DividerMixin`, `ListItemMixin`, `ErrorsWarningsMixin`,
  `ColorsTagsMixin`).
- `git/git_utils.py` (1859) → `git/git_operations.py` (~1451) +
  `git/git_notifications.py` (215); `git_utils.py` = shim.
- `core/update_utils.py` (2285) → `core/update_check.py` (pure leaf, no Qt) +
  `core/update_apply.py` (apply/UI); `update_utils.py` = 38-LOC shim.
- `core/generic.py` (745) → `fs_utils.py`, `text_utils.py`, `ui_helpers.py`,
  `game_launch.py`; shim retained.
- `controllers/main_content_controller.py` (1870 → 165 curated) — handlers in
  `app/controllers/handlers/`.

Translation batch logic deduplicated: `cli/translate.py` and
`translation_workers.py` both call `translate_language_batch()` from
`core/translation_utils.py`.

### Typing gaps

- **434** `Any` annotations across `app/`. Most are legitimate `dict[str, Any]`
  (JSON/ACF data) and `list[Any]` (Steamworks instruction tuples); a smaller set
  are intentional mixin stubs in `windows/mixins/_shared.py` /
  `views/mixins/_shared.py`.
- **17** `# type: ignore` suppressions in `app/`: 7× the necessary `TrMixin`
  `[misc]` (keep), the documented keep-gaps (§8.7 A/C/D/E), and 3 un-audited
  additions (§8.7 G). Full inventory in §8.7 / §8.9.
- `tests/` carries **39** suppressions outside the mypy gate (see §8.7.1).

### Tech-debt markers

**17** real `TODO`/`FIXME`/`HACK` code markers (the 3 `RESTRUCTURING.md`
doc-comment hits are excluded); file:line catalogue with intent is in **§8.6**.
The 4× "let user configure window launch state and size" notes are one tracked
issue (#3).

### Test-coverage gaps (leaf layers largely untested)

Direct unit tests exist for `models/`, `controllers/`, `sort/`, `utils/steam/*`,
`utils/github/`, `views/`, `windows/`, `net/`, most of `core/` (dict_utils,
obfuscate_message, launch_command_parser, window_launch_state, event_bus, schema,
update_check, win_find_steam, app_info), `io/`, `mods/`, `services/`
(mod_path, path_autodetect, window_manager, instance, import_export), and
`git/git_worker`. **Still no dedicated tests** for `ui/widgets/`, remaining
`core/*`, `git/` repo ops, most of `cli/` (only `cli/translate` is covered), and
the fixers/IO builders — the purest logic and the highest-ROI coverage targets.

## 2. Recommendations (prioritized)

### P0 — Enforce the documented leaf-layer boundary

- [x] **Leaf-layer boundary enforced.** `check_layer_violations.py` forbids
      `services/` + `utils/*` and `models/` from importing
      `views`/`controllers`/`windows`. Any _new_ leaf→UI/orchestration import
      fails `just layer-check`.
  - All **12/12** seeded violations resolved: 6 by relocating `views/dialogue` →
    `app/ui/dialogue` (the thin UI bridge), 4 by retyping against leaf-defined
    Protocols (`MetadataProvider`, `InstanceControllerProtocol`,
    `AuxMetadataControllerProtocol`, `RunnerPanelProtocol`), 2 by dependency
    injection in `InstanceService`. No seeded violations remain.

### P1 — Decompose mega-modules

- [x] **Split `windows/base_mods_panel.py` (1191 → 48 LOC)** into `UIBaseMixin`,
      `TableMixin`, `ModRowsMixin`, `SelectionMixin`, `ButtonsMixin`,
      `ColumnsMixin` in `app/windows/mixins/`.
  - **PySide6:** mixins must remain plain Python classes — a `QObject` base
    creates a C++ double-init diamond-inheritance segfault with `QWidget`.
  - **i18n:** these mixins are registered in `QOBJECT_CLASSES` of
    `check_i18n_extraction.py` so their `self.tr()` stays extractable.
  - **WARNING — keep `TrMixin` stubs as `super()` delegations, never no-ops.**
    `TrMixin` (`app/windows/mixins/_shared.py`) precedes `QWidget` in the MRO; a
    no-op stub shadows the real method → blank panels / `layout already deleted`
    crash. The `# type: ignore[misc]` on those delegations is required and
    intentional.
- [ ] **Split `views/main_content_panel.py` (2701 → 1968 raw) by sub-feature.**
  - **Done:** controller + view handler extraction into
    `app/controllers/handlers/` — `database_upload_handler.py`,
    `github_mods_handler.py`, `git_ops_handler.py`, `database_download_handler.py`,
    `import_export_handler.py`, `steam_handler.py`, `zip_mod_handler.py`.
    `main_content_controller.py` → 165 curated LOC; `MainContent` keeps thin
    delegation stubs so all call sites and EventBus signals stay compatible.
  - **Next:** extract `mod_lists_panel.py`, `settings_panel.py`,
    `github_updates_panel.py` as view modules, paired with new `tests/views/*`
    tests before merging (see §8.1).
- [x] **Consolidate git-related UI duplication** — dedicated `_clone_callback`
      delegating to `GitOpsHandler.do_git_clone`, canonical
      `models.get_cache_session()`, `create_provider()` factory in
      `utils/github/provider.py`, shared `_show_batch_results()`,
      `CORRUPTION_INDICATORS` from `git_notifications`, and the
      `check_deferred_imports.py` ALLOWED set kept in sync.
- [x] **Split `views/mod_list_widget.py` (3011 → ~317)** — mixins under
      `app/views/mixins/` (`ContextMenuMixin`, `DividerMixin`, `ListItemMixin`,
      `ErrorsWarningsMixin`, `ColorsTagsMixin`, shared `_shared.py`). Because the
      mixins are `QObject`-less, translatable strings use
      `QCoreApplication.translate("ModListWidget", ...)` so they stay extractable.
- [x] **Split `core/update_utils.py` (2285)** into pure `core/update_check.py`
      (constants, `parse_version`, asset matching, platform download URL; no Qt /
      no `app.views`) + `core/update_apply.py` (apply/self-update flow).
- [x] **Split `git/git_utils.py` (1859)** into `git/git_operations.py` (~1451,
      pygit2 ops) + `git/git_notifications.py` (215, error handling/UI). Circular
      import eliminated via a `repair_callback: Callable` parameter.

### P2 — Tighten typing & clear debt

- [x] `Any` 613 → 522 first pass, **434 now**; remainder is legitimate
      `dict[str, Any]` / `list[Any]` for heterogeneous data.
- [x] Handler constructors typed (`tr: Callable[..., str]`, etc.).
- [x] `# type: ignore` audit — 59 → **17** (inventory in §8.7).
- [x] 17 TODO/FIXME/HACK markers catalogued in §8.6 (tracked issue #3).
- [x] `core/generic.py` split into `fs_utils`, `text_utils`, `ui_helpers`,
      `game_launch`.

### P3 — Testing & tooling

- [x] **Translation Manager UI + CLI** — GUI tool and headless `app/cli/translate.py`
      (`extract`/`translate`/`validate`/`compile`/`run-all`) share
      `translate_language_batch()` in `core/translation_utils.py`. `.qm` files are
      git-ignored build artifacts compiled via `pyside6-lrelease`; `app.cli.main`
      imports PySide6 and must not run headless, so `CLI` is a `_LazyCommandGroup`
      that imports `build_db` only on demand.
- [x] i18n pass — **477 strings translated, 3 failed** across all 10 locales.
- [x] **Leaf-layer unit tests (~90 added)** — see §1 "Test-coverage gaps" for
      coverage. Remaining targets (need fixtures, higher-risk): rest of `core/*`,
      `cli/`, `git/` repo ops, `mods/db_builder*`, `ui/widgets/*`.
- [x] **Coverage floor** — `just cov-gate`: leaf-layer `--cov-fail-under=45`
      (leaf layers measure ~50.5%), wired into `just ci` after `test-coverage`.
  - **REMINDER (CI):** the floor is **local-only**. Do **not** add
    `--cov-fail-under` to `.github/workflows/pytest.yml` — whole-app `--cov=app`
    is ~38% (< 45) and would fail on every OS. Revisit only when whole-app
    coverage reaches ~75–80%.
- [x] **EventBus signal catalogue** documented in `docs/architecture.md` (grouped
      signal list + payload arity + a convention to keep new signals documented).

## 3. Execution Status

The original plan is essentially executed; remaining work = the unchecked boxes
in §2/§8: `main_content_panel.py` (then `context_menu_mixin.py` + `mods_panel.py`)
sub-feature splits, the last untested leaf modules, and the 3 un-audited
`# type: ignore` suppressions.

## 4. Developer Tooling (`justfile`)

All checks/tests are driven by `just` recipes (see `justfile`):

- `just check` — Windows quality gate: typecheck (mypy) + pyright + jscpd (0% dup)
  + deferred-imports + layer-check + i18n-check. **Keep it green on every change.**
- `just layer-check` — runs `check_layer_violations.py` (P0 leaf-layer guard).
- `just deferred-imports` — circular-import regression guard
  (`check_deferred_imports.py`).
- `just typecheck` / `just pyright` — the P2 typing work is verified here.
- `just ruff` — import sorting/formatting; run after any file move/split.
- `just test` / `just test-coverage` — full suite; `test-coverage` emits
  `--cov=app` XML/HTML.
- `just ci` — `check` + `test-coverage` + `cov-gate` (full local CI simulation).
- `just stats` — re-measures `app/`/`tests/` file + LOC + `locales` counts.
- `just build` — `check` + `i18n-compile` plus the Nuitka onefile packaging step.
- `just i18n-translate` / `i18n-validate` / `i18n-full` — AI translation pipeline
  via the CLI (`translate run-all`; pass flags with `ARGS`).

Unix CI additionally runs `super-lint` (super-linter container: ruff, ruff-format,
jscpd, bash, json, yaml, checkov, gitleaks) via `just check`.

### 4.1 Full recipe index

Every recipe in `justfile` is documented in **`CONTRIBUTING.md`** ("Development
tooling"). The recipes above are the ones contributors need most.

### 4.2 Contributor guardrails (mandatory)

Every change to `app/` or `tests/` must keep `just check` green. Two hard rules
keep the gate from silently rotting between runs:

1. **Run `just check` after any implementation.** Fix every failure it reports.
   A "green" change never run through `just check` is not done. The git hook
   installed by `just install-hooks` runs `just check` automatically on commit.

2. **Avoid `# type: ignore` unless extremely necessary.** It hides a real type
   gap and is easy to add and forget. Prefer a real fix first:
   - Retype against a `Protocol` / `TypedDict` instead of `object` / `Any`
     (e.g. the `_Closeable` Protocol in `app/services/window_manager.py`).
   - Add a thin wrapper (e.g. `assign_event_handler`) or a plain base class
     declaring the cross-mixin surface (e.g. `BaseModsPanelSurface`) so MRO
     resolves methods without `attr-defined` suppression.
   - Only when there is a genuine, no-clean-fix gap (missing third-party stubs
     such as `vdf`/`networkx`, a Qt ctor/MRO quirk, a gitpython descriptor gap)
     is a suppression acceptable — and then pin the **correct** error code
     (e.g. `# type: ignore[misc]`, not a guessed `[return-value]`).
   - Re-run `grep "# type: ignore" app/` after any type-related change so the
     count in §8.7 stays honest (currently **17**). **Re-verify new suppressions
     rather than accumulating them; do not move backwards.**

## 5. Notes / non-goals

- `app/ui/` is a namespace package (`__init__.py` only) plus `ui/dialogue.py`
  and `ui/widgets/` — the dialogue module is the thin UI bridge for leaf layers.
- `app/utils/` holds substantive modules (steam/*, github/*, rentry/*,
  workshop_utils, db_builder_thread) — 5.4k curated LOC across 34 files.
- The `base_mods_panel` (windows/) vs `mods_panel` (views/) naming split is
  intentional: base/shared class vs independent reusable panel.
- jscpd enforces a **0% duplication** threshold. The last clones were
  deduplicated (`_resolve_release_asset()`, `_record_installed_version()` in
  `github_mods_handler.py`; shared `summarize_download_results()` in
  `app/net/http_downloader.py`). All guards (mypy, pyright, deferred-imports,
  layer-check, i18n-check, jscpd) are green; see §7.

## 6. Exclusion Map (derived from `.gitignore`)

> Moved to **`EXCLUSION_MAP.md`** (root) on 2026-09-23. Paths treated as
> excluded (not counted in LOC, not committed, not scanned); "Present" = exists
> on disk and is excluded right now. See that file for the full top-level and
> per-rule `.gitignore` breakdown.

## 7. Last Verification Run (2026-09-13)

Windows `just check` fully green: deferred-imports, layer-check, i18n-check,
mypy (365 files), pyright (0 errors/warnings/informations), jscpd (0 clones,
337 files), ruff check + format clean (416 files); pytest **1492 collected →
1478 passed, 14 skipped, 0 failed** (~39 s). Not run: `super-lint` (Unix),
`build` (Nuitka packaging). `cov-gate` is wired but **local-only** — do not add
`--cov-fail-under` to CI (see §2 P3 REMINDER).

## 8. Improvement & Refactoring Suggestions

Priorities follow the P0–P3 scheme used above.

### 8.1 Highest-ROI remaining splits (mega-modules)

- [x] `core/update_utils.py` (2285) — **split** into `update_check.py` (pure) +
      `update_apply.py` (self-update); retired the last `views` import from a
      `core/` module holding pure check logic.
- [ ] **`views/main_content_panel.py` (1968 raw / 1643 curated)** — finish the
      sub-feature split from §2 P1 (`mod_lists_panel.py`, `settings_panel.py`,
      `github_updates_panel.py`). Risk: high without `tests/views/*` coverage;
      pair with tests before merging.
- [ ] **`views/mixins/context_menu_mixin.py` (1648 raw / 1417 curated)** and
      **`views/mods_panel.py` (1703 raw / 1379 curated)** — natural next targets
      after `main_content_panel.py`. Break the mixin into per-context helpers
      (item menu, divider menu, "find translations"). Pair with `tests/views/*`.

### 8.2 Dead / stray artifacts to remove

- [x] `app/views/mod_list_widget_mixins/` — **removed** (held only a `__pycache__/`).

### 8.3 Typing & debt (P2 follow-up)

- [ ] **Introduce a `SteamworksInstruction` TypedDict/Protocol** and retype the
      instruction tuples in `steam_handler.py`, `main_content_panel.py`,
      `steamworks/wrapper.py`. Cuts the remaining `Any` from `list[Any]` and
      gives real checking; guard with `just typecheck` + `just pyright`.
- The `# type: ignore` count is **17** (was 12 @ 2026-07-17; 59 before the
  audit) — three un-audited suppressions appeared post-inventory (§8.7 G).
  Treat the §8.7 G / §8.9 **actionable** list first.
- [x] `TrMixin` base class (plain, non-Protocol) — `windows/mixins/`
      `attr-defined` suppressions 37 → 17 (the remaining are sibling-mixin MRO
      calls, out of scope).
- [x] `HandlerViewProtocol` for the handler `view` param — removed 4
      `# type: ignore[attr-defined]`.
- [x] 17 TODO/FIXME/HACK markers tracked — catalogue in §8.6 (issue #3 for the
      4× window-launch-state notes).

### 8.4 Testing & tooling (P3 follow-up)

- [x] `just cov-gate` wired (leaf `--cov-fail-under=45`, into `just ci`).
- [x] EventBus signal catalogue documented in `docs/architecture.md`.
- Remaining untested leaf modules (high ROI, mostly pure): rest of `core/*`,
  `git/` repo ops, `ui/widgets/*`, rest of `cli/`.
  (`cli/translate`, `mods/db_builder`, `services/*` (instance, import_export,
  window_manager), and `core` update_check/win_find_steam/app_info now have
  dedicated tests.)

### 8.5 Docs / process

- [x] `scripts/stats.py` restored and `just stats` working (file/LOC +
      `locales/*.ts` + largest-file output); §0/§1 counts synced from it.
- [x] `.ruff_cache/` promoted to the root `.gitignore` (see `EXCLUSION_MAP.md`).

### 8.6 TODO / debt marker catalogue

Authoritative list of the **17** real `# TODO` / `# FIXME` / `# HACK` code
markers in `app/` (re-verified 2026-09-23). Excludes the 3 doc-comment
references to `RESTRUCTURING.md` (in `git/git_operations.py`, `git/git_utils.py`,
`git/git_notifications.py`). Markers consolidated into a tracked issue are noted.

- **Windows panels (4× "window launch state/size", tracked as issue #3)**
  - `app/windows/mixins/ui_mixin.py:116`, `app/windows/missing_mods_panel.py:100`,
    `app/windows/missing_mod_properties_panel.py:81`,
    `app/windows/duplicate_mods_panel.py:58` — `TODO(#3)`: let user configure
    window launch state and size (from settings controller).

- **Views**
  - `app/views/main_content_panel.py:453` + `:513` — `TODO`: key-repeat
    graphical bug — holding a key inserts empty items too quickly
    (`__handle_active_mod_key_press` / `__handle_inactive_mod_key_press`).
  - `app/views/mod_info_panel.py:354` — `TODO`: replace the notes `QTextEdit`
    with a markdown + clickable-hyperlink custom editor, collapsible.
  - `app/views/acf_log_panel.py:166` — `TODO;`: find a better refresh-on-
    metadata-update than a manual refresh.
  - `app/views/mixins/errors_warnings_mixin.py:300` — `TODO`: check if
    `toggle_warning` can add a mod to the ignore list.

- **Controllers**
  - `app/controllers/sort_controller.py:43` — `TODO(debt)`: `do_topo_sort` /
    `do_alphabetical_sort` both re-derive sort state (dedupe).
  - `app/controllers/main_window_controller.py:168` — `TODO`: fix `@Slot()`
    mypy errors once PYSIDE-2942 is fixed (decorator currently commented out).

- **Models**
  - `app/models/metadata/metadata_structure.py:712` — `TODO`: type the
    `ModMetadata` keys with a `TypedDict` someday.

- **Utils / Steam + infra**
  - `app/utils/log_setup.py:35` — `TODO(debt)`: make `session_history`
    configurable via settings.
  - `app/utils/steam/workshop_utils.py:1` — `TODO(debt)`:
    `check_if_pfids_blacklisted` / `import_steamcmd_acf_data` use GUI
    (should be headless-friendly).
  - `app/utils/steam/db_builder_thread.py:112` — `TODO`: make this warning
    visible to the user.
  - `app/utils/steam/steamworks/wrapper.py:206` — `TODO`: rework for proper
    static type checking (Steamworks bridge).

- **Rule editor**
  - `app/windows/rule_editor_panel.py:953` — `TODO`: leaving the case-
    insensitive path as-is for now, in case case-sensitivity matters.

### 8.7 `# type: ignore` audit (re-scanned 2026-09-23: **17** in `app/`)

Every suppression is catalogued below by *why* it exists, with an actionable
task where one is cheap and safe. **(keep)** = genuine typing gap, no clean fix.

**Current `app/` inventory (17):**

- **A. Missing third-party stubs — 2 (keep)**
  - `app/core/fs_utils.py:18` — `import vdf` (no type stubs).
  - `app/sort/topo_sort.py:72` — `nx.DiGraph(...)` (networkx ships no stubs).
- **C. gitpython typing gap — 1 (keep, optional task)** —
  `app/controllers/handlers/database_upload_handler.py:622`
  (`repo.branches.local.get("main")` untyped). Optional: wrap in a typed
  `get_local_branch(repo, name)` helper in `app/git/git_operations.py`.
- **D. Qt `resizeEvent` cast — 1 (keep)** —
  `app/views/filter_panel.py:653` (`super().resizeEvent(event)`; `cast` would
  only relocate it).
- **E. Qt constructor / MRO casts — 2 (keep; runtime-correct)**
  - `app/windows/mixins/ui_mixin.py:175` — `QKeyEvent(event)` ctor.
  - `app/windows/mixins/ui_mixin.py:182` — `super().eventFilter(...)` MRO quirk.
- **TrMixin `[misc]` — 7 (keep)** — `app/windows/mixins/_shared.py:35,38,41,44,47,50,53`
  (`super()` delegations; the no-op alternative caused the documented blank-UI /
  `layout already deleted` crash — §2 P1).
- **G. Post-inventory additions — 3 (actionable first)** —
  `app/net/privatebin.py:44,48` (`[arg-type]` on the secretbox builder;
  wrap in a typed `build_secretbox(...)` helper), `app/git/git_operations.py:398`
  (`[attr-defined]`, `repo._has_hanging_threads = True`; type the pygit2
  surface via Protocol/helper), `app/io/xml.py:9` (`[attr-defined]`,
  `import LXMLTreeBuilderForXML`; re-check `bs4` stubs or add a local `.pyi`).

B (SQLAlchemy `Mapped`), D (method-assign via `assign_event_handler`), and F
(`BaseModsPanelSurface`, 18 `attr-defined`) are **done**; those suppressions
were removed. Re-run `grep "# type: ignore" app/` after any change to keep this
count honest.

### 8.7.1 `# type: ignore` in `tests/` (not in the `app/` gate)

`just typecheck` only checks `app/` (mypy config excludes `tests/`). The
`tests/` count is **39** (re-measured 2026-09-23). Buckets are legitimate and
mostly **stay** — they exercise invalid-input error paths, MagicMock/stub
dynamics, or module injection the production types intentionally forbid:

- **Invalid-input error-path tests (keep)** — `test_translation_helper.py` ×5
  (bad validator args), `sort/test_sort_controller.py:101`
  (`sort_method="nonexistent"`), `utils/test_git_utils.py:79`
  (`parse_git_url(None)`), `utils/test_mod_info.py:148`
  (`_normalize_version(42)`), `views/test_filter_panel.py` ×6
  (`mousePressEvent(None)` etc.).
- **Window/view mock & method-assign dynamics (keep)** —
  `tests/windows/test_github_mods_panel.py` ×11,
  `tests/views/test_main_window_close.py` ×2,
  `tests/views/test_main_content_divider_import.py` ×2,
  `io/test_dds_utility.py:25`, `models/test_mod_list.py:39`,
  `utils/steam/webapi/test_dynamic_query.py` ×4, `views/conftest.py:24`
  (`sys.modules["steamworks"]...` injection).
- **Broad bare ignores (keep, low-ROI)** — `views/test_dialogue.py:70,191,198`;
  tightening would require changing test-call shapes for no behavioral gain.

Re-scan with `grep "# type: ignore" tests/` if a future task widens the mypy
scope to `tests/`.

### 8.8 CI type-check / test fixes (facts that still apply)

> Moved to **`CI_PLATFORM_FACTS.md`** (root) on 2026-09-23 — `steamworks`
> pyright stubs, `lxml` `.text` typing, QtWebEngine Linux env vars,
> `runJavaScript` macOS callback arity.

### 8.9 Eliminate `# type: ignore` where possible (ongoing task)

Per the §4.2 guardrail, the goal is to drive the `app/` count (currently **17**)
toward zero by preferring real fixes over suppressions.

**Actionable next (highest ROI):**

- The three §8.7 G sites (`privatebin.py`, `git_operations.py:398`,
  `io/xml.py:9`).
- The `database_upload_handler.py:622` get-local-branch helper (§8.7 C).
- `SteamworksInstruction` TypedDict (§8.3) — also trims `Any`.
- `tests/` bare-ignore → coded-ignore pinning:
  `tests/views/test_dialogue.py:70,191,198` and
  `tests/test_translation_helper.py:266,291,321,350,384`.
  `tests/utils/steam/webapi/test_dynamic_query.py:22,125,132,163` (type
  `dq.api` as `MagicMock`).

**Explicitly keep** until their libraries/refactors land: `TrMixin` ×7,
the Qt ctor/MRO and `resizeEvent` casts (§8.7 D/E), and the missing-stub cases
(`vdf`, `networkx`).

Do not reintroduce suppressions while doing this work — verify with `just check`.
