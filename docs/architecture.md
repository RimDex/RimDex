# RimDex Architecture

This document describes the intended layering of the `app/` package and the
conventions that keep it coherent. It is enforced by CI guards
(`check_deferred_imports.py`, `check_layer_violations.py`) so the boundaries
below are regression-tested.

## Layers (dependency direction is top-to-bottom only)

```
cli / __main__            entry points; wire everything together
        |
controllers/             orchestration: react to UI events, call services/models, update views
        |
views/  windows/          rendering only: Qt widgets, panels, dialogs (no business logic)
ui/widgets/              shared Qt widget subclasses (AnimationLabel, ImageLabel, divider helpers)
        |
models/                  data/domain types only (Settings, Instance, ModList, FilterState,
        |                 OperationMode, SearchResult, metadata/*). NO imports from
        |                 controllers/ or views/.
        |
services/                I/O & side effects: window manager, instance service, path
        |                 autodetect, import/export, and external adapters.
        |
utils/  core/ io/ net/    leaf helpers: pure functions, stdlib/3rd-party wrappers.
        git/ mods/
```

Rules:

- `models/` must never import from `controllers/` or `views/`/`windows/`. Use the
  `EventBus` (`core/event_bus.py`) for model → UI notifications.
- `views/` and `windows/` render and emit signals; they may import
  `controllers/` for wiring but keep logic in controllers.
- `services/` and `utils/*` are leaf layers: they depend on nothing inside `app`
  except other leaf modules.
- No module-level mutable globals. The previous `utils/globals.py`
  `MAIN_WINDOW`/`SETTINGS` variables are replaced by a single typed
  `AppContext` (`core/app_context.py`), populated explicitly at startup via
  dependency injection (see `AppController`).
- External integrations live under their own subpackages with a `wrapper.py`
  (`steam/`, `github/`, `rentry/`, `todds/`, `platform/`).

## Naming conventions

- Reusable widgets/panels: `views/*.py`.
- Top-level dialogs / secondary windows: `windows/*.py`.
- Suffix consistently: `*_dialog.py`, `*_panel.py`, `*_window.py`.
- Qt widget subclasses shared across the UI: `ui/widgets/*.py`.
- Data/domain types: `models/*.py` (no Qt widgets).

## External adapter convention

Integrations with third-party tools/services live under `utils/` as one
subpackage per integration, each exposing a single `wrapper.py`:

- `utils/steam/*/wrapper.py` (steambrowser, steamcmd, steamfiles, steamworks, webapi)
- `utils/github/wrapper.py`, `utils/rentry/wrapper.py`, `utils/todds/wrapper.py`
- `utils/platform/windows.py` (OS-specific helpers)

HTTP access is centralized in `net/` (`http.py` client, `http_downloader.py`
worker, `http_download_service.py` higher-level service). Keep new
integrrations in this shape: one `wrapper.py` per integration, no business
logic mixed into the adapter layer.

Keeping `models/` free of UI/orchestration imports removes circular dependencies,
makes the domain layer unit-testable without a `QApplication`, and makes the
`EventBus` the single, explicit channel for cross-layer notification.
