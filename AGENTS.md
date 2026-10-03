# AGENTS.md

## Project Overview

RimDex is a free and open-source multi-platform mod manager and sorter for RimWorld, derived from [RimSort](https://github.com/RimSort/RimSort). It reads RimWorld `About.xml` metadata, sorts mod lists using graph/topological algorithms plus community/user rules databases, and integrates with the Steam Workshop (via SteamworksPy and SteamCMD), Git mods, and optional static metadata databases (`SteamDB`, `Community Rules`).

- **Stack:** Python `==3.12.*` (pinned in `pyproject.toml`), PySide6 6.11 / Qt6 GUI, Nuitka 4.2 packaging, [uv](https://docs.astral.sh/uv/) for deps, [just](https://just.systems/) task runner. Targets Windows, macOS, and Linux — no platform-locked code without a guard.
- **Architecture:** pragmatic MVC under `app/` (`views` = PySide6 widgets, `controllers` = glue/logic with `controllers/handlers/`, `models` = data classes, `services` = reusable operations, `utils` = helpers, `sort` = ordering algorithms, `windows` = top-level dialogs, plus `core/`, `git/`, `net/`, `io/`, `mods/`, `cli/`; `ui/` holds the thin Python/Qt bridge for leaf layers). Mixin modules live in `windows/mixins/` and `views/mixins/`. Tests in `tests/` mirror the `app/` layout.
- **Layout guards** are standalone scripts at the repo root: `check_deferred_imports.py`, `check_layer_violations.py`, `check_i18n_extraction.py` (shared code in `guard_common.py`) — see Traps.
- The restructuring plan and the authoritative debt catalogs (Todo ×17, `# type: ignore` ×17, actionable backlog) live in **`RESTRUCTURING.md`** (root). Points of interest: `RESTRUCTURING.md` §8.6 (Todo), §8.7 (`# type: ignore` inventory), §8.9 (actionable next).

## Setup

- Clone with submodules: `git clone --recurse-submodules https://github.com/RimDex/RimDex`
- If submodules are missing: `git submodule update --init --recursive`
- Prerequisites: git, Python 3.12, [uv](https://docs.astral.sh/uv/), [just](https://just.systems/). Full `just check` also needs Node/npx (jscpd, markdownlint).
- `just dev-setup` — creates the venv, `uv sync --locked --dev --group build`, compiles locales. Do this first (most recipes depend on it).
- `just install-hooks` — installs the pre-commit hook (runs `just check` before every commit; requires `just` on PATH).
- Always use the local venv via `uv run ...` — never activate the venv manually or use a bare `pytest`/`ruff`.

Never run `uv lock --upgrade` (== `just update`) as part of a task — dependency bumps are handled by dependabot.

## Running the App

- `just run` (== `uv run python -m app`)
- Use dev mode so you don't touch real user data: `uv run python -m app --dev` — redirects settings/logs/databases/mod-lists to `dev/` (gitignored) and enables debug logging. Env overrides: `RIMDEX_DEV`, `RIMDEX_DEV_DIR`.

## Testing

- Full suite: `just test` (== `uv run pytest --doctest-modules --no-qt-log -s`)
- Verbose: `just test-verbose`; with coverage: `just test-coverage`
- Single file: `uv run pytest --doctest-modules --no-qt-log tests/views/test_mods_panel_search.py -s`
- Single test: append `-k "name_or_substring"` to the above.
- Never run bare `pytest` — the project's `addopts` manage `--import-mode=importlib`, `pythonpath`, and `testpaths`.
- Qt tests use the `qtbot` fixture (pytest-qt); `qapp`, `mock_app_info`, `fresh_event_bus`, `mock_metadata_controller`, `mock_steamcmd_interface` are defined in `tests/conftest.py`. Autouse fixtures there block real Steam URLs and auto-accept dialogs — tests must never launch real Steam URLs or dialogs.
- Suite baseline (2026-09-13): **1492 collected → 1478 passed, 14 skipped, 0 failed**. Add or update tests for any logic you change. Current suite (2026-10-02): **1622 collected → 1622 passed, 17 skipped, 0 failed**.
- Leaf-coverage floor: `just cov-gate` (`--cov-fail-under=45` over the leaf packages) is **local-only** and inside `just ci`. Do **not** add `--cov-fail-under` to `.github/workflows/pytest.yml` — whole-app `--cov=app` is ~38% and would fail on every OS.

## Code Quality (MUST pass before finishing)

`just check` runs the quality gate. On **Windows** it is `typecheck` + `pyright` + `jscpd` + `ruff` + `ruff-format` + `deferred-imports` + `layer-check` + `i18n-check`; on **Unix** it is `super-lint` (container: ruff, ruff-format, jscpd, bash, json, yaml, markdown, checkov, gitleaks) + `typecheck` + `pyright`. `just fix` auto-fixes ruff check/format, shfmt, and markdownlint.

| Command | Purpose |
| --- | --- |
| `just typecheck` | mypy against `pyproject.toml` |
| `just pyright` | pyright (standard mode) against `pyproject.toml` |
| `just jscpd` | Copy-paste detection — enforced at **0% duplication** (config in `.jscpd.json`). If code repeats, extract a shared helper. |
| `just deferred-imports` | Guard against new function-local `from app…` imports (see Traps) |
| `just layer-check` | Guard: `models/`, `services/`, `utils/*` must not import `views`/`controllers`/`windows` (see Traps) |
| `just i18n-check` | Guard: `self.tr(...)` only on QObject classes; `pyside6-lupdate`-extractable patterns only (see i18n) |
| `just ruff` | Ruff lint check (`ruff check`, no writes) |
| `just ruff-format` | Ruff format check (`ruff format --check`, no writes) |
| `just markdownlint` | Markdown lint check for root `*.md` + `docs/**` (rules in `.markdownlint.json`) |
| `just shfmt` | Shell script format check (Unix only — Windows `autocrlf` checkouts make every `.sh` differ; CI enforces it on Linux) |
| `just fix` | Auto-fix: `ruff-fix` + `ruff-format-fix` + `shfmt-fix` + `markdownlint-fix` |

`just ruff`, `just ruff-format`, `just markdownlint`, and `just shfmt` are **check-only** recipes — they never write. Use `just fix` (or the individual `*-fix` recipes) to apply changes.

Run at minimum `just fix` + `just test` + `just typecheck` + `just pyright` + `just layer-check` + `just i18n-check` (or the full Windows `just check`, then `just test`) and get everything green before declaring a change complete. CI runs ruff, mypy, pyright, jscpd, and pytest on ubuntu/macos/windows.

## Code Style

- Ruff (config in `pyproject.toml`): line-length 88, indent 4, `quote-style = "double"`, isort (`I`) enabled; `E402` and `BLE001` are intentionally ignored project-wide — do not re-enable, and do not add project-wide `# noqa` for other rules.
- Type annotations required on all function/method signatures (mypy enforces `disallow_untyped_defs`, `disallow_untyped_calls`, etc.).
- Use modern Python: PEP 604 unions (`str | None`), built-in generics (`list[str]`), `collections.abc` — avoid importing from `typing`. Never `Optional[str]`, never `from typing import ...`.
- Docstrings: Sphinx reST format (Google-style accepted in tests). Example: `def sync(force: bool) -> None: """Run a full sync.\n\n:param force: Ignore caches.\n"""`
- `sys.platform == "win32"`-only code must be platform-guarded; the codebase targets Windows, macOS, and Linux.
- All user-facing strings must go through Qt translations (see i18n). Log and exception messages stay in English.
- Prefer type-explicit, readable logic over clever one-liners.
- `# type: ignore` count is **17** in `app/` — do **not** add suppressions. Prefer a real fix (a `Protocol` / `TypedDict`, a typed wrapper helper, a plain base class declaring a mixin surface) — see `RESTRUCTURING.md` §4.2/§8.9.

## i18n

- Every user-facing string must use `QCoreApplication.translate("ContextName", "English source string")` — the context is normally the class name (e.g. `"ModsPanel"`, `"InstanceService"`). QObject classes may use `self.tr(...)`; QObject-less classes and mixins must call `QCoreApplication.translate("ClassName", ...)` so `just i18n-check` keeps passing (`check_i18n_extraction.py`).
- After adding/changing translatable strings: run `just i18n-update` (merges into `locales/*.ts`, source language `en_US`) and `just i18n-compile` (regenerates `.qm`).
- **Commit only the `.ts` changes.** `.qm` files are git-ignored build artifacts — never commit them.
- Translation Manager GUI + headless CLI (`app/cli/translate.py`: `extract`/`translate`/`validate`/`compile`/`run-all`) share one batch engine in `core/translation_utils.py`. Convenience recipes: `just i18n-translate`, `just i18n-validate`, `just i18n-full`; `translation_helper.py` covers file-level workflows. 10 locales (de, es, fr, ja, ko, pt-BR, ru, tr, zh-CN, zh-TW).
- Preserve `%s`, `{0}`, `\n`, and HTML placeholders exactly in any translated string you touch.
- Do not change translation text of existing strings unless the English source changed.

## Project Layout

- `app/` — application source (Python package).
- `tests/` — pytest suite mirroring `app/`. Fixtures live in `tests/conftest.py`.
- `locales/` — Qt `.ts` (source) + `.qm` (compiled, gitignored) translation files.
- `themes/` — Qt stylesheet themes and icons.
- `docs/` — Jekyll documentation site source.
- `packaging/` — release packaging.
- `todds/` — texture-optimization binary location (runtime only).
- `libs/`, `submodules/` — vendor/extras, see Boundaries.
- `scripts/` — `stats.py` (LOC/counts for `RESTRUCTURING.md`), `check.py`, `mapping.py`.
- `app/utils/github/` — GitHub provider, models, installer, updater; `app/utils/steam/` — Steam integration (`steam/workshop/`, `steam/steamcmd/`, `steam/steambrowser/`).
- `distribute.py` — release build driver; `rimdex.nuitka-package.config.yml` holds Nuitka config.
- Root reference docs: `RESTRUCTURING.md` (plan + debt catalogs), `EXCLUSION_MAP.md` (`.gitignore` map), `CI_PLATFORM_FACTS.md` (platform CI constraints), `CONTRIBUTING.md` (full `justfile` recipe index), `mapping.md` (generated tree).

## Git / PR Conventions

- Feature-specific PRs only — one PR = one change. Every PR should reference a corresponding issue. Project is issue-tracker managed (see `CONTRIBUTING.md`).
- Do not submit dependency-bump PRs — dependabot and maintainers handle them.
- Tests + all quality checks must pass and the PR should be ready before requesting review; use a draft otherwise.

## RimSort sync tracking

RimDex is a fork of RimSort, so upstream commits must be reviewed rather than merged.
The reference checkout is `D:\Github\RimSort` (branch `main`).

**Sync baseline: `88e9d295`** (2026-10-01, upstream HEAD). Every upstream commit from
`b2fe1c10` (2026-09-02) through `88e9d295` has been individually reviewed and classified
as *ported*, *already present*, or *deferred* below — a 70-commit window. Older history
was covered by the full-tree comparison performed when the fork was analysed. To audit
the next upstream range:

```sh
git -C ../RimSort log --oneline 88e9d295..main
git -C ../RimSort diff --stat 88e9d295..main -- app/ tests/
```

Then advance the baseline to the new HEAD once the range is classified, and record any
new deferral in the table below or in `RESTRUCTURING.md` §8.10.

Classification rule: **dependency bumps and CI/release plumbing are `n/a`** — RimDex
pins its own versions and dependabot owns bumps (see Boundaries). Only `app/` and
`tests/` behaviour needs porting.

### Current deferred / not-applicable items

| Upstream commit | Change | State | Action when relevant |
| --- | --- | --- | --- |
| `88e9d295` | sqlalchemy 2.1.1 bump + `set[str]()`/`cast()` typing in fuzzy search | deferred | RimDex pins `sqlalchemy==2.0.52` (it is also a few bumps behind on `platformdirs` 4.11.7→4.12.0, `networkx` 3.6.1→3.7, `pygit2` 1.20.0→1.20.1, dev `nuitka` 4.2.1→4.2.2 — all dependabot's domain). When the sqlalchemy pin moves to 2.1.x, re-apply the typing casts, or if mypy starts flagging `matching_paths` in `app/views/mods_panel.py`. |
| `c203d5fe` | super-linter 8.7.0; `IGNORE_GITIGNORED_FILES: false` + `"gitignore": true` in `.jscpd.json` | landed (as v9.0.0) | RimDex now runs super-linter `slim-v9.0.0`. Its bundled mypy moved `1.19.1`→`2.3.1` (8.6.0 crashed with `ImportError: cannot import name 'extract_symbol' from 'librt.internal'`), and it dropped the jscpd `--gitignore` flag in favour of the config key. `IGNORE_GITIGNORED_FILES: true` stays — it filters super-linter's file list, which is separate from jscpd. 9.0.0 also bumps shfmt `3.13.0`→`3.14.1` and ruff `0.15.8`→`0.16.8`, which made shellcheck/shfmt lint the `justfile` (just interpolation and a PowerShell one-liner, neither valid bash) and added ruff's `EXE001`. Hence `(^|/)justfile$` in `FILTER_REGEX_EXCLUDE`, and the exec bit on `app/__main__.py`, `distribute.py`, `packaging/optimize_macos_bundle.py`. **Keep all of these in lockstep** when bumping: `.github/workflows/lint.yml`, `justfile` (`superlinter_image` + the recipe's `FILTER_REGEX_EXCLUDE`), `.jscpd.json`. |
| `540987ca` | `Calculating...` locale strings | blocked | Source string is not used in RimDex. If adopted, repair `locales/*.ts` first — they are currently malformed, so `just i18n-update` fails. |
| `f4e5ca9b` | upstream `AGENTS.md` | n/a by design | RimDex has its own; see the divergence note below. |
| `7b07ab07`/`95f6427e` | codeql-action v4.38.1→v4.38.2 | landed | RimDex now pins `v4.38.2` in `.github/workflows/codeql.yml` (both `init` and `analyze`). |
| `8984ba70` | codecov-action v7.1.1 | landed | RimDex now pins v7.1.1 in `.github/workflows/pytest.yml` as `codecov/codecov-action@303a32d # v7.1.1`. Keep the SHA pin — it is the annotated tag's commit, not the tag object. |

### Known divergences from upstream (intentional or structural)

- **Layout.** RimDex was restructured (see `RESTRUCTURING.md` §8.10), so upstream paths
  rarely match. Port by behaviour, not by path. Map the change first, then apply:

  | Upstream (RimSort) | RimDex |
  | --- | --- |
  | `app/utils/update_utils.py` | `app/core/update_apply.py` (+ `update_check.py`) |
  | `app/utils/git_utils.py`, `git_worker.py`, `pygit2_loader.py` | `app/git/` (core logic in `git_operations.py`) |
  | `app/utils/{acf_utils,csv_export_utils,dds_utility,files,json_utils,symlink,xml,zip_extractor}.py` | `app/io/` |
  | `app/utils/{http,http_downloader,privatebin}.py`; `app/services/http_download_service.py` | `app/net/` |
  | `app/utils/{aux_db_utils,db_builder,db_builder_core,file_search,ignore_extensions,ignore_manager,mod_info,mod_utils}.py` | `app/mods/` |
  | `app/utils/globals.py` | replaced by `app/core/app_context.py` (AppContext) |
  | `app/utils/{app_info,constants,dict_utils,event_bus,generic,launch_command_parser,schema,single_instance,system_info,watchdog,win_find_steam,window_launch_state}.py` | `app/core/` |
  | `app/utils/{button_factory,custom_list_widget_item,custom_list_widget_item_metadata,custom_qlabels,gui_info}.py` | `app/ui/widgets/` |
  | `app/windows/base_mods_panel.py` | `app/windows/mixins/*` + `app/views/mixins/*` (plain classes, no QObject — see Traps) |
  | controllers | RimDex adds `app/controllers/handlers/*` per-feature glue (`steam_handler`, `zip_mod_handler`, `git_ops_handler`, `github_mods_handler`, `import_export_handler`, `database_*_handler`) |
  | `app/utils/{steam,github,platform,rentry,todds}/`, `app/services/`, `app/models/`, `app/sort/` | largely unchanged; RimDex adds `app/services/translation_service.py` |
- **`AGENTS.md`.** Upstream's version is a sibling, not a base to overwrite. RimDex adds the
  restructure guards (`check_deferred_imports.py`, `check_layer_violations.py`,
  `check_i18n_extraction.py`), the i18n workflow, and the Definition of Done. When syncing
  upstream convention changes, apply them as a diff and keep every RimDex-only section.
- **`locales/`.** Malformed XML; blocks `just i18n-update` and `just i18n-compile`.
- **Quality gate.** `just check` on Windows omits `super-lint` (Unix/container only), so
  `markdownlint`, `bash`, `json` and `yaml` rules are only enforced in CI.
- **Suppression budget.** `# type: ignore` is documented as 17 in §8.7 but the tree
  actually contains **22** (10 in `app/windows/mixins/_shared.py`, 2 in `privatebin.py`,
  2 in `ui_mixin.py`, 8 singletons). §8.7 is due a re-scan.
- **`just markdownlint` scope.** Now matches upstream `e01c88be`: `.markdownlint-cli2.jsonc`
  globs `docs/**/*.md` *and* `*.md`, and ignores `LICENSE.md`. Before that fix, config
  globs silently overrode the justfile's `"*.md"` argument, so root markdown was never
  linted. If root docs start failing, fix the file — do not narrow the glob.
- **`setup_web_channel_script.js` is a reduced implementation.** Upstream's copy is ~680
  lines and implements page-mode detection, History-API URL sync, hub add-buttons, and a
  full badge re-sync loop; RimDex's is ~190 lines (per-tile badges only). This is the
  single biggest behavioural gap between the trees and the source of the open Workshop-browser
  work. When porting any upstream browser change, diff this file first — upstream substitutions
  use `@var@` tokens (see `build_web_channel_script`), RimDex uses `$var` in `page_scripts.py`.

## Boundaries

- 🚫 **Never** — edit `submodules/` (vendored: SteamworksPy, steamfiles fork) or the prebuilt binaries in `libs/`; submit dep-bump PRs; commit secrets/API keys (name env variables only), `.venv`, `dev/`, `build/`, `dist/`, `version.xml` (generated, gitignored), or `locales/*.qm`.
- ⚠️ **Ask first** — changing public/`__init__.py` API signatures, adding a runtime dependency, editing `distribute.py` or Nuitka config, running a release/build/publish workflow, bumping dependencies, or doing large refactors beyond the task.
- ✅ **Always** — use `uv run ...` for everything, add/update tests for changed logic, run the Definition of Done checks below before declaring done.
- Avoid importing Qt-heavy modules at module scope where it creates cycles/startup cost — see `check_deferred_imports.py` (Traps).
- Do not run `just update`, `just build`, or release workflows as part of normal tasks.

## Definition of Done

1. `just fix` + `just typecheck` + `just pyright` + `just deferred-imports` + `just layer-check` + `just i18n-check` all pass (or full `just check` on Windows).
2. `just test` passes (full suite).
3. The diff contains no unrelated reformatting, comments, or scope creep — no wholesale reformatting, no explanatory comments.
4. New translatable strings have been run through `just i18n-update`; commit the `.ts` changes (`.qm` are gitignored build artifacts).
5. No new `# type: ignore` suppressions in `app/` (count is 17 — see `RESTRUCTURING.md` §8.7). Re-run `grep "# type: ignore" app/` after any type-related change.

## Traps

- **Deferred imports are judged, not banned:** `check_deferred_imports.py` fails on any *new* function-local `import app…` not in its `ALLOWED` set. Genuine circular-import fixes go in `ALLOWED`; start-up hot-path imports may stay deferred. If you add one, you must update `ALLOWED` or CI (`just deferred-imports`) fails.
- **Leaf-layer boundary is enforced:** `models/`, `services/`, and `utils/*` may not import `views`/`controllers`/`windows` (or any UI/orchestration). Fix violations with leaf-defined `Protocol`s or dependency injection — never by importing the UI. `just layer-check` fails on any new violation.
- **Mixins are plain Python classes, not `QObject`s.** `windows/mixins/*` and `views/mixins/*` must not inherit `QObject` (a C++ double-init diamond segfault). Use `QCoreApplication.translate("ClassName", ...)` for strings there.
- **Keep `TrMixin` stubs as `super()` delegations, never no-ops.** `TrMixin` (`app/windows/mixins/_shared.py`) precedes `QWidget` in the MRO; a no-op stub shadows the real method → blank panels / `layout already deleted` crash. The `# type: ignore[misc]` on those delegations is required and intentional.
- **`# type: ignore` is 17 and must not grow.** Prefer a real fix first; a "keep" suppression must be a genuine no-clean-fix gap (missing stubs, a Qt MRO quirk). See `RESTRUCTURING.md` §8.7/§8.9 for the inventory and the actionable list.
- Never reformat code wholesale or add comments explaining what the code does — match surrounding style and only change what your feature touches.
- Don't create new top-level data dirs/files under the repo root; app data goes through `AppInfo` (`app/core/app_info.py`), which tests redirect via `mock_app_info`.
- Keep `docs/` edits and root `*.md` lint-clean (markdownlint) and only touch docs when truly needed.
