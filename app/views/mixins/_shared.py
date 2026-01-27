"""Shared typing surface for the ModListWidget feature mixins.

``ModListWidgetMixinBase`` declares the QListWidget surface, the shared
instance state and the signals that the feature mixins (context menu,
divider, list item, errors/warnings, colors/tags) touch. The concrete
``ModListWidget`` supplies the real, typed implementations through the
method-resolution order; the mixins only ever see the ``Any`` surface, which
lets them be type-checked independently without ``# type: ignore`` noise.

The ``Any`` stubs intentionally shadow QListWidget's own methods *for the
mixins* (so cross-mixin calls resolve), while ``ModListWidget`` itself keeps
the precise QListWidget typing because it lists ``QListWidget`` first in its
base tuple.
"""

from __future__ import annotations

from typing import Any


class ModListWidgetMixinBase:
    """Typing surface shared by all ModListWidget feature mixins.

    Intentionally does NOT inherit ``QObject``: listing the concrete
    ``ModListWidget(QListWidget, *mixins)`` with ``QListWidget`` last keeps
    ``QObject`` (reached via ``QListWidget``'s chain) *after* the widget in the
    MRO, which is required for PySide's non-cooperative ``__init__`` (otherwise
    the C++ object is initialised twice). ``tr`` and the widget surface are
    declared as ``Any`` stubs so the mixins can be type-checked independently.
    """

    # ── QObject surface used across mixins (tr, etc.) ────────────
    tr: Any

    # ── Instance state (set by ModListWidget.__init__) ────────────
    settings: Any
    metadata_controller: Any
    list_type: Any
    paths: Any
    ignore_warning_list: Any
    show_tags: Any
    show_translation_status: Any
    translation_lookup: Any
    deletion_sub_menu: Any
    _latest_save_package_ids: Any

    # ── Signals (defined on ModListWidget) ───────────────────────
    edit_rules_signal: Any
    item_added_signal: Any
    key_press_signal: Any
    list_update_signal: Any
    mod_info_signal: Any
    recalculate_warnings_signal: Any
    refresh_signal: Any
    tags_changed_signal: Any
    update_git_mods_signal: Any
    steamdb_blacklist_signal: Any

    # ── QListWidget / QWidget surface used across mixins ─────────
    item: Any
    addItem: Any
    model: Any
    selectionModel: Any
    setDefaultDropAction: Any
    setDragDropMode: Any
    setSelectionMode: Any
    currentItemChanged: Any
    itemClicked: Any
    itemDoubleClicked: Any
    installEventFilter: Any
    horizontalScrollBar: Any
    verticalScrollBar: Any
    itemWidget: Any
    setItemWidget: Any
    removeItemWidget: Any
    count: Any
    row: Any
    takeItem: Any
    insertItem: Any
    clear: Any
    setUpdatesEnabled: Any
    repaint: Any
    visualItemRect: Any
    viewport: Any
    indexAt: Any
    visualRect: Any
    currentItem: Any
    selectedItems: Any
    selectedIndexes: Any
    setFocus: Any
    clearFocus: Any
    hasFocus: Any
    mapFromGlobal: Any
    mapToGlobal: Any
    itemAt: Any

    # ── Cross-mixin helpers (real impls live in sibling mixins) ──
    apply_collapse_states: Any
    toggle_divider_collapse: Any
    remove_divider: Any
    rename_divider: Any
    add_divider: Any
    _find_next_divider_index: Any
    _update_divider_mod_counts: Any
    _update_single_divider_mod_count: Any
    get_dividers_data: Any
    restore_dividers: Any
    create_widget_for_item: Any
    check_widgets_visible: Any
    check_item_visible: Any
    get_visible_indexes: Any
    rebuild_item_widget_from_uuid: Any
    recreate_mod_list: Any
    recreate_mod_list_and_sort: Any
    replaceItemAtIndex: Any
    handle_rows_inserted: Any
    handle_rows_removed: Any
    append_new_item: Any
    get_all_mod_list_items: Any
    get_all_loaded_mod_list_items: Any
    get_all_toggled_mod_list_items: Any
    get_all_loaded_and_toggled_mod_list_items: Any
    handle_item_data_changed: Any
    handle_other_list_row_added: Any
    get_item_widget_at_index: Any
    toggle_warning: Any
    change_mod_color: Any
    change_all_mod_colors: Any
    reset_mod_color: Any
    reset_all_mod_colors: Any
    get_common_selected_tags: Any
    refresh_mod_tags_for_uuid: Any
    set_tags_visible: Any
    SetUserCustomColors: Any
    SaveUserCustomColors: Any
    recalculate_internal_errors_warnings: Any
    _check_missing_dependencies: Any
    _check_incompatibilities: Any
    _check_load_order_violations: Any
    _check_version_mismatch: Any
    _check_use_this_instead: Any
    _get_latest_save_package_ids: Any
    _has_replacement: Any
    _mod_to_context_dict: Any
    _get_selected_metadata: Any
    _calculate_translation_similarity: Any
    _find_and_open_translations: Any
    _show_divider_context_menu: Any
    on_selection_changed: Any
    dropEvent: Any
    focusOutEvent: Any
    keyPressEvent: Any
    resizeEvent: Any
    mod_changed_to: Any
    mod_clicked: Any
    mod_double_clicked: Any
