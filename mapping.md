# Git Ignore Mapping & Codebase Definitions

## Overview
This document maps all files, folders, patterns, and definitions found in the `.gitignore` configuration along with class/function definitions from the RimDex codebase.

---

## 1. Files & Folders from .gitignore

### Directories/Folders Mentioned:
| Path | Description |
|------|-------------|
| `__pycache__/` | Python bytecode cache |
| `build/` | Build artifacts |
| `dist/` | Distribution files |
| `.pytest_cache/` | pytest test cache |
| `htmlcov/` | HTML coverage reports |
| `junit/` | JUnit XML output |
| `.mypy_cache/` | mypy type checker cache |
| `.venv/` | Python virtual environment |
| `env/` | Environment directory |
| `venv/` | Python virtual environment |
| `ENV/` | Environment directory |
| `Scripts/` | Scripts directory |
| `.idea/` | IntelliJ IDEA project files |
| `.vs/` | Visual Studio project files |
| `.ropeproject/` | Rope editor project |
| `.continue/` | VS Code Continue extension |
| `*.build/` | Nuitka build directories |
| `*.dist/` | Nuitka distribution directories |
| `*.onefile-build/` | Nuitka onefile builds |
| `.tools/` | Development tools directory |
| `MagicMock/` | Test artifacts |
| `/.cocoindex_code/` | CocoIndex Code index |

### File Patterns:
| Pattern | Description |
|---------|-------------|
| `*.py[cod]` | Python source files and bytecode |
| `*$py.class` | Python class files |
| `*.egg-info/` | Python egg info directories |
| `*.egg` | Python egg packages |
| `MANIFEST` | Manifest file |
| `.coverage` | Coverage data |
| `.coverage.*` | Coverage data files |
| `coverage.xml` | Coverage XML report |
| `nosetests.xml` | nose test results |
| `junit.xml` | JUnit test results |
| `.dmypy.json` | dmypy configuration |
| `dmypy.json` | dmypy configuration |
| `.ruff_cache/` | Ruff linter cache |
| `.env` | Environment variables file |
| `version.xml` | Version information (GitHub Actions) |
| `ltex.dictionary*` | LaTeX dictionaries |
| `locales/*.qm` | Compiled Qt translation files |
| `.translation_cache.json` | Translation cache |

### Special Entries:
| Entry | Description |
|-------|-------------|
| `DEBUG` | Debug directory |
| `.DS_Store` | macOS hidden file |
| `/todds` | Todds directory (relative path) |
| `steamworks_sdk_*.zip` | Steam SDK packages |
| `!./vscode/launch.json` | Exclude launch.json from ignore |
| `!./vscode/settings.json` | Exclude settings.json from ignore |

---

## 2. Project Directory Structure (excluding .gitignore patterns)

### Root Level Files:
```
.gitignore
.gitmodules
.jscpd.json
.markdownlint-cli2.jsonc
.prettierignore
.python-version
LICENSE.md
README.md
rimdex.nuitka-package.config.yml
setup_web_channel_script.js
steam_appid.txt
justfile
pyproject.toml
uv.lock
distribute.py
guard_common.py
check_deferred_imports.py
check_i18n_extraction.py
check_layer_violations.py
translation_helper.py
update.bat
update.sh
```

### Root Level Directories:
```
app/                    # Main application code
docs/                   # Documentation
libs/                   # Precompiled Steam API libraries
locales/                # Translation source files (.ts)
packaging/              # Distribution packaging scripts
scripts/                # Utility scripts
stubs/                  # Type stub files
submodules/             # Git submodules (steamfiles, SteamworksPy)
tests/                  # Test suite
themes/                 # UI themes
todds/                  # Todds application (external)
.github/                # GitHub workflows and templates
.githooks/              # Git hooks
```

