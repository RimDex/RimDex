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

## EventBus signal catalogue

`core/event_bus.py` is a `QObject` singleton (`EventBus()`). It is the **only**
cross-layer notification channel: models/services emit, views/windows/controllers
connect. Signals are grouped below by the menu/area that originates or consumes
them. Payloads are noted in parentheses (empty `()` = no payload).

### Menu bar — Mod list

- `do_open_mod_list` ()
- `do_save_mod_list_as` ()
- `do_import_mod_list_from_rentry` ()
- `do_import_mod_list_from_workshop_collection` ()
- `do_import_mod_list_from_save_file` ()
- `do_export_mod_list_to_clipboard` ()
- `do_export_mod_list_to_rentry` ()

### Menu bar — Shortcuts (open directories)

- `do_open_app_directory` ()
- `do_open_settings_directory` ()
- `do_open_rimdex_logs_directory` ()
- `do_open_rimworld_directory` ()
- `do_open_rimworld_config_directory` ()
- `do_open_rimworld_logs_directory` ()
- `do_open_local_mods_directory` ()
- `do_open_steam_mods_directory` ()

### Menu bar — Edit

- `do_rule_editor` ()
- `do_ignore_json_editor` ()
- `reset_warnings_signal` ()
- `reset_mod_colors_signal` ()

### Menu bar — Download

- `do_add_git_mod` ()
- `do_open_github_mods_panel` ()
- `github_version_switch_requested` `(str mod_path, str target_tag)`
- `do_add_zip_mod` ()
- `do_browse_workshop` ()
- `do_check_for_workshop_updates` ()
- `do_steam_verify_game_files` ()

### Menu bar — Instances

- `do_activate_current_instance` `(str)`
- `do_backup_existing_instance` `(str)`
- `do_clone_existing_instance` `(str)`
- `do_create_new_instance` ()
- `do_delete_current_instance` ()
- `do_restore_instance_from_archive` ()

### Menu bar — Textures

- `do_optimize_textures` ()
- `do_delete_dds_textures` ()

### Settings

- `settings_have_changed` ()
- `settings_corrupted` `(dict)` — emitted by Settings on a corrupted persisted
  file; payload is already-translated dialog strings + `use_old_backup` flag. The
  UI layer (not the model) shows the recovery dialog / exits.

### SettingsDialog (database / ACF / SteamCMD actions)

- `do_upload_community_rules_db_to_github` ()
- `do_download_community_rules_db_from_github` ()
- `do_upload_steam_workshop_db_to_github` ()
- `do_download_steam_workshop_db_from_github` ()
- `do_upload_no_version_warning_db_to_github` ()
- `do_download_no_version_warning_db_from_github` ()
- `do_upload_use_this_instead_db_to_github` ()
- `do_download_use_this_instead_db_from_github` ()
- `do_upload_log` `(Path)`
- `do_open_default_editor` `(Path)`
- `do_download_all_mods_via_steamcmd` ()
- `do_download_all_mods_via_steam` ()
- `do_compare_steam_workshop_databases` ()
- `do_merge_steam_workshop_databases` ()
- `do_build_steam_workshop_database` ()
- `do_clear_steamcmd_depot_cache` ()
- `do_import_acf` ()
- `do_export_acf` ()
- `do_delete_acf` ()
- `do_install_steamcmd` ()
- `do_change_mod_coloring_mode` ()

### MainWindow (refresh / game launch / Steamworks / animation)

- `do_button_animation` `(QPushButton)`
- `do_save_button_animation_start` ()
- `do_save_button_animation_stop` ()
- `do_refresh_mods_lists` ()
- `do_clear_active_mods_list` ()
- `do_restore_active_mods_list` ()
- `do_sort_active_mods_list` ()
- `do_save_active_mods_list` ()
- `do_run_game` ()
- `do_steamworks_api_call` `(list)`
- `do_steamcmd_download` `(list)`
- `do_delete_outdated_entries_in_aux_db` ()
- `do_set_all_entries_in_aux_db_as_outdated` ()
- `refresh_started` ()
- `refresh_finished` ()
- `do_metadata_refresh_cache` ()
- `do_check_missing_mod_properties` ()

### Dialogs

- `reset_settings_file` ()

### ModsPanel

- `list_updated_signal` `()` — note: documented arity is `()`; the historical
  `(count, list_type)` payload was removed.
- `filters_changed_in_active_modlist` ()
- `filters_changed_in_inactive_modlist` ()
- `use_this_instead_clicked` ()

### Menu bar — Help

- `do_check_for_application_update` ()

### Loading animation

- `do_threaded_loading_animation` `(str, object, str)`

### Translation

- `do_toggle_translation_status` `(bool)`
- `do_auto_add_translations` ()
- `do_open_translation_manager` ()

> When adding a new cross-layer signal, declare it on `EventBus` and add it here.
> Prefer a typed payload (e.g. a `TypedDict` or dataclass) over a bare `list`/`dict`
> so consumers and this catalogue stay accurate.
