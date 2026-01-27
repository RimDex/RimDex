"""Backward-compatible re-export shim.

All functionality has moved to focused modules under ``app.core``:

- :mod:`app.core.fs_utils` — filesystem operations, path helpers, formatting
- :mod:`app.core.text_utils` — text/time parsing, URL utilities
- :mod:`app.core.ui_helpers` — clipboard, file openers, warnings, network
- :mod:`app.core.game_launch` — game executable detection and process spawning

New code should import from the specific modules directly.
"""

from app.core.fs_utils import (  # noqa: F401
    attempt_chmod,
    chunks,
    delete_files_except_extension,
    delete_files_only_extension,
    delete_files_with_condition,
    directories,
    find_steam_rimworld,
    flatten_to_list,
    format_file_size,
    get_path_up_to_string,
    handle_remove_read_only,
    rmtree,
    sanitize_filename,
    scanpath,
)
from app.core.game_launch import (  # noqa: F401
    get_executable_path,
    launch_game_process,
    launch_process,
    validate_game_executable,
)
from app.core.text_utils import (  # noqa: F401
    check_valid_http_git_url,
    extract_git_dir_name,
    extract_git_user_or_org,
    extract_page_title_steam_browser,
    format_time_display,
    get_relative_time,
)
from app.core.ui_helpers import (  # noqa: F401
    check_internet_connection,
    copy_to_clipboard_safely,
    open_url_browser,
    platform_specific_open,
    restart_application,
    show_no_steam_warning,
    show_snap_steam_warning,
    upload_data_to_0x0_st,
)