### Application Modules (`app/`):
```
app/
├── __init__.py
├── __main__.py
├── cli/
│   ├── __init__.py
│   ├── main.py
│   ├── build_db.py
│   └── translate.py
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py
│   ├── database_builder_controller.py
│   ├── file_search_controller.py
│   ├── instance_controller.py
│   ├── language_controller.py
│   ├── main_content_controller.py
│   ├── main_window_controller.py
│   ├── menu_bar_controller.py
│   ├── metadata_controller.py
│   ├── metadata_db_controller.py
│   ├── mods_panel_controller.py
│   ├── settings_controller.py
│   ├── sort_controller.py
│   ├── theme_controller.py
│   ├── todds_controller.py
│   ├── translation_controller.py
│   ├── troubleshooting_controller.py
│   ├── database/             # Empty directory (no source files)
│   ├── git_ops/              # Empty directory (no source files)
│   ├── github_install/       # Empty directory (no source files)
│   ├── github_update/        # Empty directory (no source files)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── database_download_handler.py
│   │   ├── database_upload_handler.py
│   │   ├── git_ops_handler.py
│   │   ├── github_mods_handler.py
│   │   ├── import_export_handler.py
│   │   ├── steam_handler.py
│   │   └── zip_mod_handler.py
│   └── settings_tabs/
│       ├── __init__.py
│       ├── advanced_tab_controller.py
│       ├── appearance_tab_controller.py
│       ├── base_tab_controller.py
│       ├── databases_tab_controller.py
│       ├── external_tools_tab_controller.py
│       ├── game_launch_tab_controller.py
│       ├── internal_tools_tab_controller.py
│       ├── locations_tab_controller.py
│       └── sorting_tab_controller.py
├── core/
│   ├── __init__.py
│   ├── app_context.py
│   ├── app_info.py
│   ├── constants.py
│   ├── dict_utils.py
│   ├── event_bus.py
│   ├── fs_utils.py
│   ├── game_launch.py
│   ├── generic.py
│   ├── launch_command_parser.py
│   ├── obfuscate_message.py
│   ├── schema.py
│   ├── single_instance.py
│   ├── system_info.py
│   ├── text_utils.py
│   ├── translation_utils.py
│   ├── translation_workers.py
│   ├── ui_helpers.py
│   ├── update_apply.py
│   ├── update_check.py
│   ├── update_utils.py
│   ├── watchdog.py
│   ├── win_find_steam.py
│   └── window_launch_state.py
├── git/
│   ├── __init__.py
│   ├── git_notifications.py
│   ├── git_operations.py
│   ├── git_utils.py
│   ├── git_worker.py
│   └── pygit2_loader.py
├── io/
│   ├── __init__.py
│   ├── acf_utils.py
│   ├── csv_export_utils.py
│   ├── dds_utility.py
│   ├── files.py
│   ├── json_utils.py
│   ├── symlink.py
│   ├── xml.py
│   └── zip_extractor.py
├── models/
│   ├── __init__.py
│   ├── filter_state.py
│   ├── instance.py
│   ├── mod_list.py
│   ├── operation_mode.py
│   ├── search_result.py
│   ├── settings.py
│   ├── translation.py
│   └── metadata/
│       ├── __init__.py
│       ├── metadata_db.py
│       ├── metadata_factory.py
│       ├── metadata_mediator.py
│       └── metadata_structure.py
├── mods/
│   ├── __init__.py
│   ├── aux_db_utils.py
│   ├── db_builder.py
│   ├── db_builder_core.py
│   ├── file_search.py
│   ├── ignore_extensions.py
│   ├── ignore_manager.py
│   ├── mod_info.py
│   └── mod_utils.py
├── net/
│   ├── __init__.py
│   ├── http.py
│   ├── http_download_service.py
│   └── http_downloader.py
├── services/
│   ├── __init__.py
│   ├── import_export_service.py
│   ├── instance_service.py
│   ├── mod_path_service.py
│   ├── path_autodetect_service.py
│   ├── translation_service.py
│   └── window_manager.py
├── sort/
│   ├── __init__.py
│   ├── alphabetical_sort.py
│   ├── dependencies.py
│   ├── mod_sorting.py
│   └── topo_sort.py
├── ui/
│   ├── __init__.py
│   ├── dialogue.py
│   └── widgets/
│       ├── __init__.py
│       ├── animations.py
│       ├── button_factory.py
│       ├── custom_list_widget_item.py
│       ├── custom_list_widget_item_metadata.py
│       ├── custom_qlabels.py
│       ├── divider.py
│       ├── gui_info.py
│       ├── image_label.py
│       └── runner_panel_protocol.py
├── utils/
│   ├── __init__.py
│   ├── github/
│   │   ├── __init__.py
│   │   ├── installer.py
│   │   ├── models.py
│   │   ├── provider.py
│   │   ├── updater.py
│   │   └── worker.py
│   ├── platform/
│   │   ├── __init__.py
│   │   └── windows.py
│   ├── rentry/
│   │   ├── __init__.py
│   │   └── wrapper.py
│   ├── steam/
│   │   ├── __init__.py
│   │   ├── availability.py
│   │   ├── db_builder_thread.py
│   │   ├── workshop_utils.py
│   │   ├── steambrowser/
│   │   │   ├── __init__.py
│   │   │   ├── badge_state.py
│   │   │   ├── browser.py
│   │   │   ├── download_list.py
│   │   │   ├── js_bridge.py
│   │   │   └── page_scripts.py
│   │   ├── steamcmd/
│   │   │   ├── __init__.py
│   │   │   └── wrapper.py
│   │   ├── steamfiles/
│   │   │   ├── __init__.py
│   │   │   └── wrapper.py
│   │   ├── steamworks/
│   │   │   ├── __init__.py
│   │   │   └── wrapper.py
│   │   └── webapi/
│   │       ├── __init__.py
│   │       └── wrapper.py
│   └── todds/
│       ├── __init__.py
│       └── wrapper.py
├── views/
│   ├── __init__.py
│   ├── acf_log_panel.py
│   ├── database_builder_dialog.py
│   ├── deletion_menu.py
│   ├── description_widget.py
│   ├── divider_widget.py
│   ├── file_search_dialog.py
│   ├── filter_panel.py
│   ├── main_content_panel.py
│   ├── main_window.py
│   ├── menu_bar.py
│   ├── mods_panel.py
│   ├── mod_info_panel.py
│   ├── mod_list_icons.py
│   ├── mod_list_item_inner.py
│   ├── mod_list_widget.py
│   ├── player_log_panel.py
│   ├── settings_dialog.py
│   ├── status_panel.py
│   ├── tag_edit_dialog.py
│   ├── task_progress_window.py
│   ├── troubleshooting_dialog.py
│   └── mixins/
│       ├── __init__.py
│       ├── _shared.py
│       ├── colors_tags_mixin.py
│       ├── context_menu_mixin.py
│       ├── divider_mixin.py
│       ├── errors_warnings_mixin.py
│       ├── list_item_mixin.py
└── windows/
    ├── __init__.py
    ├── base_mods_panel.py
    ├── duplicate_mods_panel.py
    ├── github_mods_panel.py
    ├── ignore_json_editor.py
    ├── missing_dependencies_dialog.py
    ├── missing_mod_properties_panel.py
    ├── missing_mods_panel.py
    ├── rule_editor_panel.py
    ├── runner_panel.py
    ├── translation_manager.py
    ├── use_this_instead_panel.py
    ├── workshop_mod_updater_panel.py
    └── mixins/
        ├── __init__.py
        ├── _shared.py
        ├── buttons_mixin.py
        ├── columns_mixin.py
        ├── mod_rows_mixin.py
        ├── selection_mixin.py
        ├── table_mixin.py
        └── ui_mixin.py
```

