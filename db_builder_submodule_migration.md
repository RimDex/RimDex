# Database Builder → Independent, Prebuilt, Wrapper-Launched App: Migration Plan

> Status: **IN PROGRESS** — Stages 1–4 done; Stage 5 applied (2026-07-18).
>
> What's applied so far:
> - Stages 1–3: standalone repo (`RimDex/RimDex-Database-Builder`), Nuitka build + child
>   CI, and the `submodules/DatabaseBuilder` submodule (added to RimDex `.gitmodules`,
>   branch `main`).
> - Stage 4: `app/utils/db_builder/wrapper.py` (`DatabaseBuilderInterface`) implemented
>   and verified launching the child GUI from the source fallback; the `build-db` CLI in
>   the child **fully supports `--include {all_mods,no_local}` + `--mods-file`** (so the
>   wrapper now forwards `--include` and a `--mods-file` when driving `all_mods`);
>   `distribute.py::get_latest_db_builder_release()` + `--skip-db-builder`; `.gitignore`
>   `/db_builder`; `rimdex.nuitka-package.config.yml` bundles `../db_builder`. The
>   "Database Builder (standalone test)" Tools-menu action was removed and the real
>   `Database Builder…` action now launches the child GUI via the wrapper.
> - Stage 5 (done): deleted in-repo F1–F6 (`app/mods/db_builder.py`,
>   `app/mods/db_builder_core.py`, `app/utils/steam/db_builder_thread.py`,
>   `app/controllers/database_builder_controller.py`, `app/views/database_builder_dialog.py`,
>   `app/cli/build_db.py`) and all wiring; removed the 5 DB-Builder-only EventBus signals;
>   removed the `db_builder_include` / `build_steam_database_*` settings; moved the two
>   RimDex `db_builder*` tests into the child repo (`tests/test_orchestrator.py`,
>   `tests/test_thread.py`). RimDex `just check` + full suite green (1344 passed).
> - Post-Stage 5 (2026-07-18): fixed 5 mypy errors + 2 pyright errors + 6 ruff errors
>   in the child repo (`steamworks_query.py` null-guard / `_time()` fix / dynamic-attr
>   suppressions, `tests/test_thread.py` missing import, `core.py` import order,
>   `tests/test_orchestrator.py` unused var). Updated child `Agent.md` (accurate module
>   counts: 21 project modules + 16 vendored `steamworks/` subpackage; added
>   `steamworks_query.py` to architecture table; documented vendored SteamworksPy
>   subpackage). Child `just check` green (pyright 0 errors, ruff clean, mypy clean).
> - Remaining: Stage 6 (real `just build` + per-platform smoke test of the bundled
>   binary), Stage 7 (docs: Agent.md / docs/architecture.md / child README).
>
> **Goal (final, per user):** The Database Builder becomes a **fully independent
> application** that:
> 1. RimDex talks to through a thin **wrapper** (modeled on
>    `app/utils/steam/steamworks/wrapper.py` and `app/utils/todds/wrapper.py`).
> 2. Is **built independently with Nuitka by itself**, with **no RimDex dependency**.
> 3. Ships with RimDex as a **prebuilt binary** — exactly like `todds/todds.exe`
>    (bundled at build time, launched at runtime), so RimDex can be shipped with
>    just the prebuilt Database Builder in future.
> 4. Builds both **locally** (`distribute.py`) and via **GitHub Actions**, on all
>    **3 platforms** (Windows, macOS, Linux), the same way the current build works.
>
> Locked-in decisions from prior turns:
> - Separate GUI **process**, launched via `QProcess`/`subprocess` (not imported).
> - Its own **git repo**, consumed as a **git submodule** (wired like SteamworksPy).
> - **Fully self-contained** — the app *vendors* the small shared pieces it needs
>   (DLC constants, dict-merge, json-dump, Steam WebAPI `DynamicQuery`). Zero `app.*`.

---

## 1. Two reference patterns we're combining

RimDex already ships and drives two external tools; the DB Builder becomes a third,
combining the best of both:

### A. `todds` — the **prebuilt-binary bundling** model (what we copy for shipping)
- Prebuilt binary lives in a top-level dir `todds/` (`todds.exe` on Windows, `todds`
  elsewhere). `/todds` is **git-ignored** (`.gitignore:55`).
- Fetched at build time by `distribute.py::get_latest_todds_release()` (downloads the
  platform-specific release zip from GitHub, extracts to `todds/`, sets +x).
