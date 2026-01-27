from functools import partial
from typing import Optional, cast

from loguru import logger
from PySide6.QtCore import (
    QSize,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QIcon,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from rapidfuzz import fuzz
from sqlalchemy import text

from app.controllers.metadata_controller import MetadataController
from app.controllers.metadata_db_controller import AuxMetadataController
from app.models.divider import is_divider_uuid
from app.models.filter_state import FilterState
from app.models.metadata.metadata_structure import AboutXmlMod, ModType
from app.models.settings import Settings
from app.sort.mod_sorting import (
    FolderSizeWorker,
    ModsPanelSortKey,
)
from app.utils.app_info import AppInfo
from app.utils.aux_db_utils import (
    auxdb_get_all_tags,
)
from app.utils.custom_list_widget_item import CustomListWidgetItem
from app.utils.custom_list_widget_item_metadata import (
    CustomListWidgetItemMetadata,
    bulk_prefetch_item_metadata,
)
from app.utils.custom_qlabels import AdvancedClickableQLabel
from app.utils.event_bus import EventBus
from app.utils.mod_utils import MOD_TYPE_TO_FILTER_SOURCE
from app.views.dialogue import (
    show_warning,
)
from app.views.filter_panel import FilterButton
from app.views.mod_list_icons import ModListIcons
from app.views.mod_list_item_inner import ModListItemInner
from app.views.mod_list_widget import ModListWidget


class ModsPanel(QWidget):
    """
    This class controls the layout and functionality for the
    active/inactive mods list panel on the GUI.
    """

    check_dependencies_signal = Signal()

    # OPTIMIZATION: Class-level constant for sort text to enum mapping
    # Centralizes the text->enum conversion logic
    SORT_TEXT_TO_KEY_MAP = {
        "Name": ModsPanelSortKey.MODNAME,
        "Author": ModsPanelSortKey.AUTHOR,
        "Modified Time": ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME,
        "Folder Size": ModsPanelSortKey.FOLDER_SIZE,
        "Version": ModsPanelSortKey.VERSION,
        "PackageId": ModsPanelSortKey.PACKAGEID,
        "Color": ModsPanelSortKey.MOD_COLOR,
        "Tags": ModsPanelSortKey.MOD_TAGS,
        "Workshop Updated": ModsPanelSortKey.MOD_UPDATED,
    }

    # Note: combobox items store their corresponding `ModsPanelSortKey` in
    # userData; avoid index-based mappings which are fragile if ordering
    # changes or items are hidden.

    def update_sort_ui_from_settings(self) -> None:
        """
        Update the inactive mods sort UI elements from settings.

        Restores the saved sort key and direction to the UI combobox and button.
        """
        self.inactive_mods_sort_key = self.settings.inactive_mods_sort_key
        self.inactive_mods_sort_descending = self.settings.inactive_mods_sort_descending
        # Select the combo box entry by matching stored enum name to item userData
        try:
            desired_enum = ModsPanelSortKey[self.inactive_mods_sort_key]
        except Exception:
            desired_enum = ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME
        idx = self.inactive_mods_sort_combobox.findData(desired_enum)
        if idx >= 0:
            self.inactive_mods_sort_combobox.setCurrentIndex(idx)
        else:
            fallback_idx = self.inactive_mods_sort_combobox.findData(
                ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME
            )
            if fallback_idx >= 0:
                self.inactive_mods_sort_combobox.setCurrentIndex(fallback_idx)
        # Update sort order button text
        self.inactive_mods_sort_order_button.setText(
            self.tr("Desc") if self.inactive_mods_sort_descending else self.tr("Asc")
        )

    def __init__(
        self, settings: Settings, metadata_controller: MetadataController
    ) -> None:
        """
        Initialize the class.
        Create a ListWidget using the dict of mods. This will
        create a row for every key-value pair in the dict.
        """
        super(ModsPanel, self).__init__()

        # Cache MetadataController instance and initialize panel
        logger.debug("Initializing ModsPanel")
        self.metadata_controller = metadata_controller
        self.settings = settings

        # Load inactive mods sort settings
        if self.settings.save_inactive_mods_sort_state:
            self.inactive_mods_sort_key = self.settings.inactive_mods_sort_key
            self.inactive_mods_sort_descending = (
                self.settings.inactive_mods_sort_descending
            )
        else:
            self.inactive_mods_sort_key = "FILESYSTEM_MODIFIED_TIME"
            self.inactive_mods_sort_descending = True

        # Background folder-size sorting state
        self._size_progress_dialog: Optional[QProgressDialog] = None
        self._size_thread: Optional[QThread] = None
        self._size_worker: Optional[FolderSizeWorker] = None
        self._size_current_uuids: list[str] = []

        # Build search filter text-to-key mapping (translation-safe)
        self._search_filter_map: dict[str, str] = {
            self.tr("Name"): "name",
            self.tr("Notes"): "notes",
            self.tr("Tags"): "tags",
            self.tr("PackageId"): "packageid",
            self.tr("Author(s)"): "authors",
            self.tr("PublishedFileId"): "publishedfileid",
            self.tr("Version"): "version",
            self.tr("Colors"): "colors",
        }

        # Cache for mod notes fuzzy search results
        self._notes_search_cache: dict[str, set[str]] = {}

        # Debounce timer for non-heavy sort operations
        self._sort_debounce_timer = QTimer()
        self._sort_debounce_timer.setSingleShot(True)
        self._sort_debounce_timer.timeout.connect(self._execute_pending_sort)
        self._pending_sort_params: Optional[
            tuple[str, list[str], ModsPanelSortKey, bool]
        ] = None

        # Base layout with a splitter for resizable mod lists
        self.panel = QVBoxLayout()
        self.lists_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.lists_splitter.setChildrenCollapsible(False)
        self.lists_splitter.setHandleWidth(4)
        self.active_panel = QVBoxLayout()
        self.inactive_panel = QVBoxLayout()
        self.inactive_container = QWidget()
        self.inactive_container.setLayout(self.inactive_panel)
        self.active_container = QWidget()
        self.active_container.setLayout(self.active_panel)
        self.lists_splitter.addWidget(self.inactive_container)
        self.lists_splitter.addWidget(self.active_container)
        self.lists_splitter.setStretchFactor(0, 1)
        self.lists_splitter.setStretchFactor(1, 1)
        self.panel.addWidget(self.lists_splitter, 1)

        # Create the buttons layout
        self.button_panel = QHBoxLayout()
        # Create buttons frame
        self.button_panel_frame: QFrame = QFrame()
        self.button_panel_frame.setObjectName("MainWindowButtons")

        # Create and add Use This Instead button
        self.use_this_instead_button = QPushButton(
            self.tr('Check "Use This Instead" Database')
        )
        self.use_this_instead_button.setObjectName("UseThisInsteadButton")
        self.use_this_instead_button.clicked.connect(
            EventBus().use_this_instead_clicked.emit
        )
        self.button_panel.addWidget(self.use_this_instead_button)

        # Create and add Check Dependencies button
        self.check_dependencies_button: QPushButton = QPushButton(
            self.tr("Check Dependencies")
        )
        self.check_dependencies_button.setObjectName("CheckDependenciesButton")
        self.button_panel.addWidget(self.check_dependencies_button)
        self.check_dependencies_button.clicked.connect(
            self.check_dependencies_signal.emit
        )
        self.button_panel_frame.setLayout(self.button_panel)

        # Add the buttons frame below the lists panel
        self.panel.addWidget(self.button_panel_frame, 0)

        self.mode_filter_icon = QIcon(
            str(AppInfo().theme_data_folder / "default-icons" / "filter.png")
        )
        self.mode_filter_tooltip = self.tr("Hide Filter Disabled")
        self.mode_nofilter_icon = QIcon(
            str(AppInfo().theme_data_folder / "default-icons" / "nofilter.png")
        )
        self.mode_nofilter_tooltip = self.tr("Hide Filter Enabled")

        # ACTIVE mod list widget
        self.active_mods_label = QLabel(self.tr("Active [0]"))
        self.active_mods_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_mods_label.setObjectName("summaryValue")
        self.active_mods_list = ModListWidget(
            list_type="Active",
            settings=self.settings,
            metadata_controller=self.metadata_controller,
        )
        # Active mods search widgets
        self.active_mods_search_layout = QHBoxLayout()
        self.initialize_active_mods_search_widgets()

        # Add active mods widgets to layout
        self.active_panel.addWidget(self.active_mods_label)
        self.active_panel.addLayout(self.active_mods_search_layout)
        self.active_panel.addWidget(self.active_mods_list)

        # Add the errors summary frame below the active mods list
        self.active_panel.addWidget(self.errors_summary_frame)

        # Initialize inactive mods widgets
        self.inactive_mods_label = QLabel(self.tr("Inactive [0]"))
        self.inactive_mods_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inactive_mods_label.setObjectName("summaryValue")
        self.inactive_mods_list = ModListWidget(
            list_type="Inactive",
            settings=self.settings,
            metadata_controller=self.metadata_controller,
        )

        # Inactive mods search layout
        self.inactive_mods_search_layout = QHBoxLayout()
        self.initialize_inactive_mods_search_widgets()

        # Add inactive mods widgets to layout
        self.inactive_panel.addWidget(self.inactive_mods_label)
        self.inactive_panel.addLayout(self.inactive_mods_search_layout)
        self.inactive_panel.addWidget(self.inactive_mods_list)

        # Connect signals and slots
        self.connect_signals()

        # Connect to settings changed to update sort UI
        EventBus().settings_have_changed.connect(self.update_sort_ui_from_settings)

        # Set the main layout for the widget
        self.setLayout(self.panel)

        logger.debug("Finished ModsPanel initialization")

    def initialize_active_mods_search_widgets(self) -> None:
        """Initialize widgets for active mods search layout."""
        self.active_mods_search_filter_state = True
        self.active_mods_search_mode_filter_button = QToolButton()
        self.active_mods_search_mode_filter_button.setIcon(self.mode_filter_icon)
        self.active_mods_search_mode_filter_button.setToolTip(self.mode_filter_tooltip)
        self.active_mods_search_mode_filter_button.clicked.connect(
            self.on_active_mods_mode_filter_toggle
        )
        self.active_mods_search = QLineEdit()
        self.active_mods_search.setClearButtonEnabled(True)
        self.active_mods_search.textChanged.connect(self.on_active_mods_search)
        self.active_mods_search.inputRejected.connect(self.on_active_mods_search_clear)
        self.active_mods_search.setPlaceholderText(self.tr("Search by..."))
        # Add explicit type annotation to help mypy
        self.active_mods_search_clear_button = cast(
            QToolButton, self.active_mods_search.findChild(QToolButton)
        )
        if not isinstance(self.active_mods_search_clear_button, QToolButton):
            raise TypeError("Could not find QToolButton in QLineEdit")
        self.active_mods_search_clear_button.setEnabled(True)
        self.active_mods_search_clear_button.clicked.connect(
            self.on_active_mods_search_clear
        )
        self.active_mods_search_filter: QComboBox = QComboBox()
        self.active_mods_search_filter.setObjectName("MainUI")
        self.active_mods_search_filter.setMaximumWidth(125)
        self.active_mods_search_filter.addItems(
            [
                self.tr("Name"),
                self.tr("Notes"),
                self.tr("Tags"),
                self.tr("PackageId"),
                self.tr("Author(s)"),
                self.tr("PublishedFileId"),
                self.tr("Version"),
                self.tr("Colors"),
            ]
        )

        # FilterButton replaces old source/type/tag filter widgets
        self.active_filter_button = FilterButton(self)
        self.active_filter_button.filter_panel.filters_changed.connect(
            lambda: self.signal_search_and_filters(
                list_type="Active", pattern=self.active_mods_search.text()
            )
        )

        # Active mods search layouts
        self.active_mods_search_layout.addWidget(self.active_mods_search, 45)
        self.active_mods_search_layout.addWidget(self.active_mods_search_filter, 70)
        self.active_mods_search_layout.addWidget(self.active_filter_button)
        self.active_mods_search_layout.addWidget(
            self.active_mods_search_mode_filter_button
        )
        # Active mods list Errors/warnings widgets
        self.errors_summary_frame: QFrame = QFrame()
        self.errors_summary_frame.setObjectName("errorFrame")
        self.errors_summary_layout = QVBoxLayout()
        self.errors_summary_layout.setContentsMargins(0, 0, 0, 0)
        self.errors_summary_layout.setSpacing(2)
        # Create horizontal layout for warnings and errors
        self.warnings_errors_layout = QHBoxLayout()
        self.warnings_errors_layout.setSpacing(2)
        self.warnings_icon: QLabel = QLabel()
        self.warnings_icon.setPixmap(ModListIcons.warning_icon().pixmap(QSize(20, 20)))
        self.warnings_text: AdvancedClickableQLabel = AdvancedClickableQLabel(
            self.tr("0 warnings")
        )
        self.warnings_text.setObjectName("summaryValue")
        self.warnings_text.setToolTip(self.tr("Click to only show mods with warnings"))
        self.errors_icon: QLabel = QLabel()
        self.errors_icon.setPixmap(ModListIcons.error_icon().pixmap(QSize(20, 20)))
        self.errors_text: AdvancedClickableQLabel = AdvancedClickableQLabel("0 errors")
        self.errors_text.setObjectName("summaryValue")
        self.errors_text.setToolTip(self.tr("Click to only show mods with errors"))
        self.warnings_layout = QHBoxLayout()
        self.warnings_layout.addWidget(self.warnings_icon, 1)
        self.warnings_layout.addWidget(self.warnings_text, 99)
        self.errors_layout = QHBoxLayout()
        self.errors_layout.addWidget(self.errors_icon, 1)
        self.errors_layout.addWidget(self.errors_text, 99)
        self.warnings_errors_layout.addLayout(self.warnings_layout, 50)
        self.warnings_errors_layout.addLayout(self.errors_layout, 50)

        # Add warnings/errors layout to main vertical layout
        self.errors_summary_layout.addLayout(self.warnings_errors_layout)

        # Add to the outer frame
        self.errors_summary_frame.setLayout(self.errors_summary_layout)
        self.errors_summary_frame.setHidden(True)
        # New mods label (next to warnings/errors)
        self.news_layout = QHBoxLayout()
        self.new_icon: QLabel = QLabel()
        self.new_icon.setPixmap(
            QIcon(
                str(AppInfo().theme_data_folder / "default-icons" / "new.png")
            ).pixmap(QSize(20, 20))
        )
        self.new_text: AdvancedClickableQLabel = AdvancedClickableQLabel(
            self.tr("0 new")
        )
        self.new_text.setObjectName("summaryValue")
        self.new_text.setToolTip(
            self.tr("Click to only show active mods not in latest save")
        )
        self.news_layout.addWidget(self.new_icon, 1)
        self.news_layout.addWidget(self.new_text, 99)
        self.warnings_errors_layout.addLayout(self.news_layout, 50)

    def initialize_inactive_mods_search_widgets(self) -> None:
        """Initialize widgets for inactive mods search layout."""
        self.inactive_mods_search_filter_state = True
        self.inactive_mods_search_mode_filter_button = QToolButton()
        self.inactive_mods_search_mode_filter_button.setIcon(self.mode_filter_icon)
        self.inactive_mods_search_mode_filter_button.setToolTip(
            self.mode_filter_tooltip
        )
        self.inactive_mods_search_mode_filter_button.clicked.connect(
            self.on_inactive_mods_mode_filter_toggle
        )
        self.inactive_mods_search = QLineEdit()
        self.inactive_mods_search.setClearButtonEnabled(True)
        self.inactive_mods_search.textChanged.connect(self.on_inactive_mods_search)
        self.inactive_mods_search.inputRejected.connect(
            self.on_inactive_mods_search_clear
        )
        self.inactive_mods_search.setPlaceholderText(self.tr("Search by..."))
        # Add explicit type annotation to help mypy
        self.inactive_mods_search_clear_button = cast(
            QToolButton, self.inactive_mods_search.findChild(QToolButton)
        )
        if not isinstance(self.inactive_mods_search_clear_button, QToolButton):
            raise TypeError("Could not find QToolButton in QLineEdit")
        self.inactive_mods_search_clear_button.setEnabled(True)
        self.inactive_mods_search_clear_button.clicked.connect(
            self.on_inactive_mods_search_clear
        )
        self.inactive_mods_search_filter: QComboBox = QComboBox()
        self.inactive_mods_search_filter.setParent(self)
        self.inactive_mods_search_filter.setObjectName("MainUI")
        self.inactive_mods_search_filter.setMaximumWidth(140)
        self.inactive_mods_search_filter.addItems(
            [
                self.tr("Name"),
                self.tr("Notes"),
                self.tr("Tags"),
                self.tr("PackageId"),
                self.tr("Author(s)"),
                self.tr("PublishedFileId"),
                self.tr("Version"),
                self.tr("Colors"),
            ]
        )

        # FilterButton replaces old source/type/tag filter widgets
        self.inactive_filter_button = FilterButton(self)
        self.inactive_filter_button.filter_panel.filters_changed.connect(
            lambda: self.signal_search_and_filters(
                list_type="Inactive", pattern=self.inactive_mods_search.text()
            )
        )

        self.inactive_mods_sort_combobox: QComboBox = QComboBox()
        self.inactive_mods_sort_combobox.setParent(self)
        self.inactive_mods_sort_combobox.setObjectName("MainUI")
        self.inactive_mods_sort_combobox.setMaximumWidth(120)
        self.inactive_mods_sort_combobox.setToolTip(self.tr("Sort inactive mods by"))
        # Populate combobox with translated text and store the corresponding
        # ModsPanelSortKey enum in the userData for each item. Using userData
        # keeps the mapping stable across locales and if the visible text changes.
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Name"), ModsPanelSortKey.MODNAME
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Author"), ModsPanelSortKey.AUTHOR
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Modified Time"), ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Folder Size"), ModsPanelSortKey.FOLDER_SIZE
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Version"), ModsPanelSortKey.VERSION
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("PackageId"), ModsPanelSortKey.PACKAGEID
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Color"), ModsPanelSortKey.MOD_COLOR
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Tags"), ModsPanelSortKey.MOD_TAGS
        )
        self.inactive_mods_sort_combobox.addItem(
            self.tr("Workshop Updated"), ModsPanelSortKey.MOD_UPDATED
        )
        # Set initial combo box selection based on loaded settings by matching
        # the stored enum name to the item userData. Fall back to
        # FILESYSTEM_MODIFIED_TIME if the stored value is invalid.
        try:
            desired_enum = ModsPanelSortKey[self.inactive_mods_sort_key]
        except Exception:
            desired_enum = ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME
        idx = self.inactive_mods_sort_combobox.findData(desired_enum)
        if idx >= 0:
            self.inactive_mods_sort_combobox.setCurrentIndex(idx)
        else:
            # Ensure at least a sensible default is selected
            fallback_idx = self.inactive_mods_sort_combobox.findData(
                ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME
            )
            if fallback_idx >= 0:
                self.inactive_mods_sort_combobox.setCurrentIndex(fallback_idx)
        # Sort order toggle (Asc/Desc)
        self.inactive_sort_descending: bool = self.inactive_mods_sort_descending
        self.inactive_mods_sort_order_button: QToolButton = QToolButton()
        self.inactive_mods_sort_order_button.setParent(self)
        self.inactive_mods_sort_order_button.setObjectName("MainUI")
        self.inactive_mods_sort_order_button.setMaximumWidth(60)
        self.inactive_mods_sort_order_button.setToolTip(self.tr("Toggle sort order"))
        self.inactive_mods_sort_order_button.setText(
            self.tr("Desc") if self.inactive_mods_sort_descending else self.tr("Asc")
        )
        self.inactive_mods_search_layout.addWidget(self.inactive_mods_search, 45)
        self.inactive_mods_search_layout.addWidget(self.inactive_mods_search_filter, 70)
        self.inactive_mods_search_layout.addWidget(self.inactive_filter_button)
        self.inactive_mods_search_layout.addWidget(
            self.inactive_mods_search_mode_filter_button
        )
        self.inactive_mods_search_layout.addWidget(
            self.inactive_mods_sort_combobox, 120
        )
        self.inactive_mods_search_layout.addWidget(self.inactive_mods_sort_order_button)

    def connect_signals(self) -> None:
        self.active_mods_list.list_update_signal.connect(
            self.on_active_mods_list_updated
        )
        self.inactive_mods_list.list_update_signal.connect(
            self.on_inactive_mods_list_updated
        )
        self.active_mods_list.recalculate_warnings_signal.connect(
            partial(self.recalculate_list_errors_warnings, list_type="Active")
        )
        self.inactive_mods_list.recalculate_warnings_signal.connect(
            partial(self.recalculate_list_errors_warnings, list_type="Inactive")
        )
        self.active_mods_list.tags_changed_signal.connect(
            self.refresh_all_tag_filter_selectors
        )
        self.inactive_mods_list.tags_changed_signal.connect(
            self.refresh_all_tag_filter_selectors
        )
        self.inactive_mods_sort_combobox.currentTextChanged.connect(
            self.on_inactive_mods_sort_changed
        )
        self.inactive_mods_sort_order_button.clicked.connect(
            self.on_inactive_mods_sort_order_toggled
        )

    def on_inactive_mods_sort_order_toggled(self) -> None:
        """
        Handle the Asc/Desc toggle button click for inactive mods sorting.

        Toggles the sort direction, updates the button label, saves the state
        if enabled, and re-sorts the list with the new direction.
        """
        # Toggle state and update button label
        self.inactive_sort_descending = not self.inactive_sort_descending
        self.inactive_mods_sort_order_button.setText(
            self.tr("Desc") if self.inactive_sort_descending else self.tr("Asc")
        )

        # Save if enabled
        if self.settings.save_inactive_mods_sort_state:
            self.settings.inactive_mods_sort_descending = self.inactive_sort_descending
            self.settings.save()

        # Apply updated sort direction - re-sort with new descending flag
        current_text = self.inactive_mods_sort_combobox.currentText()
        # Re-sort list with updated descending flag
        self.on_inactive_mods_sort_changed(current_text)

    @Slot(int, int)
    def _on_folder_size_progress(self, current: int, total: int) -> None:
        """
        Update the progress dialog during folder size calculation.

        Slot for FolderSizeWorker.progress signal. Updates the progress dialog
        with the current progress (current/total items processed).

        Args:
            current: Current number of items processed
            total: Total number of items to process
        """
        if self._size_progress_dialog is not None:
            self._size_progress_dialog.setMaximum(total)
            self._size_progress_dialog.setValue(current)

    @Slot(dict)
    def _on_folder_size_finished(self, sizes: dict[str, int]) -> None:
        """
        Handle completion of folder size calculation.

        Slot for FolderSizeWorker.finished signal. Sorts the inactive mods list
        by computed folder sizes, rebuilds the UI with the sorted order,
        and cleans up the background worker and progress dialog.

        Args:
            sizes: Dictionary mapping mod UUID -> folder size in bytes
        """
        try:
            # Sort and rebuild with visible progress to avoid post-close pause
            current_uuids: list[str] = getattr(self, "_size_current_uuids", [])
            sorted_uuids = sorted(
                current_uuids,
                key=lambda u: sizes.get(u, 0),
                reverse=self.inactive_sort_descending,
            )
            if self._size_progress_dialog is not None:
                self._size_progress_dialog.close()
                self._size_progress_dialog = None

            lw = self.inactive_mods_list
            # Disconnect model signals during rebuild to prevent cascading updates and duplicate items
            lw.setUpdatesEnabled(False)
            try:
                lw.model().rowsInserted.disconnect(lw.handle_rows_inserted)
            except TypeError:
                pass  # Signal not connected
            try:
                lw.model().rowsAboutToBeRemoved.disconnect(lw.handle_rows_removed)
            except TypeError:
                pass  # Signal not connected

            lw.clear()
            lw.paths = list()

            # Get aux controller once for performance
            aux_metadata_controller = (
                AuxMetadataController.get_or_create_cached_instance(
                    self.settings.aux_db_path
                )
            )

            # Single session + single aux query + single metadata pass
            with aux_metadata_controller.Session() as aux_metadata_session:
                aux_entries = aux_metadata_controller.get_all_by_paths(
                    aux_metadata_session, sorted_uuids
                )
                pre_fetched = bulk_prefetch_item_metadata(
                    self.metadata_controller, aux_entries, sorted_uuids
                )
                for uuid_key in sorted_uuids:
                    list_item = CustomListWidgetItem(lw)
                    data = CustomListWidgetItemMetadata(
                        path=uuid_key,
                        list_type=lw.list_type,
                        settings=self.settings,
                        **pre_fetched[uuid_key],
                    )
                    data.__dict__["show_tags"] = lw.show_tags
                    list_item.setData(Qt.ItemDataRole.UserRole, data)
                    lw.addItem(list_item)
            lw.paths = sorted_uuids

            # Reconnect model signals
            lw.model().rowsInserted.connect(
                lw.handle_rows_inserted, Qt.ConnectionType.QueuedConnection
            )
            lw.model().rowsAboutToBeRemoved.connect(
                lw.handle_rows_removed, Qt.ConnectionType.QueuedConnection
            )
            lw.setUpdatesEnabled(True)
            lw.repaint()
            # Load visible widgets after rebuild completes
            lw.check_widgets_visible()
            # Emit signal to update counts and errors/warnings
            lw.list_update_signal.emit(str(lw.count()))
        finally:
            if self._size_progress_dialog is not None:
                self._size_progress_dialog.close()
                self._size_progress_dialog = None
            QApplication.restoreOverrideCursor()
            if self._size_thread is not None:
                self._size_thread.quit()
                self._size_thread.deleteLater()
                self._size_thread = None
            if self._size_worker is not None:
                try:
                    self._size_worker.deleteLater()
                except Exception:
                    pass
                self._size_worker = None

    def _execute_pending_sort(self) -> None:
        """
        Execute the pending sort operation after debounce timer expires.

        Non-heavy sorts (Name, Author, etc.) are debounced to prevent rapid
        rebuilds. This method executes the actual sort after the debounce delay.

        Uses _pending_sort_params stored by on_inactive_mods_sort_changed.
        """
        if self._pending_sort_params:
            list_type, uuids, key, descending = self._pending_sort_params
            self._pending_sort_params = None
            # Get the appropriate list widget and call recreate_mod_list_and_sort
            mod_list = (
                self.active_mods_list
                if list_type == "Active"
                else self.inactive_mods_list
            )
            mod_list.recreate_mod_list_and_sort(list_type, uuids, key, descending)

    @staticmethod
    def _text_to_sort_key(text: str) -> ModsPanelSortKey:
        """
        Convert combobox text to sort key enum.

        Uses SORT_TEXT_TO_KEY_MAP constant for centralized text-to-enum mapping.
        Falls back to FILESYSTEM_MODIFIED_TIME if text is not found.

        Args:
            text: The selected sort option text from the combobox
                 (e.g., "Name", "Author", "Folder Size")

        Returns:
            ModsPanelSortKey enum corresponding to the text, or
            FILESYSTEM_MODIFIED_TIME if not found
        """
        return ModsPanel.SORT_TEXT_TO_KEY_MAP.get(
            text,
            ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME,  # Default fallback
        )

    def on_inactive_mods_sort_changed(self, text: str) -> None:
        """
        Handle selection change in the inactive mods sort combobox.

        Determines whether to use background calculation (for folder size sorting)
        or debounced fast sorting (for other sorts). Folder size sorting requires
        filesystem I/O and is calculated in the background. Other sorts are fast
        data-only lookups and use debouncing to prevent rapid rebuilds.

        Args:
            text: The selected sort option text from the combobox
        """
        # Prefer the enum stored in the combobox itemData (userData). This is
        # robust across locales and reordering. Fall back to the text->enum map
        # if no userData is available.
        current_data = self.inactive_mods_sort_combobox.currentData()
        if isinstance(current_data, ModsPanelSortKey):
            sort_key = current_data
        else:
            # Fallback to text-based mapping for safety
            sort_key = self._text_to_sort_key(text)
        # Ensure we have a valid fallback (align with global default)
        if not isinstance(sort_key, ModsPanelSortKey):
            sort_key = ModsPanelSortKey.FILESYSTEM_MODIFIED_TIME

        # Get current list of paths to sort
        current_uuids = self.inactive_mods_list.paths.copy()
        if current_uuids:
            # Folder size sorting requires background calculation
            # Other sorts are fast data lookups using debounce
            is_heavy = sort_key == ModsPanelSortKey.FOLDER_SIZE
            if is_heavy:
                # Background calculation required for folder size sorting
                dlg = QProgressDialog(self.window())
                dlg.setLabelText(self.tr("Calculating folder sizes..."))
                dlg.setCancelButton(None)
                dlg.setRange(0, len(current_uuids))
                dlg.setMinimumDuration(0)
                dlg.setAutoClose(True)
                dlg.setAutoReset(False)
                dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                dlg.setValue(0)
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                # Start worker thread
                thr = QThread(self)
                self._size_thread = thr
                self._size_current_uuids = current_uuids
                worker = FolderSizeWorker(current_uuids)
                self._size_worker = worker
                worker.moveToThread(thr)
                worker.progress.connect(self._on_folder_size_progress)
                worker.finished.connect(self._on_folder_size_finished)
                thr.started.connect(worker.run)
                thr.start()
                self._size_progress_dialog = dlg
                dlg.show()
            else:
                # Non-heavy sorts use debouncing to prevent rapid rebuilds
                # Store pending sort parameters
                self._pending_sort_params = (
                    "Inactive",
                    current_uuids,
                    sort_key,
                    self.inactive_sort_descending,
                )

                # Cancel pending sort and start new timer (200ms debounce delay)
                self._sort_debounce_timer.stop()
                self._sort_debounce_timer.start(200)

                # Save the sort key immediately if enabled
                if self.settings.save_inactive_mods_sort_state:
                    self.settings.inactive_mods_sort_key = sort_key.name
                    self.settings.save()
                self.inactive_mods_sort_key = sort_key.name

    def mod_list_updated(
        self, count: str, list_type: str, recalculate_list_errors_warnings: bool = True
    ) -> None:
        # If count is 'drop', it indicates that the update was just a drag and drop within the list
        if count != "drop":
            logger.info(f"{list_type} mod count changed to: {count}")
            self.update_count(list_type=list_type)
        if recalculate_list_errors_warnings:
            # Update the mod list widget errors and warnings
            self.recalculate_list_errors_warnings(list_type=list_type)

    def on_active_mods_list_updated(self, count: str) -> None:
        self.mod_list_updated(count=count, list_type="Active")

    def on_active_mods_search(self, pattern: str) -> None:
        self.signal_search_and_filters(
            list_type="Active",
            pattern=pattern,
        )

    def on_active_mods_search_clear(self) -> None:
        self.signal_clear_search(
            list_type="Active",
        )

    def on_active_mods_mode_filter_toggle(self) -> None:
        self.signal_search_mode_filter(list_type="Active")

    def on_inactive_mods_list_updated(self, count: str) -> None:
        self.mod_list_updated(count=count, list_type="Inactive")

    def on_inactive_mods_search(self, pattern: str) -> None:
        self.signal_search_and_filters(
            list_type="Inactive",
            pattern=pattern,
        )

    def on_inactive_mods_search_clear(self) -> None:
        self.signal_clear_search(
            list_type="Inactive",
        )

    def on_inactive_mods_mode_filter_toggle(self) -> None:
        self.signal_search_mode_filter(list_type="Inactive")

    def refresh_all_tag_filter_selectors(self) -> None:
        """Refresh the available tags in both filter panels from the aux DB."""
        try:
            tags = auxdb_get_all_tags(self.settings)
        except Exception as e:
            logger.debug(f"Unable to load tag filter list: {e}")
            tags = []
        self.active_filter_button.filter_panel.set_available_tags(tags)
        self.inactive_filter_button.filter_panel.set_available_tags(tags)
        self.signal_search_and_filters(
            list_type="Active",
            pattern=self.active_mods_search.text(),
        )
        self.signal_search_and_filters(
            list_type="Inactive",
            pattern=self.inactive_mods_search.text(),
        )

    def reset_all_filters_and_search(self, list_type: str) -> None:
        """Clear all filters and search text for the given list type."""
        if list_type == "Active":
            self.active_filter_button.filter_panel.clear()
        elif list_type == "Inactive":
            self.inactive_filter_button.filter_panel.clear()
        self.signal_clear_search(list_type=list_type)

    def on_mod_created(self, uuid: str) -> None:
        self.inactive_mods_list.append_new_item(uuid)

    def on_mod_deleted(self, uuid: str) -> None:
        if uuid in self.active_mods_list.paths:
            index = self.active_mods_list.paths.index(uuid)
            self.active_mods_list.takeItem(index)
            self.active_mods_list.paths.pop(index)
            self.update_count(list_type="Active")
        elif uuid in self.inactive_mods_list.paths:
            index = self.inactive_mods_list.paths.index(uuid)
            self.inactive_mods_list.takeItem(index)
            self.inactive_mods_list.paths.pop(index)
            self.update_count(list_type="Inactive")

    def on_mod_metadata_updated(self, uuid: str) -> None:
        if uuid in self.active_mods_list.paths:
            self.active_mods_list.rebuild_item_widget_from_uuid(uuid=uuid)
        elif uuid in self.inactive_mods_list.paths:
            self.inactive_mods_list.rebuild_item_widget_from_uuid(uuid=uuid)

    def recalculate_list_errors_warnings(self, list_type: str) -> None:
        """
        Update the errors/warnings summary frame with current mod list status.

        For Active mods: displays errors, warnings, and new mods count.
        For Inactive mods: only recalculates internal state (no display update).

        Args:
            list_type: "Active" or "Inactive" to specify which list to process
        """
        if list_type == "Active":
            # Ensure all visible items have their widgets properly loaded
            self.active_mods_list.check_widgets_visible()

            # Calculate internal errors and warnings for all mods in the list
            total_error_text, total_warning_text, num_errors, num_warnings = (
                self.active_mods_list.recalculate_internal_errors_warnings()
            )

            # Count new mods (not in latest save). Only if save comparison is enabled
            new_count = 0
            if self.settings.show_save_comparison_indicators:
                try:
                    for item in self.active_mods_list.get_all_mod_list_items():
                        if item.data(Qt.ItemDataRole.UserRole).__dict__.get(
                            "is_new", False
                        ):
                            new_count += 1
                except Exception:
                    pass

            padding = " "
            has_errors_warnings = (
                total_error_text or total_warning_text or num_errors or num_warnings
            )

            # Show summary frame only if there are errors, warnings, or new mods to display
            self.errors_summary_frame.setHidden(
                not (has_errors_warnings or new_count > 0)
            )

            # Update error and warning counts/tooltips (show 0 if none exist)
            self.warnings_text.setText(
                self.tr("{padding}{num} warning(s)").format(
                    padding=padding, num=num_warnings
                )
            )
            self.errors_text.setText(
                self.tr("{padding}{num} error(s)").format(
                    padding=padding, num=num_errors
                )
            )
            self.errors_icon.setToolTip(
                total_error_text.lstrip() if total_error_text else ""
            )
            self.warnings_icon.setToolTip(
                total_warning_text.lstrip() if total_warning_text else ""
            )

            # Update new mods display (icon and count)
            # Hide icon and text if no new mods, otherwise show with count
            self.new_icon.setHidden(new_count == 0)
            self.new_text.setHidden(new_count == 0)
            self.new_text.setText(
                self.tr("{padding}{count} new").format(padding=padding, count=new_count)
                if new_count > 0
                else self.tr("0 new")
            )

            # First time and refresh: the slot will evaluate false and do nothing.
            # Purpose: triggers the _do_save_animation slot in main_content_panel
            EventBus().list_updated_signal.emit()
        else:
            # For Inactive list: only update internal state, no display updates
            self.inactive_mods_list.check_widgets_visible()
            self.inactive_mods_list.recalculate_internal_errors_warnings()

    def signal_clear_search(self, list_type: str) -> None:
        search = (
            self.active_mods_search
            if list_type == "Active"
            else self.inactive_mods_search
        )
        search.clear()
        self.signal_search_and_filters(list_type=list_type, pattern="")
        search.clearFocus()

    def search_mod_notes(self, pattern: str, limit: int = 5000) -> set[str]:
        """Searches mod notes using fuzzy search, returning mod paths matching search pattern.

        Uses a two-pass approach:
        1. Fast SQL LIKE filter to reduce rows
        2. Fuzzy matching on the filtered subset
        Results are cached by pattern within the session.
        """
        pattern = pattern.strip().lower()
        if not pattern:
            return set()

        # Return cached results if available
        if pattern in self._notes_search_cache:
            return self._notes_search_cache[pattern]

        # Two-pass: first filter with SQL LIKE (fast), then fuzz-match (accurate)
        LIKE_SQL = text("""
            SELECT path, user_notes
            FROM auxiliary_metadata
            WHERE user_notes IS NOT NULL AND user_notes != ''
            LIMIT :limit;
        """)

        aux_metadata_controller = AuxMetadataController.get_or_create_cached_instance(
            self.settings.aux_db_path
        )
        with aux_metadata_controller.engine.connect() as conn:
            rows = conn.execute(LIKE_SQL, {"limit": limit}).fetchall()

        # Second pass: fuzzy match on the pre-filtered rows
        fuzz_threshold = 80 if len(pattern) > 5 else 70
        matching_paths: set[str] = set()
        for path, note in rows:
            note_lower = note.lower()
            # Fast substring check first — avoids fuzz entirely for exact/simple matches
            if pattern in note_lower:
                matching_paths.add(path)
            elif fuzz.partial_ratio(pattern, note_lower) >= fuzz_threshold:
                matching_paths.add(path)

        # Cache result for this pattern
        self._notes_search_cache[pattern] = matching_paths
        return matching_paths

    def _get_search_widgets(
        self, list_type: str
    ) -> tuple[QComboBox, bool, list[str], FilterState]:
        """Get the search QComboBox, filter state, UUIDs list, and FilterState for a list type."""
        if list_type == "Active":
            return (
                self.active_mods_search_filter,
                self.active_mods_search_filter_state,
                self.active_mods_list.paths,
                self.active_filter_button.filter_panel.filter_state,
            )
        return (
            self.inactive_mods_search_filter,
            self.inactive_mods_search_filter_state,
            self.inactive_mods_list.paths,
            self.inactive_filter_button.filter_panel.filter_state,
        )

    def _get_mod_list(self, list_type: str) -> ModListWidget:
        return (
            self.active_mods_list if list_type == "Active" else self.inactive_mods_list
        )

    def signal_search_and_filters(
        self,
        list_type: str,
        pattern: str,
    ) -> None:
        """
        Performs a search and/or applies filters based on the given parameters.

        Called anytime the search bar text changes or the filters change.
        Filter state (source, type, tags) is read directly from the FilterPanel.

        :param list_type: The type of list to search within (Active or Inactive).
        :param pattern: The pattern to search for.
        """
        # Notify controller when search bar text or any filters change
        if list_type == "Active":
            EventBus().filters_changed_in_active_modlist.emit()
        else:
            EventBus().filters_changed_in_inactive_modlist.emit()

        _filter, filter_state, uuids, fs = self._get_search_widgets(list_type)
        mod_list = self._get_mod_list(list_type)

        # Compute whether any filters are active
        pattern = pattern.strip()
        pattern_lower = pattern.lower()
        filters_active = bool(fs.has_active_filters() or pattern)

        # Resolve search filter key via dict lookup
        search_filter = self._search_filter_map.get(_filter.currentText())

        # Early exit: no search pattern and no filters — show everything
        if not filters_active:
            for idx in range(len(uuids)):
                item = mod_list.item(idx)
                if item is None:
                    continue
                item_data = item.data(Qt.ItemDataRole.UserRole)
                item_data["filtered"] = False
                item_data["hidden_by_filter"] = False
                item.setHidden(False)
                item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.direct_update_count(list_type, 0, len(uuids))
            mod_list.check_widgets_visible()
            if list_type == "Active":
                mod_list.apply_collapse_states()
            return

        num_filtered = 0
        num_unfiltered = 0
        # Pre-compute fuzzy matches only when searching notes or name+notes
        matches: set[str] = set()
        if pattern and (
            search_filter == "notes"
            or (
                search_filter == "name"
                and self.settings.include_mod_notes_in_mod_name_filter
            )
        ):
            matches = self.search_mod_notes(pattern)

        metadata_controller = self.metadata_controller
        for idx, uuid in enumerate(uuids):
            item = mod_list.item(idx)
            if item is None:
                continue
            if is_divider_uuid(uuid):
                continue
            item_data = item.data(Qt.ItemDataRole.UserRole)
            mod_obj = metadata_controller.get_mod(uuid)
            if mod_obj is None:
                continue

            # Hide invalid items if enabled in settings
            if self.settings.hide_invalid_mods_when_filtering:
                invalid = item_data["invalid"]
                if invalid:
                    item_data["filtered"] = True
                    item.setHidden(True)
                    continue

            item_filtered = item_data["filtered"]
            mod_tags = item_data["mod_tags"]

            # Search pattern filtering
            if search_filter == "version" and pattern:
                versions = (
                    sorted(mod_obj.supported_versions)
                    if mod_obj.supported_versions
                    else []
                )
                if not versions or not any(
                    pattern_lower in v.lower() for v in versions
                ):
                    item_filtered = True
            elif search_filter == "notes":
                _mod_path = str(mod_obj.mod_path) if mod_obj.mod_path else ""
                item_filtered = _mod_path not in matches
            elif search_filter == "tags":
                item_filtered = not any(
                    pattern_lower in tag.lower() for tag in mod_tags
                )
            elif (
                search_filter == "name"
                and self.settings.include_mod_notes_in_mod_name_filter
            ):
                if mod_obj.name and pattern_lower in mod_obj.name.lower():
                    item_filtered = False
                else:
                    _mod_path = str(mod_obj.mod_path) if mod_obj.mod_path else ""
                    item_filtered = _mod_path not in matches
            elif search_filter == "name":
                if not (mod_obj.name and pattern_lower in mod_obj.name.lower()):
                    item_filtered = True
            elif search_filter == "packageid" and isinstance(mod_obj, AboutXmlMod):
                if pattern_lower not in str(mod_obj.package_id).lower():
                    item_filtered = True
            elif search_filter == "authors":
                author = str(getattr(mod_obj, "author", "") or "")
                if pattern_lower not in author.lower():
                    item_filtered = True
            elif search_filter == "publishedfileid":
                pfid = str(mod_obj.published_file_id or "")
                if pattern_lower not in pfid.lower():
                    item_filtered = True
            elif search_filter == "colors":
                mod_color = item_data["mod_color"]
                if not pattern_lower or pattern_lower == "none":
                    item_filtered = mod_color is not None
                else:
                    item_filtered = not (
                        mod_color is not None
                        and pattern_lower in mod_color.name().lower()
                    )

            # Source filtering (set-based from FilterState)
            if not item_filtered and fs.sources != FilterState.ALL_SOURCES:
                data_source = MOD_TYPE_TO_FILTER_SOURCE.get(mod_obj.mod_type, "local")
                is_git = mod_obj.mod_type == ModType.GIT
                is_steamcmd = mod_obj.mod_type == ModType.STEAM_CMD
                source_match = (
                    data_source in fs.sources
                    or ("git_repo" in fs.sources and is_git)
                    or ("steamcmd" in fs.sources and is_steamcmd)
                )
                if not source_match:
                    item_filtered = True

            # Type filtering (string-based from FilterState)
            if not item_filtered and fs.mod_type != "all":
                is_csharp = mod_obj.c_sharp_mod
                if (fs.mod_type == "csharp" and not is_csharp) or (
                    fs.mod_type == "xml" and is_csharp
                ):
                    item_filtered = True

            # User tag filtering (from FilterState)
            if not item_filtered and (fs.tags or fs.include_no_tags):
                tags_set = set(mod_tags)
                if not fs.matches_tags(tags_set):
                    item_filtered = True

            # Check if the item should be filtered or hidden based on filter state
            if filter_state:
                item.setHidden(item_filtered)
                if item_filtered:
                    item_data["hidden_by_filter"] = True
                    item_filtered = False
                    num_filtered += 1
                else:
                    item_data["hidden_by_filter"] = False
                    num_unfiltered += 1
            else:
                if item_filtered and item.isHidden():
                    item.setHidden(False)
                    item_data["hidden_by_filter"] = False
                    num_unfiltered += 1

            # Update item data
            item_data["filtered"] = item_filtered
            item.setData(Qt.ItemDataRole.UserRole, item_data)

        self.direct_update_count(list_type, num_filtered, num_unfiltered)
        mod_list.check_widgets_visible()
        if list_type == "Active":
            mod_list.apply_collapse_states()

    @staticmethod
    def _update_mode_filter_button(
        button: QToolButton,
        filter_state: bool,
        icon_active: QIcon,
        icon_inactive: QIcon,
        tip_active: str,
        tip_inactive: str,
    ) -> None:
        if filter_state:
            button.setIcon(icon_active)
            button.setToolTip(tip_active)
        else:
            button.setIcon(icon_inactive)
            button.setToolTip(tip_inactive)

    def signal_search_mode_filter(self, list_type: str) -> None:
        if list_type == "Active":
            self.active_mods_search_filter_state = (
                not self.active_mods_search_filter_state
            )
            self._update_mode_filter_button(
                self.active_mods_search_mode_filter_button,
                self.active_mods_search_filter_state,
                self.mode_filter_icon,
                self.mode_nofilter_icon,
                self.mode_filter_tooltip,
                self.mode_nofilter_tooltip,
            )
            pattern = self.active_mods_search.text()
        elif list_type == "Inactive":
            self.inactive_mods_search_filter_state = (
                not self.inactive_mods_search_filter_state
            )
            self._update_mode_filter_button(
                self.inactive_mods_search_mode_filter_button,
                self.inactive_mods_search_filter_state,
                self.mode_filter_icon,
                self.mode_nofilter_icon,
                self.mode_filter_tooltip,
                self.mode_nofilter_tooltip,
            )
            pattern = self.inactive_mods_search.text()
        else:
            raise NotImplementedError(f"Unknown list type: {list_type}")

        self.signal_search_and_filters(list_type=list_type, pattern=pattern)

    def direct_update_count(
        self, list_type: str, filtered: int, unfiltered: int
    ) -> None:
        list_type_label = (
            self.tr("Active") if list_type == "Active" else self.tr("Inactive")
        )
        label = (
            self.active_mods_label
            if list_type == "Active"
            else self.inactive_mods_label
        )
        total = filtered + unfiltered
        if filtered > 0:
            label.setText(f"{list_type_label} [{unfiltered}/{total}]")
        else:
            label.setText(f"{list_type_label} [{total}]")

    def update_count(self, list_type: str) -> None:
        mod_list = (
            self.active_mods_list if list_type == "Active" else self.inactive_mods_list
        )
        search = (
            self.active_mods_search
            if list_type == "Active"
            else self.inactive_mods_search
        )
        uuids = mod_list.paths
        num_filtered = 0
        num_unfiltered = 0
        for idx in range(len(uuids)):
            if is_divider_uuid(uuids[idx]):
                continue
            item = mod_list.item(idx)
            if item is None:
                continue
            item_data = item.data(Qt.ItemDataRole.UserRole)
            item_filtered = item_data["filtered"]

            if item.isHidden() or item_filtered:
                num_filtered += 1
            else:
                num_unfiltered += 1
        list_type_label = (
            self.tr("Active") if list_type == "Active" else self.tr("Inactive")
        )
        label = (
            self.active_mods_label
            if list_type == "Active"
            else self.inactive_mods_label
        )
        total = num_filtered + num_unfiltered
        if search.text() or num_filtered > 0:
            label.setText(f"{list_type_label} [{num_unfiltered}/{total}]")
        else:
            label.setText(f"{list_type_label} [{total}]")

    def _on_toggle_translation_status(self, enabled: bool) -> None:
        """
        Toggle the visibility of translation status indicators on mod list items.

        Args:
            enabled (bool): Whether to show or hide the indicators.
        """
        logger.info(f"Toggling translation status: {enabled}")

        # Update state on list widgets
        self.active_mods_list.show_translation_status = enabled
        self.inactive_mods_list.show_translation_status = enabled

        if enabled:
            # Build translation lookup table (packageId -> bool)
            # Find which mods have translations installed
            translation_lookup = self._build_translation_lookup()
            self.active_mods_list.translation_lookup = translation_lookup
            self.inactive_mods_list.translation_lookup = translation_lookup
        else:
            self.active_mods_list.translation_lookup = set()
            self.inactive_mods_list.translation_lookup = set()

        # Update visible items
        for mod_list in [self.active_mods_list, self.inactive_mods_list]:
            for i in range(mod_list.count()):
                item = mod_list.item(i)
                widget = mod_list.itemWidget(item)
                if isinstance(widget, ModListItemInner):
                    if enabled:
                        mod_path_str = widget.path
                        meta = self.metadata_controller.get_mod(mod_path_str)
                        if meta is None:
                            continue
                        pkg_id = (
                            str(meta.package_id)
                            if isinstance(meta, AboutXmlMod)
                            else ""
                        )

                        # Official expansions/DLCs have multilingual support built-in
                        is_official_expansion = meta.mod_type == ModType.LUDEON

                        # Check if this mod itself is a translation mod
                        is_translation_mod = False
                        pfid = meta.published_file_id
                        _steam_db = self.metadata_controller.steam_db
                        _steam_db_db = _steam_db.database if _steam_db else {}
                        if pfid and _steam_db_db:
                            steam_entry = _steam_db_db.get(pfid)
                            if steam_entry:
                                tag_set = {
                                    tag_item.get("tag", "").lower()
                                    for tag_item in steam_entry.tags
                                }
                                is_translation_mod = "translation" in tag_set

                        # Mark as localized if:
                        # 1. Official expansion/DLC (has built-in multilingual support)
                        # 2. Translation mod itself
                        # 3. Has an installed translation
                        has_translation = (
                            is_official_expansion
                            or is_translation_mod
                            or (pkg_id in self.active_mods_list.translation_lookup)
                        )
                        widget.update_translation_status(has_translation)
                    else:
                        widget.hide_translation_status()

    def _build_translation_lookup(self) -> set[str]:
        """
        Identify mods that have installed translations.

        Uses the same logic as _find_and_open_translations to check Steam Workshop metadata
        for installed translation mods based on:
        1. Translation tag in steamDB
        2. Dependency relationship via publishedfileid

        Returns:
            set[str]: A set of packageIds that have at least one translation mod installed.
        """
        translated_pkg_ids: set[str] = set()

        # Check if Steam metadata is available
        steam_db = self.metadata_controller.steam_db
        steam_db_database = steam_db.database if steam_db else {}
        if not steam_db_database:
            logger.warning(
                "Steam Workshop metadata database is not loaded for translation lookup"
            )
            return translated_pkg_ids

        # Get all installed mods
        all_local_metadata = self.metadata_controller.mods_metadata

        # Build a mapping: pfid -> packageId for all installed mods
        pfid_to_packageid: dict[str, str] = {}
        for _path, meta in all_local_metadata.items():
            pfid = meta.published_file_id
            packageid = (
                str(meta.package_id).lower() if isinstance(meta, AboutXmlMod) else ""
            )
            if pfid and packageid:
                pfid_to_packageid[pfid] = packageid

        # Iterate through all installed mods to find translations
        for _path, meta in all_local_metadata.items():
            pfid = meta.published_file_id

            # Skip if this mod doesn't have a publishedfileid (local-only mod)
            if not pfid:
                continue

            # Check if this mod exists in Steam metadata
            if pfid not in steam_db_database:
                continue

            steam_entry = steam_db_database[pfid]

            # Build tag set for fast lookups
            tag_set = {tag_item.get("tag", "").lower() for tag_item in steam_entry.tags}

            # Check if this mod has "translation" tag
            if "translation" not in tag_set:
                continue

            # Check dependencies to find target mods
            # For each dependency, if it's an installed mod, mark it as having a translation
            for dep_pfid in steam_entry.dependencies.keys():
                # Check if the dependency is an installed mod
                if dep_pfid in pfid_to_packageid:
                    target_packageid = pfid_to_packageid[dep_pfid]
                    translated_pkg_ids.add(target_packageid)
                    logger.debug(
                        f"Found translation {meta.name} for mod with packageId {target_packageid}"
                    )

        return translated_pkg_ids

    def _on_auto_add_translations(self) -> None:
        """
        Automatically find and add translation mods for active mods.
        Uses Steam Workshop metadata to reliably identify translations.
        """
        logger.info("Auto-adding translation mods...")

        # Check if Steam metadata is available
        steam_db = self.metadata_controller.steam_db
        steam_db_database = steam_db.database if steam_db else {}
        if not steam_db_database:
            logger.warning(
                "Steam Workshop metadata database is not loaded for auto-add translations"
            )
            show_warning(
                self.tr("Database not available"),
                self.tr(
                    "Steam Workshop metadata database is not loaded. "
                    "Please build the database first using the Database Builder."
                ),
            )
            return

        active_uuids = [
            u for u in self.active_mods_list.paths if not is_divider_uuid(u)
        ]
        all_local_metadata = self.metadata_controller.mods_metadata

        # Build a mapping: pfid -> path for all installed mods
        pfid_to_uuid: dict[str, str] = {}
        for mod_path, meta in all_local_metadata.items():
            pfid = meta.published_file_id
            if pfid:
                pfid_to_uuid[pfid] = mod_path

        # Get active mods' publishedfileids
        active_pfids = set()
        for uuid in active_uuids:
            mod = all_local_metadata.get(uuid)
            if mod:
                pfid = mod.published_file_id
                if pfid:
                    active_pfids.add(pfid)

        mods_to_add: list[str] = []

        # Find translations for active mods
        for uuid, meta in all_local_metadata.items():
            if uuid in active_uuids:
                continue  # Already active

            pfid = meta.published_file_id

            # Skip if this mod doesn't have a publishedfileid (local-only mod)
            if not pfid:
                continue

            # Check if this mod exists in Steam metadata
            if pfid not in steam_db_database:
                continue

            steam_entry = steam_db_database[pfid]

            # Build tag set for fast lookups
            tag_set = {tag_item.get("tag", "").lower() for tag_item in steam_entry.tags}

            # Check if this mod has "translation" tag
            if "translation" not in tag_set:
                continue

            # Check if this translation targets any active mod
            targets_active_mod = False
            target_mod_name = ""
            for dep_pfid in steam_entry.dependencies.keys():
                if dep_pfid in active_pfids:
                    targets_active_mod = True
                    # Get the target mod's name for similarity check
                    target_uuid = pfid_to_uuid.get(dep_pfid)
                    if target_uuid and target_uuid in all_local_metadata:
                        target_mod_name = all_local_metadata[target_uuid].name
                    logger.debug(
                        f"Found translation {meta.name} for active mod with pfid {dep_pfid}"
                    )
                    break

            if targets_active_mod:
                # Calculate similarity score to filter out false positives
                trans_name = meta.name
                similarity = self.active_mods_list._calculate_translation_similarity(
                    target_mod_name, trans_name
                )

                SIMILARITY_THRESHOLD = 0.5
                if similarity >= SIMILARITY_THRESHOLD:
                    mods_to_add.append(uuid)
                    logger.debug(
                        f"Translation '{trans_name}' passed similarity check "
                        f"(score: {similarity:.2f}) for mod '{target_mod_name}'"
                    )
                else:
                    logger.debug(
                        f"Filtered out translation '{trans_name}' due to low similarity "
                        f"(score: {similarity:.2f}) with mod '{target_mod_name}'"
                    )

        if not mods_to_add:
            show_warning(
                self.tr("No Translations Found"),
                self.tr(
                    "No applicable translation mods were found for your active mod list."
                ),
            )
            return

        # Add found mods to active list
        count = 0
        added_uuids: list[str] = []
        for uuid in mods_to_add:
            if uuid not in self.active_mods_list.paths:
                # Need to find the item in inactive list
                if uuid in self.inactive_mods_list.paths:
                    index = self.inactive_mods_list.paths.index(uuid)
                    item = self.inactive_mods_list.takeItem(
                        index
                    )  # This removes from list widget
                    self.inactive_mods_list.paths.pop(index)

                    self.active_mods_list.addItem(item)
                    # self.active_mods_list.paths is updated via handle_rows_inserted signal

                    # Ensure item data is updated (list_type)
                    data = item.data(Qt.ItemDataRole.UserRole)
                    if data:
                        data["list_type"] = "Active"
                        item.setData(Qt.ItemDataRole.UserRole, data)

                    count += 1
                    added_uuids.append(uuid)

        if count > 0:
            logger.info(f"Added {count} translation mods.")
            show_warning(
                self.tr("Translations Added"),
                self.tr(
                    f"Successfully added {count} translation mods to the active list."
                ),
            )

            # Also update translation status indicators if enabled
            if self.active_mods_list.show_translation_status:
                self._on_toggle_translation_status(True)
        else:
            logger.info("No new translation mods added (maybe already active).")
            show_warning(
                self.tr("No New Translations"),
                self.tr("All found translation mods are already active."),
            )