### Documentation (`docs/`):
```
docs/
├── _config.yml
├── .gitignore
├── .ruby-version
├── 404.html
├── ACKNOWLEDGEMENTS.md
├── architecture.md
├── faq.md
├── faq.zh-cn.md
├── favicon.ico
├── Gemfile
├── Gemfile.lock
├── index.md
├── index.zh-cn.md
├── rentry_preview.png
├── rentry_steam_icon.png
├── _includes/
├── _sass/
│   └── color_schemes/
├── assets/
│   └── images/
│       └── previews/
│           └── settings/
├── development-guide/
└── user-guide/
```

### Libraries (`libs/`):
```
libs/
├── libsteam_api.dylib          # Steam API (macOS)
├── libsteam_api.so             # Steam API (Linux)
├── steam_api.lib               # Steam API library
├── steam_api64.dll             # Steam API 64-bit DLL
├── steam_api64.lib             # Steam API 64-bit library
├── SteamworksPy_arm.dylib      # SteamWorks Py ARM
├── SteamworksPy_i386.dylib     # SteamWorks Py i386
├── SteamworksPy_x86_64.so      # SteamWorks Py x86_64
├── SteamworksPy.dylib          # SteamWorks Py
└── SteamworksPy64.dll          # SteamWorks Py 64-bit
```

### Localization (`locales/`):
```
locales/
├── de_DE.ts    # German (Germany)
├── en_US.ts    # English (US)
├── es_ES.ts    # Spanish (Spain)
├── fr_FR.ts    # French (France)
├── ja_JP.ts    # Japanese (Japan)
├── ko_KR.ts    # Korean (South Korea)
├── pt_BR.ts    # Portuguese (Brazil)
├── ru_RU.ts    # Russian (Russia)
├── tr_TR.ts    # Turkish (Turkey)
├── zh_CN.ts    # Chinese (Simplified)
└── zh_TW.ts    # Chinese (Traditional)
```

### Packaging (`packaging/`):
```
packaging/
├── EULA.rtf
├── optimize_macos_bundle.py
├── linux/
│   ├── build-appimage.sh
│   ├── io.github.rimdex.RimDex.metainfo.xml
│   └── io.github.rimdex.RimDex.desktop
└── msi/
    ├── RimDex.wxs
    ├── build_msi.ps1
    └── RimDex.wixproj
```

### GitHub CI/CD (`.github/`):
```
.github/
├── dependabot.yml
├── labeler.yml
├── release.yml
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml
│   ├── config.yml
│   └── feature_request.yml
└── workflows/
    ├── auto_build.yml
    ├── build.yml
    ├── codeql.yml
    ├── get_version_info.yml
    ├── lint.yml
    ├── pages.yml
    ├── pr_labeler.yml
    ├── pyright.yml
    ├── pytest.yml
    ├── release.yml
    └── test_builds.yml
```

### Git Hooks (`.githooks/`):
```
.githooks/
└── pre-commit
```

### Scripts (`scripts/`):
```
scripts/
└── stats.py
```

### Stubs (`stubs/`):
```
stubs/
└── steamworks/
    ├── __init__.pyi
    └── structs.pyi
```