- Bundled into the Nuitka build via `rimdex.nuitka-package.config.yml`:
  ```yaml
  dlls:
    - from_filenames:
        relative_path: "../todds"
        prefixes: ["todds"]
        executable: "yes"
      dest_path: "todds"
  ```
- Located & launched at runtime by the **wrapper** `app/utils/todds/wrapper.py`
  (`ToddsInterface`): picks the exe name per-OS, resolves
  `AppInfo().application_folder / "todds" / <exe>`, checks existence, and runs it
  through a `RunnerPanel` (QProcess), streaming progress. Shows a helpful error if
  missing.

### B. `steamworks/wrapper.py` — the **wrapper module + source/compiled guard** model
- A dedicated `app/utils/.../wrapper.py` that is RimDex's single point of contact
  with the external component.
- Uses `if "__compiled__" not in globals():` to branch **running-from-source** vs.
  **Nuitka-compiled** for path resolution.

**DB Builder = a `todds`-style prebuilt binary, driven by a `steamworks`-style
wrapper module.** RimDex never imports the DB Builder's Python; it launches the
bundled binary and talks over the process boundary.

---

## 2. The wrapper (RimDex side)

New module: **`app/utils/db_builder/wrapper.py`** → class `DatabaseBuilderInterface`.

Responsibilities (mirrors `ToddsInterface`):
- **Locate** the prebuilt binary:
  - Compiled: `AppInfo().application_folder / "db_builder" / <exe>`
    (`RimDexDatabaseBuilder.exe` on Windows, `RimDexDatabaseBuilder` otherwise).
  - From source (dev): fall back to launching the submodule entry point
    (`uv run python -m rimdex_db_builder ...` inside `submodules/DatabaseBuilder`),
    guarded by `if "__compiled__" not in globals():` like the steamworks wrapper.
- **Build argv** for the requested action (see §4 contract).
- **Launch** via `RunnerPanel` (QProcess) — reuse the existing runner so progress
  streams into a RimDex window exactly like todds; or fire-and-forget the child's own
  GUI when the user just wants the standalone tool.
- **Consume results**: exit code + the written database JSON on disk; optionally parse
  a machine-readable line (e.g. a `--pfids-out <file>` list) for the download flows.
- **Missing-binary UX**: same friendly error/dev-guide message pattern todds uses.

This wrapper **replaces** the current in-process `DatabaseBuilder`/
`DatabaseBuilderController`/dialog wiring in RimDex.

---

## 3. The standalone app (new repo)

New repo (name in §8 Q1): **`RimDex/RimDexDatabaseBuilder`**, cloned to
`submodules/DatabaseBuilder`, self-contained, Nuitka-buildable on its own.

```
submodules/DatabaseBuilder/                 # own git repo, own CI
├── .github/workflows/build.yml             # builds the app on win/mac/linux, publishes releases
├── .gitmodules                             # only if it nests SteamworksPy (§8 Q2 option B)
├── LICENSE
├── README.md
├── pyproject.toml                          # deps: PySide6, requests, loguru, click; own [project.scripts]
├── uv.lock
├── distribute.py                           # its OWN Nuitka build script (mirrors RimDex's, minus RimDex bits)
├── db_builder.nuitka-package.config.yml    # its own packaging config
├── rimdex_db_builder/
│   ├── __init__.py
│   ├── __main__.py                         # `python -m rimdex_db_builder` (GUI default + subcommands)
│   ├── app.py                              # QApplication bootstrap
│   ├── cli.py                              # headless build-db / compare / merge / query-pfids
│   ├── orchestrator.py                     # was app/mods/db_builder.py (F3)
│   ├── controller.py                       # was database_builder_controller.py (F4)
│   ├── dialog.py                           # was database_builder_dialog.py (F5)
│   ├── thread.py                           # was db_builder_thread.py (F2)
│   ├── core.py                             # was db_builder_core.py (F1)
│   ├── config.py                           # DbBuilderConfig (replaces Settings + AppInfo)
│   ├── constants.py                        # vendored DB_BUILDER_* + RIMWORLD_DLC_METADATA
│   ├── steamworks_query.py                 # native DLC deps via vendored SteamworksPy + libs/
│   ├── steam/webapi.py                     # vendored DynamicQuery (+ its webapi deps)
│   ├── steamworks/                         # vendored SteamworksPy pure-Python package (16 files)
│   │   ├── __init__.py                     # self-registers as top-level "steamworks" in sys.modules
│   │   ├── enums.py, exceptions.py, methods.py, structs.py, util.py
│   │   └── interfaces/                     # apps, friends, input, matchmaking, etc.
│   ├── ui/{dialogue,gui_info,runner_panel}.py   # vendored minimal UI helpers
│   └── _util/{dict_utils,json_utils}.py    # vendored recursively_update_dict / atomic_json_dump
├── libs/                                   # prebuilt Steamworks native libs (committed, not a submodule)
│   ├── SteamworksPy64.dll / SteamworksPy.dylib / ...
│   └── steam_api64.dll / libsteam_api.so / ...
└── tests/                                  # moved + new tests, zero RimDex deps
```

