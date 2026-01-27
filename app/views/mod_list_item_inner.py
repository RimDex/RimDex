from datetime import datetime
from typing import Optional, cast

from loguru import logger
from PySide6.QtCore import (
    QEvent,
    QObject,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QFontMetrics,
    QIcon,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)

from app.controllers.metadata_controller import MetadataController
from app.core.generic import format_file_size
from app.models.metadata.metadata_structure import AboutXmlMod, ModType
from app.models.settings import Settings
from app.mods.aux_db_utils import auxdb_get_mod_tags
from app.sort.mod_sorting import _FOLDER_SIZE_CACHE
from app.ui.widgets.custom_list_widget_item import CustomListWidgetItem
from app.ui.widgets.custom_qlabels import ClickableQLabel
from app.views.mod_list_icons import ModListIcons


class ModListItemInner(QWidget):
    toggle_warning_signal = Signal(str, str)
    toggle_error_signal = Signal(str, str)

    def __init__(
        self,
        errors_warnings: str,
        errors: str,
        warnings: str,
        filtered: bool,
        invalid: bool,
        mismatch: bool,
        alternative: bool,
        settings: Settings,
        path: str,
        mod_color: QColor,
        metadata_controller: MetadataController | None = None,
    ) -> None:
        super(ModListItemInner, self).__init__()

        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self._selected = False
        self._hovered = False

        self.metadata_controller = metadata_controller or MetadataController.instance()

        self.errors_warnings = errors_warnings
        self.errors = errors
        self.warnings = warnings
        self.filtered = filtered
        self.invalid = invalid
        self.mismatch = mismatch
        self.alternative = alternative
        self.settings = settings
        self.show_tags = False  # Updated by repolish() after construction
        self.mod_color: QColor | None = mod_color

        self.path = path
        mod = self.metadata_controller.get_mod(self.path)
        name_value = mod.name if mod is not None else None
        if not isinstance(name_value, str):
            name_value = "name error in mod about.xml"
        self.list_item_name = name_value
        self.main_label = QLabel()
        self.mod_tags_label = QLabel()
        self.mod_tags_label.setObjectName("ListItemTagsLabel")
        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(12, 12)
        self.color_swatch.setHidden(True)

        self.setToolTip(self.get_tool_tip_text())
        self.main_item_layout = QHBoxLayout()
        self.main_item_layout.setContentsMargins(0, 0, 0, 0)
        self.main_item_layout.setSpacing(0)
        self.font_metrics = QFontMetrics(self.font())

        self.csharp_icon = None
        self.xml_icon = None
        if self.settings.mod_type_filter:
            if mod is not None and mod.c_sharp_mod:
                self.csharp_icon = QLabel()
                self.csharp_icon.setPixmap(
                    ModListIcons.csharp_icon().pixmap(QSize(20, 20))
                )
                self.csharp_icon.setToolTip(
                    self.tr("Contains custom C# assemblies (custom code)")
                )
            else:
                self.xml_icon = QLabel()
                self.xml_icon.setPixmap(ModListIcons.xml_icon().pixmap(QSize(20, 20)))
                self.xml_icon.setToolTip(
                    self.tr("Contains custom content (textures / XML)")
                )
        self.git_icon = None
        if mod is not None and mod.mod_type == ModType.GIT:
            self.git_icon = QLabel()
            self.git_icon.setPixmap(ModListIcons.git_icon().pixmap(QSize(20, 20)))
            self.git_icon.setToolTip(
                self.tr("Local mod that contains a git repository")
            )
        self.steamcmd_icon = None
        if mod is not None and mod.mod_type == ModType.STEAM_CMD:
            self.steamcmd_icon = QLabel()
            self.steamcmd_icon.setPixmap(
                ModListIcons.steamcmd_icon().pixmap(QSize(20, 20))
            )
            self.steamcmd_icon.setToolTip(
                self.tr("Local mod that can be used with SteamCMD")
            )
        self.warning_icon_label = ClickableQLabel()
        self.warning_icon_label.clicked.connect(self.__on_warning_icon_clicked)
        self.warning_icon_label.setPixmap(
            ModListIcons.warning_icon().pixmap(QSize(20, 20))
        )
        self.warning_icon_label.setHidden(True)
        self.new_icon_label = QLabel()
        self.new_icon_label.setPixmap(ModListIcons.new_icon().pixmap(QSize(20, 20)))
        self.new_icon_label.setToolTip(self.tr("Not in latest save"))
        self.new_icon_label.setHidden(True)
        self.updated_icon_label = QLabel()
        self.updated_icon_label.setPixmap(
            ModListIcons.updated_icon().pixmap(QSize(20, 20))
        )
        self.updated_icon_label.setToolTip(self.tr("Recently updated on Workshop"))
        self.updated_icon_label.setHidden(True)
        self.in_save_icon_label = QLabel()
        self.in_save_icon_label.setPixmap(
            ModListIcons.clear_icon().pixmap(QSize(20, 20))
        )
        self.in_save_icon_label.setToolTip(self.tr("In latest save"))
        self.in_save_icon_label.setHidden(True)
        self.error_icon_label = ClickableQLabel()
        self.error_icon_label.clicked.connect(self.__on_error_icon_clicked)
        self.error_icon_label.setPixmap(ModListIcons.error_icon().pixmap(QSize(20, 20)))
        self.error_icon_label.setHidden(True)
        self.translation_status_label = QLabel()
        self.translation_status_label.setHidden(True)
        self.mod_source_icon = None
        if not self.git_icon and not self.steamcmd_icon:
            self.mod_source_icon = QLabel()
            self.mod_source_icon.setPixmap(self.get_icon().pixmap(QSize(20, 20)))
            if mod is not None:
                mod_type = mod.mod_type
                if mod_type == ModType.LUDEON:
                    self.mod_source_icon.setObjectName("expansion")
                    self.mod_source_icon.setToolTip(
                        self.tr("Official RimWorld content by Ludeon Studios")
                    )
                elif mod_type == ModType.LOCAL:
                    self.mod_source_icon.setObjectName("local")
                    self.mod_source_icon.setToolTip(self.tr("Installed locally"))
                elif mod_type == ModType.GIT:
                    self.mod_source_icon.setObjectName("git_repo")
                elif mod_type == ModType.STEAM_CMD:
                    self.mod_source_icon.setObjectName("steamcmd")
                elif mod_type == ModType.STEAM_WORKSHOP:
                    self.mod_source_icon.setObjectName("workshop")
                    self.mod_source_icon.setToolTip(self.tr("Subscribed via Steam"))
        if self.mod_color is not None:
            self.main_label.setObjectName("ListItemLabelCustomColor")
            self.handle_mod_color_change(init=True)
        elif self.filtered:
            self.main_label.setObjectName("ListItemLabelFiltered")
        elif errors_warnings:
            self.main_label.setObjectName("ListItemLabelInvalid")
        else:
            self.main_label.setObjectName("ListItemLabel")
        if self.git_icon:
            self.main_item_layout.addWidget(self.git_icon, Qt.AlignmentFlag.AlignRight)
        if self.steamcmd_icon:
            self.main_item_layout.addWidget(
                self.steamcmd_icon, Qt.AlignmentFlag.AlignRight
            )
        if self.mod_source_icon:
            self.main_item_layout.addWidget(
                self.mod_source_icon, Qt.AlignmentFlag.AlignRight
            )
        if self.csharp_icon:
            self.main_item_layout.addWidget(
                self.csharp_icon, Qt.AlignmentFlag.AlignRight
            )
        if self.xml_icon:
            self.main_item_layout.addWidget(self.xml_icon, Qt.AlignmentFlag.AlignRight)
        self.main_item_layout.addWidget(self.color_swatch, Qt.AlignmentFlag.AlignCenter)
        self.main_item_layout.addWidget(self.main_label, Qt.AlignmentFlag.AlignCenter)
        self.main_item_layout.addWidget(
            self.mod_tags_label, Qt.AlignmentFlag.AlignCenter
        )
        self.update_tags_label()
        if self.settings.show_save_comparison_indicators:
            self.main_item_layout.addWidget(
                self.in_save_icon_label, Qt.AlignmentFlag.AlignRight
            )
            self.main_item_layout.addWidget(
                self.new_icon_label, Qt.AlignmentFlag.AlignRight
            )
        if self.settings.mod_list_updated_indicator:
            self.main_item_layout.addWidget(
                self.updated_icon_label, Qt.AlignmentFlag.AlignRight
            )

        self.main_item_layout.addWidget(
            self.translation_status_label, Qt.AlignmentFlag.AlignRight
        )
        self.main_item_layout.addWidget(
            self.warning_icon_label, Qt.AlignmentFlag.AlignRight
        )
        self.main_item_layout.addWidget(
            self.error_icon_label, Qt.AlignmentFlag.AlignRight
        )
        self.main_item_layout.addStretch()
        self.setLayout(self.main_item_layout)

        if self.warnings:
            self.warning_icon_label.setToolTip(self.warnings)
            self.warning_icon_label.setHidden(False)
        if self.errors:
            self.error_icon_label.setToolTip(self.errors)
            self.error_icon_label.setHidden(False)

        self._last_icon_count = self.count_icons(self)

    def __on_error_icon_clicked(self) -> None:
        mod = self.metadata_controller.get_mod(self.path)
        package_id = str(mod.package_id) if isinstance(mod, AboutXmlMod) else ""
        self.toggle_error_signal.emit(
            package_id,
            self.path,
        )

    def __on_warning_icon_clicked(self) -> None:
        mod = self.metadata_controller.get_mod(self.path)
        package_id = str(mod.package_id) if isinstance(mod, AboutXmlMod) else ""
        self.toggle_warning_signal.emit(
            package_id,
            self.path,
        )

    def _resize_text_after_icon_toggle(self, icon_count: int = -1) -> None:
        event = QResizeEvent(self.size(), self.size())
        self.resizeEvent(event, icon_count=icon_count)

    def update_translation_status(self, is_translated: bool) -> None:
        if is_translated:
            self.translation_status_label.setText("🟢")
            self.translation_status_label.setToolTip(
                self.tr(
                    "Translation available - This mod has a translation or is already localized"
                )
            )
        else:
            self.translation_status_label.setText("🔴")
            self.translation_status_label.setToolTip(
                self.tr(
                    "No translation found - This mod does not have a translation installed"
                )
            )
        self.translation_status_label.setHidden(False)
        self._resize_text_after_icon_toggle()

    def hide_translation_status(self) -> None:
        self.translation_status_label.setHidden(True)
        self._resize_text_after_icon_toggle()

    def enterEvent(self, event: QEnterEvent) -> None:
        self._hovered = True
        if self._selected:
            return
        self.setStyleSheet("")
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._hovered = False
        if self._selected:
            return
        if self.mod_color is None:
            self.setStyleSheet("")
        else:
            self.handle_mod_color_change(init=True)
        super().leaveEvent(event)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.handle_selected()

    def handle_selected(self) -> None:
        if self._selected:
            self.setStyleSheet("")
        elif not self._selected:
            if self.mod_color:
                self.handle_mod_color_change(init=True)
            else:
                self.setStyleSheet("")

    def count_icons(self, widget: QObject) -> int:
        count = 0
        if isinstance(widget, QLabel):
            try:
                if widget.isHidden():
                    return 0
            except Exception:
                pass
            pixmap = widget.pixmap()
            if pixmap and not pixmap.isNull():
                count += 1

        if isinstance(widget, QWidget):
            for child in widget.children():
                count += self.count_icons(child)

        return count

    def get_tool_tip_text(self) -> str:
        mod = self.metadata_controller.get_mod(self.path)

        name_line = f"Mod: {mod.name if mod is not None else 'Not specified'}\n"

        tags = auxdb_get_mod_tags(self.settings, self.path)
        tags_line = f"Tags: {', '.join(tags) if tags else 'None'}\n"

        color_text = (
            self.mod_color.name()
            if self.mod_color and self.mod_color.isValid()
            else "None"
        )
        color_line = f"Color: {color_text}\n"

        if isinstance(mod, AboutXmlMod) and mod.authors:
            authors_text = ", ".join(mod.authors)
        else:
            authors_text = "Not specified"
        author_line = f"Authors: {authors_text}\n"

        package_id = (
            str(mod.package_id) if isinstance(mod, AboutXmlMod) else "Not specified"
        )
        package_id_line = f"PackageID: {package_id}\n"

        mod_version = (
            mod.mod_version
            if isinstance(mod, AboutXmlMod) and mod.mod_version
            else "Not specified"
        )
        modversion_line = f"Mod Version: {mod_version}\n"

        if mod is not None and mod.supported_versions:
            supported_versions_text = ", ".join(sorted(mod.supported_versions))
        else:
            supported_versions_text = "Not specified"
        supported_versions_line = f"Supported Versions: {supported_versions_text}\n"

        mod_path_str = (
            str(mod.mod_path)
            if mod is not None and mod.mod_path is not None
            else "Not specified"
        )
        path_line = f"Path: {mod_path_str}\n"

        folder_size_line = "Folder Size: Not available\n"
        if mod is not None and mod.mod_path is not None:
            cached = _FOLDER_SIZE_CACHE.get(str(mod.mod_path))
            if cached:
                folder_size_line = f"Folder Size: {format_file_size(cached[1])}\n"

        fs_time_val = mod.internal_time_touched if mod is not None else None
        if isinstance(fs_time_val, int) and fs_time_val > 0:
            try:
                dt_fs = datetime.fromtimestamp(fs_time_val)
                formatted_time = dt_fs.strftime("%Y-%m-%d %H:%M:%S")
                last_touched_line = f"Filesystem Modified: {formatted_time}"
            except (ValueError, OSError, OverflowError):
                last_touched_line = "Filesystem Modified: Invalid timestamp"
        else:
            last_touched_line = "Filesystem Modified: Not available"

        return "".join(
            [
                name_line,
                tags_line,
                color_line,
                author_line,
                package_id_line,
                modversion_line,
                folder_size_line,
                supported_versions_line,
                path_line,
                last_touched_line,
            ]
        )

    def get_icon(self) -> QIcon:
        mod = self.metadata_controller.get_mod(self.path)
        if mod is not None:
            if mod.mod_type == ModType.LUDEON:
                return ModListIcons.ludeon_icon()
            elif mod.mod_type in (ModType.LOCAL, ModType.GIT, ModType.STEAM_CMD):
                return ModListIcons.local_icon()
            elif mod.mod_type == ModType.STEAM_WORKSHOP:
                return ModListIcons.steam_icon()
        package_id = str(mod.package_id) if isinstance(mod, AboutXmlMod) else "unknown"
        logger.error(f"No type found for ModListItemInner with package id {package_id}")
        return ModListIcons.local_icon()

    def resizeEvent(self, event: QResizeEvent, icon_count: int = -1) -> None:
        if icon_count == -1:
            icon_count = self.count_icons(self)

        icon_width = icon_count * 20
        if not self.translation_status_label.isHidden():
            icon_width += (
                self.translation_status_label.fontMetrics()
                .boundingRect(self.translation_status_label.text())
                .width()
                + 6
            )

        padding = 6 if icon_count > 2 else 0
        self.item_width = super().width()

        available_content_width = max(0, int(self.item_width - icon_width - padding))
        min_name_width = int(available_content_width * 0.45)
        max_tags_width = int(available_content_width * 0.35)

        tags_width = 0
        if (
            self.show_tags
            and not self.mod_tags_label.isHidden()
            and self.mod_tags_label.toolTip()
        ):
            tags_text = self.mod_tags_label.toolTip()
            tags_width_needed = (
                self.mod_tags_label.fontMetrics().boundingRect(tags_text).width() + 6
            )
            tags_width = min(max_tags_width, tags_width_needed)

            shortened_tags = self.mod_tags_label.fontMetrics().elidedText(
                tags_text,
                Qt.TextElideMode.ElideRight,
                tags_width,
            )
            self.mod_tags_label.setText(" " + shortened_tags)
            self.mod_tags_label.setMaximumWidth(tags_width)
        else:
            self.mod_tags_label.setText("")
            self.mod_tags_label.setMaximumWidth(0)
            tags_width = 0

        name_width = max(min_name_width, available_content_width - tags_width)
        text_width_needed = QRectF(
            self.font_metrics.boundingRect(self.list_item_name)
        ).width()

        if text_width_needed > name_width:
            shortened_text = self.font_metrics.elidedText(
                self.list_item_name,
                Qt.TextElideMode.ElideRight,
                name_width,
            )
            self.main_label.setText(str(shortened_text))
        else:
            self.main_label.setText(self.list_item_name)
        return super().resizeEvent(event)

    def repolish(self, item: CustomListWidgetItem) -> None:
        item_data = item.data(Qt.ItemDataRole.UserRole)
        error_tooltip = item_data["errors"]
        warning_tooltip = item_data["warnings"]

        self.set_tags_visible(
            bool(item_data.__dict__.get("show_tags", False)), item_data["mod_tags"]
        )
        if error_tooltip:
            self.error_icon_label.setHidden(False)
            self.error_icon_label.setToolTip(error_tooltip)
        else:
            self.error_icon_label.setHidden(True)
            self.error_icon_label.setToolTip("")
        if warning_tooltip:
            self.warning_icon_label.setHidden(False)
            self.warning_icon_label.setToolTip(warning_tooltip)
        else:
            self.warning_icon_label.setHidden(True)
            self.warning_icon_label.setToolTip("")
        is_new = bool(item_data.__dict__.get("is_new", False))
        in_save = bool(item_data.__dict__.get("in_save", False))
        list_type = cast(str | None, item_data.__dict__.get("list_type"))
        show_indicators = self.settings.show_save_comparison_indicators
        if not show_indicators:
            self.new_icon_label.setHidden(True)
            self.in_save_icon_label.setHidden(True)
        elif list_type == "Active":
            self.new_icon_label.setHidden(not is_new)
            self.in_save_icon_label.setHidden(True)
        elif list_type == "Inactive":
            self.new_icon_label.setHidden(True)
            self.in_save_icon_label.setHidden(not in_save)
        else:
            self.new_icon_label.setHidden(True)
            self.in_save_icon_label.setHidden(True)
        widget_object_name = self.main_label.objectName()
        if item_data["mod_color"] is not None:
            self.handle_mod_color_change(item)
            new_widget_object_name = "ListItemLabelCustomColor"
        elif item_data["filtered"]:
            new_widget_object_name = "ListItemLabelFiltered"
            self.handle_mod_color_reset()
        elif error_tooltip or warning_tooltip:
            new_widget_object_name = "ListItemLabelInvalid"
            self.handle_mod_color_reset()
        else:
            new_widget_object_name = "ListItemLabel"
            self.handle_mod_color_reset()
        if widget_object_name != new_widget_object_name:
            logger.debug("Repolishing: " + new_widget_object_name)
            self.main_label.setObjectName(new_widget_object_name)
            self.main_label.style().unpolish(self.main_label)
            self.main_label.style().polish(self.main_label)

        is_recently_updated = bool(item_data.__dict__.get("is_recently_updated", False))
        if self.settings.mod_list_updated_indicator:
            self.updated_icon_label.setHidden(not is_recently_updated)
        else:
            self.updated_icon_label.setHidden(True)

        new_icon_count = self.count_icons(self)
        if new_icon_count != self._last_icon_count:
            self._resize_text_after_icon_toggle(icon_count=new_icon_count)
            self._last_icon_count = new_icon_count

    def handle_mod_color_change(
        self, item: CustomListWidgetItem | None = None, init: bool = False
    ) -> None:
        new_mod_color_name: Optional[str] = None
        if init:
            if self.mod_color:
                new_mod_color_name = self.mod_color.name()
        elif item:
            item_data = item.data(Qt.ItemDataRole.UserRole)
            new_mod_color_name = item_data["mod_color"].name()
            self.mod_color = item_data["mod_color"]

        if new_mod_color_name:
            prop = (
                "background"
                if self.settings.color_background_instead_of_text_toggle
                else "color"
            )
            self.setStyleSheet(f"{prop}: {new_mod_color_name};")
            self.color_swatch.setStyleSheet(f"background: {new_mod_color_name};")
            self.color_swatch.setToolTip(f"Color: {new_mod_color_name}")
            self.color_swatch.setHidden(False)
        else:
            self.color_swatch.setHidden(True)
            self.color_swatch.setToolTip("")

    def handle_mod_color_reset(self) -> None:
        self.setStyleSheet("")
        self.mod_color = None
        self.color_swatch.setHidden(True)
        self.color_swatch.setToolTip("")

    def update_tags_label(self, tags: list[str] | None = None) -> None:
        if tags is None:
            tags = auxdb_get_mod_tags(self.settings, self.path)

        if not self.show_tags or not tags:
            self.mod_tags_label.setText("")
            self.mod_tags_label.setToolTip(", ".join(tags) if tags else "")
            self.mod_tags_label.setHidden(True)
            return

        full_tags_text = " ".join(f"[{tag}]" for tag in tags)
        self.mod_tags_label.setToolTip(full_tags_text)
        self.mod_tags_label.setHidden(False)

        self.mod_tags_label.setText(full_tags_text)

    def set_tags_visible(self, visible: bool, tags: list[str] | None = None) -> None:
        self.show_tags = visible
        self.update_tags_label(tags)
        self._resize_text_after_icon_toggle()