### Submodules:
```
submodules/
├── steamfiles/
│   ├── docs/
│   ├── steamfiles/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── acf.py
│   │   ├── appinfo.py
│   │   ├── manifest.py
│   │   ├── manifest_pb2.py
│   │   └── setup.py
│   └── tests/
│       ├── __init__.py
│       ├── test_acf.py
│       ├── test_appinfo.py
│       └── test_manifest.py
└── SteamworksPy/
    ├── examples/
    │   ├── achievements/
    │   ├── basic/
    │   └── stats/
    ├── library/
    │   └── sdk/
    │       └── redist/
    ├── redist/
    │   └── windows/
    ├── steamworks/
    │   ├── __init__.py
    │   ├── enums.py
    │   ├── exceptions.py
    │   ├── interfaces/
    │   ├── methods.py
    │   ├── structs.py
    │   └── util.py
    ├── tests/
    │   ├── __init__.py
    │   ├── legacy/
    │   └── test_base.py
    └── setup.py
```

### Tests (`tests/`):
```
tests/
├── __init__.py
├── conftest.py
├── translation_fixtures.py
├── benchmarks/
│   └── find_search_terms.py
├── cli/
│   └── test_translate.py
├── controllers/
│   ├── __init__.py
│   ├── settings_tabs/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_sorting_tab_controller.py
│   ├── test_file_search.py
│   ├── test_language_controller.py
│   ├── test_metadata_controller.py
│   ├── test_metadata_controller_compile.py
│   ├── test_metadata_db_controller.py
│   ├── test_metadata_parity.py
│   ├── test_path_autodetection.py
│   ├── test_todds_controller.py
│   └── test_troubleshooting.py
├── core/
│   ├── __init__.py
│   ├── test_app_info.py
│   ├── test_dict_utils.py
│   ├── test_event_bus.py
│   ├── test_launch_command_parser.py
│   ├── test_obfuscate_message.py
│   ├── test_schema.py
│   ├── test_translation_utils.py
│   ├── test_translation_workers.py
│   ├── test_update_check.py
│   ├── test_win_find_steam.py
│   └── test_window_launch_state.py
├── data/
│   ├── dbs/
│   ├── instance/
│   ├── mod_examples/
│   └── modconfigs/
├── git/
│   ├── __init__.py
│   └── test_git_worker.py
├── io/
│   ├── __init__.py
│   ├── test_acf_utils.py
│   ├── test_dds_utility.py
│   ├── test_files.py
│   └── test_json_utils.py
├── models/
│   ├── __init__.py
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── test_byversion_precedence.py
│   │   ├── test_metadata_factory.py
│   │   ├── test_metadata_mediator.py
│   │   └── test_metadata_structure.py
│   ├── test_filter_state.py
│   ├── test_mod_list.py
│   ├── test_run_args_migration.py
│   ├── test_settings_defaults.py
│   └── test_translation.py
├── mods/
│   ├── __init__.py
│   ├── test_aux_db_utils.py
│   ├── test_db_builder.py
│   ├── test_file_search.py
│   └── test_ignore_extensions.py
├── services/
│   ├── test_import_export_service.py
│   ├── test_instance_service.py
│   ├── test_mod_path_service.py
│   ├── test_path_autodetect_service.py
│   ├── test_translation_service.py
│   └── test_window_manager.py
├── sort/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_alphabetical_sort.py
│   ├── test_dependencies.py
│   ├── test_mod_sorting.py
│   ├── test_sort_controller.py
│   ├── test_sort_integration.py
│   └── test_topo_sort.py
├── utils/
│   ├── __init__.py
│   ├── conftest.py
│   ├── github/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_installer.py
│   │   ├── test_models.py
│   │   ├── test_provider.py
│   │   └── test_updater.py
│   ├── steam/
│   │   ├── __init__.py
│   │   ├── steamworks/
│   │   │   ├── __init__.py
│   │   │   └── test_get_app_dependencies.py
│   │   └── webapi/
│   │       ├── __init__.py
│   │       ├── test_dynamic_query.py
│   │       ├── test_get_published_file_details.py
│   │       └── test_workshop_update.py
│   └── test_*.py (various utility tests)
├── views/
│   ├── conftest.py
│   ├── test_deletion_menu.py
│   ├── test_dialogue.py
│   ├── test_filter_panel.py
│   ├── test_main_content_run.py
│   ├── test_main_window_close.py
│   ├── test_main_window_watchdog.py
│   ├── test_menu_bar.py
│   ├── test_mod_info_panel.py
│   └── test_mods_panel.py
└── windows/
    ├── conftest.py
    └── test_github_mods_panel.py
```

### Themes (`themes/`):
```
themes/
├── default-icons/
│   └── (numerous icon files: .png, .gif, .svg, .ico, .icns)
├── Modern/
│   └── style.qss
├── Nature/
│   └── style.qss
├── RimPy/
│   └── style.qss
├── SunSet/
│   └── style.qss
└── Wood/
    └── style.qss
```

---

## 3. Class & Function Definitions (from codebase analysis)

### From `app/__main__.py`:
| Name | Type | Description |
|------|------|-------------|
| `handle_exception()` | function | Exception handling |
| `main_thread() -> None` | function | Main thread entry point |
| `formatter(record: "loguru.Record") -> str` | nested function | Log record formatter |

### From `app/cli/main.py`:
| Name | Type | Description |
|------|------|-------------|
| `_LazyCommandGroup(click.Group)` | class | Lazy command group |
| `get_command(self, ctx: click.Context, cmd_name: str) -> "click.Command \| None"` | method | Get command by name |
| `cli() -> None` | function | CLI entry point |