**Files that move out of RimDex (deleted here, recreated there):**
`app/mods/db_builder_core.py` (F1), `app/utils/steam/db_builder_thread.py` (F2),
`app/mods/db_builder.py` (F3), `app/controllers/database_builder_controller.py` (F4),
`app/views/database_builder_dialog.py` (F5), `app/cli/build_db.py` (F6).

**Vendored (copied) shared code** — full self-containment:
`DB_BUILDER_PRUNE_EXCEPTIONS`/`DB_BUILDER_RECURSE_EXCEPTIONS`/`RIMWORLD_DLC_METADATA`
(from `app/core/constants.py`), `recursively_update_dict` (`app/core/dict_utils.py`),
`atomic_json_dump` (`app/io/json_utils.py`), `DynamicQuery` + webapi deps
(`app/utils/steam/webapi/wrapper.py`), and minimal own versions of `app/ui/dialogue.py`,
`app/ui/widgets/gui_info.py`, `app/windows/runner_panel.py`.

> **`DynamicQuery`/DLC caveat (decide §8 Q2):** `DynamicQuery` transitively uses
> `app.utils.steam.availability` → `steamworks.wrapper` (needs the SteamworksPy
> native lib) only for `get_appid_deps` (DLC dependency queries). Option **(A)**:
> vendor WebAPI-only, make `--dlc-data` degrade/no-op (child needs no native lib —
> simplest, keeps the child's build trivial). Option **(B)**: child nests its **own**
> SteamworksPy submodule + builds the native lib in its own `distribute.py` for full
> `--dlc-data` parity (heavier build).
>
> **Implemented approach (hybrid):** The child vendors the SteamworksPy pure-Python
> package (`rimdex_db_builder/steamworks/`, 16 files copied from `submodules/SteamworksPy`)
> and prebuilt native libs (`libs/`, identical copies from the main repo's
> `submodules/SteamworksPy`). This gives full DLC query capability without requiring
> a SteamworksPy submodule or native build in the child. The trade-off: if the main
> repo's `submodules/SteamworksPy` native libs are updated, the child's `libs/` must
> be manually updated too (independent copies).

---

## 4. Runtime contract (wrapper ⇄ standalone)

Since they're separate processes, define an explicit CLI/IO contract (extends the
existing `build_db` CLI conventions in F6):