### From `app/cli/build_db.py`:
| Name | Type | Description |
|------|------|-------------|
| `build_db()` | function | Database builder |
| `progress_callback(msg: str) -> None` | nested function | Progress callback |

### From `app/cli/translate.py`:
| Name | Type | Description |
|------|------|-------------|
| `_log(msg: str, quiet: bool) -> None` | function | Logging helper |
| `_log_green(msg: str, quiet: bool) -> None` | function | Green log helper |
| `_log_red(msg: str, quiet: bool) -> None` | function | Red log helper |
| `_resolve_languages(lang: Optional[str], quiet: bool) -> list[str]` | function | Language resolution |
| `_add_translate_options(func: Any) -> Any` | function | Option decorator |
| `_setup_translate()` | function | Translation setup |
| `translate_group() -> None` | function | Translate command group |
| `extract_cmd(lang: Optional[str], quiet: bool) -> None` | function | Extract translation command |
| `translate_cmd()` | function | Translate command |
| `_translate_language()` | async function | Async language translation |
| `validate_cmd(lang: Optional[str], quiet: bool) -> None` | function | Validation command |
| `compile_cmd(lang: Optional[str], quiet: bool) -> None` | function | Compilation command |
| `run_all_cmd()` | function | Run all translations |

### From `app/controllers/app_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `AppController(QObject)` | class | Main application controller |

### From `app/controllers/database_builder_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `DatabaseBuilderController(QObject)` | class | Database builder controller |

### From `app/controllers/file_search_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `FileSearchController(QObject)` | class | File search controller |

### From `app/controllers/instance_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `InstanceController(QObject)` | class | Instance controller |

### From `app/controllers/language_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `LanguageController` | class | Language controller |

### From `app/controllers/main_content_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `MainContentController(QObject)` | class | Main content controller |

### From `app/controllers/main_window_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `MainWindowController(QObject)` | class | Main window controller |

### From `app/controllers/menu_bar_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `MenuBarController(QObject)` | class | Menu bar controller |

### From `app/controllers/metadata_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `MetadataController(QObject)` | class | Metadata controller |

### From `app/controllers/metadata_db_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `MetadataDbController` | class | Metadata database controller |
| `AuxMetadataController(MetadataDbController)` | class | Auxiliary metadata controller |

### From `app/controllers/mods_panel_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModsPanelController(QObject)` | class | Mods panel controller |

### From `app/controllers/settings_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `SettingsController(QObject)` | class | Settings controller |

### From `app/controllers/sort_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `Sorter` | class | Sorting utility |

### From `app/controllers/theme_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `ThemeController` | class | Theme controller |

### From `app/controllers/todds_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `ToddsController` | class | Todds controller |

### From `app/controllers/translation_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `TranslationController(QObject)` | class | Translation controller |

### From `app/controllers/troubleshooting_controller.py`:
| Name | Type | Description |
|------|------|-------------|
| `TroubleshootingController(QObject)` | class | Troubleshooting controller |

### From `app/core/app_context.py`:
| Name | Type | Description |
|------|------|-------------|
| `AppContext` | class | Application context |

### From `app/core/app_info.py`:
| Name | Type | Description |
|------|------|-------------|
| `AppInfo` | class | Application information |
| `StorageSubfolders` | class | Storage subfolders |
| `BackupSubfolders` | class | Backup subfolders |

### From `app/core/constants.py`:
| Name | Type | Description |
|------|------|-------------|
| `KnownMods` | class | Known mods constant |
| `MiscConstants` | class | Miscellaneous constants |

### From `app/core/dict_utils.py`:
| Name | Type | Description |
|------|------|-------------|
| `merge_nested_dicts()` | function | Merge nested dictionaries |
| `prune_empty_dicts()` | function | Prune empty dictionaries |

### From `app/core/event_bus.py`:
| Name | Type | Description |
|------|------|-------------|
| `EventBus(QObject)` | class | Event bus for signal handling |

### From `app/core/generic.py`:
| Name | Type | Description |
|------|------|-------------|
| `SingleInstanceLock` | class | Single instance lock |

### From `app/core/launch_command_parser.py`:
| Name | Type | Description |
|------|------|-------------|
| `ParsedLaunchCommand` | class | Parsed launch command structure |

### From `app/core/obfuscate_message.py`:
| Name | Type | Description |
|------|------|-------------|
| `obfuscate_message(message: str, anonymize_path: bool = True) -> str` | function | Message obfuscation |

### From `app/core/schema.py`:
| Name | Type | Description |
|------|------|-------------|
| `Schema` | class | Schema definition |

### From `app/core/system_info.py`:
| Name | Type | Description |
|------|------|-------------|
| `SystemInfo` | class | System information |

### From `app/core/update_check.py`:
| Name | Type | Description |
|------|------|-------------|
| `UpdateManager(QObject)` | class | Update manager |
| `UpdateError(Exception)` | class | Base update error |
| `UpdateNetworkError(UpdateError)` | class | Network update error |
| `UpdateDownloadError(UpdateError)` | class | Download update error |
| `UpdateExtractionError(UpdateError)` | class | Extraction update error |
| `UpdateScriptLaunchError(UpdateError)` | class | Script launch update error |
| `ReleaseInfo(TypedDict)` | class | Release info structure |
| `DownloadInfo(TypedDict)` | class | Download info structure |
| `PlatformPatterns(TypedDict)` | class | Platform patterns structure |
| `ScriptConfig` | class | Script configuration |

### From `app/core/win_find_steam.py`:
| Name | Type | Description |
|------|------|-------------|
| `find_steam_rimworld(steam_folder: Path \| str) -> str` | function | Find Steam RimWorld |
| `get_executable_path(game_install_path: Path) -> str \| None` | function | Get executable path |
| `validate_game_executable(game_folder: str) -> bool` | function | Validate game executable |
| `launch_game_process(game_install_path: Path, run_args: str = "") -> None` | function | Launch game process |

### From `app/core/window_launch_state.py`:
| Name | Type | Description |
|------|------|-------------|
| `ParsedLaunchCommand` | class | Parsed launch command |
| `WindowLaunchState` | class | Window launch state |

### From `app/git/git_operations.py`:
| Name | Type | Description |
|------|------|-------------|
| `GitError(Exception)` | class | Git error |
| `GitOperationType(Enum)` | class | Git operation type |
| `GitNotificationHandler(Protocol)` | class | Git notification handler |
| `DefaultNotificationHandler` | class | Default notification handler |
| `GitOperationConfig` | class | Git operation configuration |
| `GitCloneResult(Enum)` | class | Git clone result |
| `GitPullResult(Enum)` | class | Git pull result |
| `GitPushResult(Enum)` | class | Git push result |
| `GitStageCommitResult(Enum)` | class | Git stage commit result |
| `GitStashResult(Enum)` | class | Git stash result |
| `ParsedGitUrl` | class | Parsed Git URL |

### From `app/git/git_utils.py`:
| Name | Type | Description |
|------|------|-------------|
| `parse_git_url(repo_url: str) -> Optional[ParsedGitUrl]` | function | Parse Git URL |
| `git_get_repo_name(repo_url: str) -> str` | function | Get repo name |

### From `app/io/files.py`:
| Name | Type | Description |
|------|------|-------------|
| `read_file(path: str \| Path) -> str` | function | Read file |
| `write_file(path: str \| Path, content: str) -> None` | function | Write file |

### From `app/models/filter_state.py`:
| Name | Type | Description |
|------|------|-------------|
| `FilterState` | class | Filter state model |

### From `app/models/instance.py`:
| Name | Type | Description |
|------|------|-------------|
| `Instance(msgspec.Struct)` | class | Instance model |

### From `app/models/mod_list.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModEntry` | class | Mod entry |
| `ModList` | class | Mod list |
| `ModListDiff` | class | Mod list diff |

### From `app/models/operation_mode.py`:
| Name | Type | Description |
|------|------|-------------|
| `OperationMode(Enum)` | class | Operation mode enum |

### From `app/models/search_result.py`:
| Name | Type | Description |
|------|------|-------------|
| `SearchResult` | class | Search result |

### From `app/models/settings.py`:
| Name | Type | Description |
|------|------|-------------|
| `Settings(QObject)` | class | Settings model |

### From `app/models/translation.py`:
| Name | Type | Description |
|------|------|-------------|
| `LangMapEntry(TypedDict)` | class | Language map entry |
| `TranslationCache` | class | Translation cache |

### From `app/mods/db_builder.py`:
| Name | Type | Description |
|------|------|-------------|
| `DatabaseBuilder(QObject)` | class | Database builder |

### From `app/mods/db_builder_core.py`:
| Name | Type | Description |
|------|------|-------------|
| `DBBuilderCore` | class | Database builder core |
| `init_empty_db_from_publishedfileids()` | function | Initialize empty database |
| `output_database()` | function | Output database |

### From `app/mods/file_search.py`:
| Name | Type | Description |
|------|------|-------------|
| `FileSearch` | class | File search utility |

### From `app/mods/ignore_manager.py`:
| Name | Type | Description |
|------|------|-------------|
| `IgnoreManager` | class | Ignore manager |

### From `app/mods/mod_info.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModInfo` | class | Mod information |

### From `app/net/http_downloader.py`:
| Name | Type | Description |
|------|------|-------------|
| `HttpDatabaseDownloader` | class | HTTP database downloader |
| `DatabaseDownloadTask` | class | Database download task |
| `HttpDownloadWorker(QThread)` | class | HTTP download worker |

### From `app/services/import_export_service.py`:
| Name | Type | Description |
|------|------|-------------|
| `ExportData` | class | Export data structure |
| `ImportExportService` | class | Import/export service |

### From `app/services/instance_service.py`:
| Name | Type | Description |
|------|------|-------------|
| `InstanceControllerProtocol(Protocol)` | class | Instance controller protocol |
| `AuxMetadataControllerProtocol(Protocol)` | class | Aux metadata controller protocol |
| `InstanceService` | class | Instance service |