**RimDex → child (argv / env):**
- Default (no subcommand): launch the **standalone GUI**.
- `build-db --output <path> [--include {all_mods,no_local}] [--dlc-data/--no-dlc-data] [--update/--overwrite]`
- `--api-key <key>` or env `RIMDEX_STEAM_API_KEY` (already F6's convention).
- `--mods-file <path>`: JSON RimDex writes with the local mod metadata needed for
  `all_mods` mode (replaces reading `MetadataController.mods_metadata` in-process).
  Flat schema: `[{published_file_id, package_id, name, authors[], supported_versions[],
  steam_app_id, db_builder_no_name, mod_type}]` (only fields F2 reads).
- `--storage-dir <path>`: default dir for file dialogs / db read-write (replaces
  `AppInfo().app_storage_folder`).
- `query-pfids --appid 294100 --pfids-out <file>`: for the "download entire workshop"
  flows — child queries PublishedFileIDs and writes them to `<file>`; **RimDex** then
  drives SteamCMD/Steam downloads (keeps download integration in RimDex — §8 Q4).

**child → RimDex:**
- Exit code `0`/non-zero (already F6's pattern).
- The written **JSON database** / **pfids file** on disk.
- **stdout/stderr** progress lines → streamed into a RimDex `RunnerPanel` via
  `QProcess.readyReadStandardOutput` (todds-style), or the child shows its own window.

**EventBus (5 signals):** the F4→F3 seam is now internal to the child (one process) →
plain method calls. The 5 signals are **removed** from RimDex's
`app/core/event_bus.py` and their wiring deleted from `main_content_panel.py`.

---

## 5. Building the child **independently** with Nuitka (todds-parity)

The child owns a **complete, standalone build** — no RimDex involvement:

- `submodules/DatabaseBuilder/distribute.py`: its own Nuitka invocation (mirrors
  RimDex's `freeze_application`, minus RimDex-specific bits). Sets its own
  `PYTHONPATH` only if it nests SteamworksPy (§8 Q2-B).
- `db_builder.nuitka-package.config.yml`: bundles PySide6 + its own data.
- Output binary name: `RimDexDatabaseBuilder[.exe]` (+ `.app` on macOS).
- Local build: `just build` inside the submodule (or `uv run python distribute.py`).

### Shipping it inside RimDex (todds model)
1. **Fetch/produce the prebuilt binary** into a top-level `db_builder/` dir:
   - **CI (recommended):** RimDex's build downloads the child's latest **GitHub
     release** for the current platform (a new `get_latest_db_builder_release()` in
     RimDex's `distribute.py`, copy-pasted from `get_latest_todds_release()` with the
     child's repo + asset-name scheme). This is what makes "ship RimDex with just the
     prebuilt DB Builder" work.
   - **Local dev alt:** build the submodule locally and copy its binary into
     `db_builder/`.
2. **Git-ignore** `/db_builder` (add to `.gitignore`, next to `/todds`).
3. **Bundle** via `rimdex.nuitka-package.config.yml` — add a `dlls` entry cloned from
   the todds one:
   ```yaml
   - from_filenames:
       relative_path: "../db_builder"
       prefixes: ["RimDexDatabaseBuilder", "db_builder"]
       executable: "yes"
     dest_path: "db_builder"
   ```
   (macOS `.app` bundling: mirror how the app dir is included; the child `.app` may
   need a fixup step like `post_build_fixup_macos_steamworks`.)
4. **Runtime resolution:** the wrapper finds
   `AppInfo().application_folder / "db_builder" / <exe>` — exactly the todds path
   shape.

---

## 6. GitHub Actions (all 3 platforms, local parity)

### Child repo CI (`submodules/DatabaseBuilder/.github/workflows/build.yml`)
- Clone RimDex's `build.yml` matrix (macos-intel, macos-arm, ubuntu-22.04,
  ubuntu-24.04, windows-latest), stripped to the child.
- Steps: checkout (recursive if §8 Q2-B) → setup Python/uv → `uv sync` →
  Nuitka-Action build → upload artifact **and publish a release asset** named per the
  platform scheme RimDex's fetch step expects
  (e.g. `RimDexDatabaseBuilder_Windows_x86_64_<tag>.zip`, mirroring todds' naming).

### RimDex CI (`.github/workflows/build.yml`) — minimal additions
- Existing `submodules: recursive` checkout already pulls the new submodule. ✔
- The existing "Build Actions" step runs `distribute.py --skip-build`, which already
  calls `get_latest_todds_release()`; add `get_latest_db_builder_release()` alongside
  it so `db_builder/` is populated before the Nuitka bundle step.
- Nuitka bundle picks up `db_builder/` from the updated package config. No matrix
  change needed (RimDex just consumes the prebuilt child binary).
- **Version-change path detection:** `semantic-version` `change_path` currently
  `"app libs submodules themes"` already includes `submodules`. ✔

### Local parity
- `just submodules-init` (already `git submodule update --init --recursive`) pulls it.
- `distribute.py` change above makes `just build` fetch+bundle the child locally too.

---

## 7. Exact RimDex edits

**Delete:** F1–F6 and their consumers/wiring:
- `app/mods/db_builder.py`, `app/mods/db_builder_core.py`,
  `app/utils/steam/db_builder_thread.py`,
  `app/controllers/database_builder_controller.py`,
  `app/views/database_builder_dialog.py`, `app/cli/build_db.py`.
- `app/cli/main.py`: remove `build-db` registration.
- `app/core/event_bus.py`: remove the 5 `do_*_steam_workshop_database*` /
  `do_download_all_mods_via_*` signals.
- `app/views/main_content_panel.py`: remove `self.db_builder = DatabaseBuilder(...)`
  and the 5 `EventBus().…connect(...)` lines.
- `app/controllers/app_controller.py`: remove `initialize_database_builder()` +
  `database_builder_controller` construction & pass-through.
- `app/views/main_window.py`: remove the `database_builder_controller` param + its
  `_window_manager` registration.
- `check_deferred_imports.py`: remove the `app/cli/main.py: from app.cli.build_db …`
  entry.
- Move `tests/mods/test_db_builder.py` + `tests/utils/steam/test_db_builder_thread.py`
  into the child repo.

**Keep:** `AboutXmlMod.db_builder_no_name` model field +
`tests/models/metadata/test_metadata_structure.py` (mod metadata, not the app).

**Add:**
- `app/utils/db_builder/wrapper.py` (`DatabaseBuilderInterface`) — §2. **DONE.**
- Rewire `app/views/menu_bar.py::database_builder_action` → wrapper (via a callback
   from `AppController`/`MainWindow`, current wiring style).
   **DONE** — the real `Database Builder…` action launches the child GUI via the
   wrapper (`MenuBarController._on_launch_standalone_db_builder`). The temporary
   "standalone test" action was removed.
  - Serialize `mods_metadata` → temp `--mods-file` in the wrapper when `all_mods`.
   **DONE** — the child's `build-db` CLI supports `--include`/`--mods-file`
   (see `RimDex-Database-Builder` Agent.md §5); the wrapper forwards both.
- `.gitmodules` stanza (mirrors SteamworksPy):
  ```
  [submodule "DatabaseBuilder"]
      path = submodules/DatabaseBuilder
      url = https://github.com/RimDex/RimDexDatabaseBuilder
      ignore = dirty
      branch = main
  ```
  **DONE.**
- `.gitignore`: add `/db_builder`. **DONE.**
- `distribute.py`: add `get_latest_db_builder_release()` (todds clone) + call it in
  `main()`; add `--skip-db-builder` flag (parity with `--skip-todds`). **DONE.**
- `rimdex.nuitka-package.config.yml`: add the `db_builder/` `dlls` bundle entry. **DONE.**
- `.github/workflows/build.yml`: (only if needed) ensure the fetch runs before Nuitka.

**Guards afterward:** `check_layer_violations.py` / `check_deferred_imports.py` shrink
(feature gone). No new allow-entries. i18n: the 5 strings leave RimDex's catalogue and
become the child's own (§8 Q5).

---

## 8. Open decisions (before Stage 1)

1. **Repo/package/binary name + branch.** **RESOLVED:** repo `RimDex/RimDexDatabaseBuilder`,
   submodule path `submodules/DatabaseBuilder`, package `rimdex_db_builder`, binary
   `RimDexDatabaseBuilder` (Nuitka onefile may also emit `rimdex_db_builder[.exe/.bin]`;
   the wrapper accepts both), ship dir `db_builder/`, branch `main`.
2. **DLC data / `DynamicQuery`.** **RESOLVED → (A):** WebAPI-only child, no SteamworksPy;
   `--dlc-data` degrades gracefully (warns, proceeds without DLC deps).
3. **How RimDex obtains the prebuilt child in CI.** (a) download the child's GitHub
   **release asset** (todds-exact, best for "ship with prebuilt"); or (b) build the
   child in the same workflow and copy the artifact. (a) recommended.
4. **Workshop downloads.** Recommended: child only builds/merges/compares + emits
   pfids (`query-pfids`); **RimDex** owns SteamCMD/Steam downloading. Confirm.
5. **i18n ownership.** Child owns its own translations; the 5 strings leave RimDex.
   Confirm.
6. **Progress UX.** Stream child stdout into a RimDex `RunnerPanel` (todds-style), or
   let the child show its own GUI window, or both (per action)?
7. **Git history.** Preserve F1–F6 history into the new repo (`git filter-repo`/subtree)
   or fresh copy with attribution?
8. **macOS packaging.** Ship the child as a nested `.app`, or a plain executable inside
   `db_builder/`? (Affects the Nuitka bundle + any macOS fixup step.)

---

## 9. Staged execution plan (each stage keeps RimDex `just check`/`just test` green)

- **Stage 0 — Baseline & decisions.** Record `just check`/`just test`; resolve §8.
- **Stage 1 — Stand up the standalone repo.** Scaffold §3; copy F1–F6; vendor shared
  code (rewrite all `app.*` imports to local); replace EventBus with internal calls;
  add `__main__`/`app.py`/`cli.py` and the §4 contract; own tests. Must run alone:
  `python -m rimdex_db_builder` (GUI) and `… build-db --output x.json` (headless).
- **Stage 2 — Independent Nuitka build + child CI.** Child `distribute.py` +
  package config + `.github/workflows/build.yml` producing per-platform release
  assets. Verify a green 3-platform build in the child repo.
- **Stage 3 — Add submodule to RimDex.** `git submodule add` + `.gitmodules` stanza.
  **DONE** (submodule `DatabaseBuilder`, branch `main`).
- **Stage 4 — Wrapper + fetch/bundle.** `app/utils/db_builder/wrapper.py`;
  `distribute.py::get_latest_db_builder_release()`; `.gitignore /db_builder`; Nuitka
  config bundle entry; rewire menu to the wrapper; `--mods-file` serialization.
   **DONE (2026-07-18):** wrapper implemented + verified launching the child
   GUI from source; fetch func + `--skip-db-builder`; `.gitignore`; Nuitka bundle entry;
   the real `Database Builder…` menu action launches the child GUI via the wrapper
   (replacing the in-repo dialog); the wrapper forwards `--include`/`--mods-file`
   now that the child supports `all_mods`.
- **Stage 5 — Delete in-RimDex feature.** Remove F1–F6 + all wiring (§7); shrink
   guards; RimDex green. **DONE (2026-07-18)** — F1–F6 deleted, the 5 DB-Builder-only
   EventBus signals removed, `db_builder_include`/`build_steam_database_*` settings
   removed, the two RimDex `db_builder*` tests moved into the child repo, and
   `app/cli/main.py` build-db registration + the deferred-import guard entry removed.
   RimDex `just check` + full suite green (1344 passed). The child already supported
   `all_mods` (`--include`/`--mods-file`), so the documented Stage-5 blocker was moot.
- **Stage 6 — RimDex build/CI + smoke test.** Real `just build`; confirm the bundled
  `db_builder/<exe>` launches from the built RimDex on each platform; adjust CI.
- **Stage 7 — Docs.** Update `Agent.md` (§0 counts, §5 notes), `docs/architecture.md`
  (drop the 5 EventBus signals; document the wrapper + prebuilt-binary model), and the
  child's `README.md` (standalone + RimDex-launched usage + §4 contract).

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Vendoring `DynamicQuery` drags in SteamworksPy native lib | §8 Q2-A: WebAPI-only child; DLC optional |
| macOS: bundling a second `.app`/binary inside RimDex `.app` | Mirror todds/steamworks macOS handling; add a fixup step; test on both arches |
| Child release asset naming mismatch → RimDex fetch fails silently (like todds' soft-fail) | Pin an exact asset-name scheme; make RimDex fail loudly if missing in CI |
| Version skew between RimDex and bundled child | Pin the submodule commit / release tag; document the pin |
| Two build pipelines to maintain | Keep child's `distribute.py`/CI a thin clone of RimDex's; share nothing at runtime |
| Local dev without a prebuilt binary | Wrapper's source fallback runs `python -m rimdex_db_builder` from `submodules/DatabaseBuilder` (guarded by `"__compiled__"`) |

---

## 11. Effort estimate

- Stage 0: ~0.5 day. Stage 1 (vendoring is the bulk): ~2–3 days.
- Stage 2 (independent Nuitka + 3-platform child CI): ~1.5–2 days.
- Stage 3: ~0.25 day. Stage 4 (wrapper + fetch/bundle): ~1–1.5 days.
- Stage 5 (delete + guards): ~0.5 day. Stage 6 (RimDex build/CI + smoke): ~1–1.5 days.
- Stage 7 (docs): ~0.5 day.

**Total: ~7–10 focused days**, dominated by Stage 1 (self-contained vendoring) and the
two independent Nuitka/CI pipelines (Stages 2 & 6).

---

## 12. Superseded approaches (for the record)

- **v1 (import-based submodule like SteamworksPy):** obsolete — required inverting
  ~11 `app.*` deps to avoid circular imports/layer-guard failures.
- **v2 (separate process, but ship source):** superseded by this v3, which ships a
  **prebuilt Nuitka binary** (todds model) so RimDex can be shipped with just the
  prebuilt Database Builder.


## Important Note


1) if submodules\DatabaseBuilder need some code you will have to edit in D:\Github\RimDex-Database-Builder
2) if any files are edited in D:\Github\RimDex-Database-Builder you will have to commit the changes and push since its a repo
3) for any changes done in D:\Github\RimDex-Database-Builder and reflect in submodules\DatabaseBuilder u will have to delete submodules\DatabaseBuilder and run the below command:-
python distribute.py --skip-build