### From `app/services/mod_path_service.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModPathService` | class | Mod path service |

### From `app/services/path_autodetect_service.py`:
| Name | Type | Description |
|------|------|-------------|
| `PathAutodetectService` | class | Path auto-detect service |

### From `app/services/translation_service.py`:
| Name | Type | Description |
|------|------|-------------|
| `TranslationService` | class | Translation service base |
| `GoogleTranslateService(TranslationService)` | class | Google Translate service |
| `DeepLService(TranslationService)` | class | DeepL service |
| `OpenAIService(TranslationService)` | class | OpenAI service |

### From `app/services/window_manager.py`:
| Name | Type | Description |
|------|------|-------------|
| `_Closeable(Protocol)` | class | Closeable protocol |
| `WindowManager` | class | Window manager |

### From `app/sort/topo_sort.py`:
| Name | Type | Description |
|------|------|-------------|
| `do_topo_sort()` | function | Topological sort |
| `find_circular_dependencies()` | function | Find circular dependencies |

### From `app/sort/mod_sorting.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModsPanelSortKey(Enum)` | class | Sort key enum |

### From `app/ui/dialogue.py`:
| Name | Type | Description |
|------|------|-------------|
| `_BaseDialogue(QDialog)` | class | Base dialogue |
| `_BaseMessageBox(QMessageBox)` | class | Base message box |
| `InformationBox(_BaseMessageBox)` | class | Information box |
| `BinaryChoiceDialog(_BaseMessageBox)` | class | Binary choice dialog |
| `FatalErrorDialog(_BaseDialogue)` | class | Fatal error dialog |
| `SettingsFailureDialog(QDialog)` | class | Settings failure dialog |

### From `app/utils/todds/wrapper.py`:
| Name | Type | Description |
|------|------|-------------|
| `ToddsRunner(Protocol)` | class | Todds runner protocol |
| `ToddsInterface` | class | Todds interface |

### From `app/utils/steam/steamworks/wrapper.py`:
| Name | Type | Description |
|------|------|-------------|
| `SteamworksInterface` | class | Steamworks interface |
| `SteamworksAppDependenciesQuery` | class | Steamworks app dependencies query |
| `SteamworksGameLaunch(Process)` | class | Steamworks game launch |
| `SteamworksSubscriptionHandler(Process)` | class | Steamworks subscription handler |

### From `app/views/main_window.py`:
| Name | Type | Description |
|------|------|-------------|
| `MainWindow(QMainWindow)` | class | Main application window |

### From `app/views/main_content_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `MainContent(QObject)` | class | Main content panel |

### From `app/views/menu_bar.py`:
| Name | Type | Description |
|------|------|-------------|
| `MenuBar(QObject)` | class | Menu bar |

### From `app/views/filter_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `FlowLayout(QLayout)` | class | Flow layout |
| `FlowLayoutContainer(QWidget)` | class | Flow layout container |
| `TagChip(QFrame)` | class | Tag chip widget |
| `FilterPanel(QFrame)` | class | Filter panel |
| `FilterButton(QToolButton)` | class | Filter button |

### From `app/views/player_log_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `LogPatternManager` | class | Log pattern manager |
| `LogContentStorage` | class | Log content storage |
| `LogHighlighter(QSyntaxHighlighter)` | class | Log highlighter |
| `PlayerLogTab(QWidget)` | class | Player log tab |

### From `app/views/settings_dialog.py`:
| Name | Type | Description |
|------|------|-------------|
| `SettingsDialog(QDialog)` | class | Settings dialog |

### From `app/views/mod_info_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `ClickablePathLabel(QLabel)` | class | Clickable path label |
| `ModInfoPanel` | class | Mod info panel |

### From `app/views/mod_list_widget.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModListWidget` | class | Mod list widget |

### From `app/views/mods_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `ModsPanel(QWidget)` | class | Mods panel |

### From `app/views/deletion_menu.py`:
| Name | Type | Description |
|------|------|-------------|
| `DeletionResult` | class | Deletion result |
| `ModDeletionMenu(QMenu)` | class | Mod deletion menu |

### From `app/windows/base_mods_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `BaseModsPanel` | class | Base mods panel |

### From `app/windows/mixins/_shared.py`:
| Name | Type | Description |
|------|------|-------------|
| `TrMixin` | class | Translation mixin |
| `UIElements` | class | UI elements container |
| `Layouts` | class | Layouts container |
| `ColumnIndex(Enum)` | class | Column index enum |
| `BaseModsPanelSurface` | class | Base mods panel surface |

### From `app/windows/github_mods_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `GitHubModsPanel(BaseModsPanel)` | class | GitHub mods panel |

### From `app/windows/translation_manager.py`:
| Name | Type | Description |
|------|------|-------------|
| `TranslationManagerDialog(QDialog)` | class | Translation manager dialog |

### From `app/windows/runner_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `RunnerPanel(QWidget)` | class | Runner panel |

### From `app/windows/rule_editor_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `EditableDelegate(QItemDelegate)` | class | Editable delegate |
| `RuleEditor(QWidget)` | class | Rule editor |

### From `app/windows/duplicate_mods_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `DuplicateModsPanel(BaseModsPanel)` | class | Duplicate mods panel |

### From `app/windows/use_this_instead_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `InstallationStatus(Enum)` | class | Installation status |
| `ModGroupItem` | class | Mod group item |
| `UseThisInsteadPanel(BaseModsPanel)` | class | Use this instead panel |

### From `app/windows/workshop_mod_updater_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `WorkshopModUpdaterPanel(BaseModsPanel)` | class | Workshop mod updater panel |

### From `app/windows/missing_mods_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `MissingModsPrompt(BaseModsPanel)` | class | Missing mods prompt |

### From `app/windows/missing_dependencies_dialog.py`:
| Name | Type | Description |
|------|------|-------------|
| `MissingDependenciesDialog(QDialog)` | class | Missing dependencies dialog |

### From `app/windows/missing_mod_properties_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `MissingModPropertiesPanel(BaseModsPanel)` | class | Missing mod properties panel |

### From `app/windows/ignore_json_editor.py`:
| Name | Type | Description |
|------|------|-------------|
| `IgnoreJsonEditor(QDialog)` | class | Ignore JSON editor |

### From `app/windows/database_builder_dialog.py`:
| Name | Type | Description |
|------|------|-------------|
| `DatabaseBuilderDialog(QDialog)` | class | Database builder dialog |

### From `app/windows/acf_log_panel.py`:
| Name | Type | Description |
|------|------|-------------|
| `AcfLogReader(BaseModsPanel)` | class | ACF log reader |
| `ActiveModDelegate(QStyledItemDelegate)` | class | Active mod delegate |

### From `app/windows/troubleshooting_dialog.py`:
| Name | Type | Description |
|------|------|-------------|
| `TroubleshootingDialog(QDialog)` | class | Troubleshooting dialog |

### From `translation_helper.py`:
| Name | Type | Description |
|------|------|-------------|
| `RetryConfig` | class | Retry configuration |
| `TimeoutConfig` | class | Timeout configuration |
| `TranslationConfig` | class | Translation configuration |
| `TranslationCache` | class | Translation cache |
| `LangMapEntry(TypedDict)` | class | Language map entry |
| `TranslationService` | class | Translation service base |
| `GoogleTranslateService(TranslationService)` | class | Google Translate service |
| `DeepLService(TranslationService)` | class | DeepL service |
| `OpenAIService(TranslationService)` | class | OpenAI service |
| `UnfinishedItem` | class | Unfinished item |
| `get_translation_config()` | function | Get translation config |
| `set_translation_config()` | function | Set translation config |
| `get_translation_cache()` | function | Get translation cache |
| `validate_language_code()` | function | Validate language code |
| `validate_directory_path()` | function | Validate directory path |
| `validate_api_key()` | function | Validate API key |
| `validate_model_name()` | function | Validate model name |
| `validate_timeout()` | function | Validate timeout |
| `validate_retry_count()` | function | Validate retry count |
| `validate_concurrent_requests()` | function | Validate concurrent requests |
| `create_translation_service()` | function | Create translation service |
| `find_unfinished_translations()` | function | Find unfinished translations |
| `should_skip_translation()` | function | Check if translation should be skipped |
| `auto_translate_file()` | async function | Auto-translate file |
| `get_source_keys_from_file()` | function | Get source keys from file |
| `parse_ts_file()` | function | Parse TS file |
| `save_ts_file()` | function | Save TS file |

---

## 4. Summary Statistics

### Patterns from .gitignore:
- **Directories**: 25+ directories/folders mentioned
- **File patterns**: 18+ file glob patterns
- **Special entries**: 6 special ignore entries (DEBUG, .DS_Store, etc.)
- **Total lines**: 76 lines in .gitignore

### Project Structure:
- **Root files**: ~30 configuration and script files
- **App modules**: 15 subdirectories with Python packages
- **Documentation**: Comprehensive docs directory with multi-language support
- **Libraries**: Steam API binaries for multiple platforms
- **Localization**: 12 language translation files
- **Testing**: Full test suite with parallel structure to app/
- **Themes**: 6 visual themes

### Codebase Scale:
- **App Python files**: ~230+ files
- **Test Python files**: ~80+ files
- **Submodule files**: ~35 files (steamfiles, SteamworksPy)
- **Root Python files**: 8 files (check_*.py, distribute.py, guard_common.py, translation_helper.py)
- **Total classes**: ~300+
- **Total functions**: ~800+
- **Python-based application** (RimDex)
- **Steam SDK integration**
- **Multi-language support** (i18n, 12 locale files)
- **Qt-based UI framework** (PyQt/PySide)
- **Nuitka compilation support**
- **Comprehensive testing infrastructure**
- **GitHub Actions CI/CD** (13 workflow files)
- **Git hooks** (1 pre-commit hook)

---

## 5. Generated at
**Date**: 2026-07-18  
**Source**: .gitignore + workspace file listing + code definition analysis (ccc grep)
