"""Errors / warnings recalculation mixin for ModListWidget.

Holds the dependency / incompatibility / load-order / version-mismatch
analysis and the list-wide recalculation that fills each item's
errors/warnings tooltip text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from platformdirs import PlatformDirs
from PySide6.QtCore import QCoreApplication, Qt

from app.core.constants import KNOWN_MOD_REPLACEMENTS
from app.io.xml import extract_xml_package_ids, fast_rimworld_xml_save_validation
from app.models.metadata.metadata_structure import AboutXmlMod, ListedMod
from app.mods.mod_utils import is_recently_updated
from app.ui.widgets.divider import is_divider_uuid
from app.views.mixins._shared import ModListWidgetMixinBase


class ErrorsWarningsMixin(ModListWidgetMixinBase):
    """Dependency / load-order / version-mismatch analysis + recalculation."""

    def _check_missing_dependencies(
        self, mod_data: ListedMod, package_ids_set: set[str]
    ) -> tuple[set[str], set[str]]:
        """Check for missing dependencies and alternative dependencies."""
        missing_deps: set[str] = set()
        alternative_deps: set[str] = set()
        if not isinstance(mod_data, AboutXmlMod):
            return missing_deps, alternative_deps
        consider_alternatives = self.metadata_controller.settings.use_alternative_package_ids_as_satisfying_dependencies
        for dep_id, dep_mod in mod_data.overall_rules.dependencies.items():
            alt_ids: set[str] = {str(a) for a in dep_mod.alternative_package_ids}

            satisfied = str(dep_id) in package_ids_set
            if not satisfied and consider_alternatives:
                satisfied = any(alt in package_ids_set for alt in alt_ids)
            if not satisfied and self._has_replacement(
                str(mod_data.package_id), str(dep_id), package_ids_set
            ):
                satisfied = True

            if not satisfied:
                missing_deps.add(str(dep_id))
                if consider_alternatives:
                    alt_candidates = {a for a in alt_ids if a not in package_ids_set}
                    alternative_deps.update(
                        alt_candidates if alt_candidates else alt_ids
                    )
        return missing_deps, alternative_deps

    def _check_incompatibilities(
        self, mod_data: ListedMod, package_ids_set: set[str]
    ) -> tuple[set[str], set[str]]:
        """Check for conflicting incompatibilities.

        :return: (declared, reverse_only) — declared are incompatibilities this
            mod declared itself; reverse_only are ones only declared by the
            other mod.
        """
        if not isinstance(mod_data, AboutXmlMod):
            return set(), set()
        # overall_rules.incompatible_with is the merged set from all rule sources
        all_incomp = {
            str(incomp)
            for incomp in mod_data.overall_rules.incompatible_with
            if str(incomp) in package_ids_set
        }
        # about_rules.incompatible_with is what the mod itself declared
        own_declared = {
            str(incomp)
            for incomp in mod_data.about_rules.incompatible_with
            if str(incomp) in package_ids_set
        }
        declared = all_incomp & own_declared
        reverse_only = all_incomp - own_declared
        return declared, reverse_only

    def _check_load_order_violations(
        self,
        mod_data: ListedMod,
        packageid_to_path: dict[str, str],
        current_mod_index: int,
    ) -> tuple[set[str], set[str]]:
        """Check for load order violations."""
        load_before_violations: set[str] = set()
        load_after_violations: set[str] = set()
        if not isinstance(mod_data, AboutXmlMod):
            return load_before_violations, load_after_violations
        # load_before: this mod should load BEFORE the listed mods
        # violation: this mod's index >= the other mod's index
        for pid in mod_data.overall_rules.load_before:
            pid_str = str(pid)
            if pid_str in packageid_to_path:
                other_path = packageid_to_path[pid_str]
                if other_path in self.paths and current_mod_index >= self.paths.index(
                    other_path
                ):
                    load_before_violations.add(pid_str)
        # load_after: this mod should load AFTER the listed mods
        # violation: this mod's index <= the other mod's index
        for pid in mod_data.overall_rules.load_after:
            pid_str = str(pid)
            if pid_str in packageid_to_path:
                other_path = packageid_to_path[pid_str]
                if other_path in self.paths and current_mod_index <= self.paths.index(
                    other_path
                ):
                    load_after_violations.add(pid_str)
        return load_before_violations, load_after_violations

    def _check_version_mismatch(self, uuid: str) -> bool:
        """Check if mod has version mismatch."""
        return self.metadata_controller.is_version_mismatch(uuid)

    def _check_use_this_instead(self, current_item_data: dict[str, Any]) -> bool:
        """Check if use_this_instead is applicable."""
        return bool(current_item_data["alternative"])

    def _append_resolved_mod_names(
        self,
        tool_tip_text: str,
        error_keys: set[str],
        packageid_to_uuid: dict[str, str],
        all_mods_metadata: dict[str, ListedMod],
    ) -> str:
        """
        Resolve a set of package ids to display names (local metadata first,
        then SteamDB) and append one ``* <name>`` line per entry to the
        tooltip text. Returns the updated tooltip text.
        """
        for key in error_keys:
            # Try to resolve name from local metadata first, then steamdb
            resolved_path = packageid_to_uuid.get(key, "")
            resolved_mod = (
                all_mods_metadata.get(resolved_path) if resolved_path else None
            )
            name = (
                resolved_mod.name
                if resolved_mod
                else self.metadata_controller.steamdb_packageid_to_name.get(key, key)
            )
            tool_tip_text += f"\n  * {name}"
        return tool_tip_text

    def recalculate_internal_errors_warnings(self) -> tuple[str, str, int, int]:
        """
        Whenever the respective mod list has items added to it, or has
        items removed from it, or has items rearranged around within it,
        calculate the internal list errors / warnings for the mod list
        """
        logger.info(f"Recalculating {self.list_type} list errors / warnings")

        all_mods_metadata = self.metadata_controller.mods_metadata

        mod_uuids = [u for u in self.paths if not is_divider_uuid(u)]
        packageid_to_uuid: dict[str, str] = {}
        for uuid in mod_uuids:
            mod = all_mods_metadata.get(uuid)
            if isinstance(mod, AboutXmlMod):
                packageid_to_uuid[str(mod.package_id)] = uuid
        package_ids_set = set(packageid_to_uuid.keys())

        package_id_to_errors: dict[str, dict[str, None | set[str] | bool]] = {
            uuid: {
                "missing_dependencies": set() if self.list_type == "Active" else None,
                "alternative_dependencies": set()
                if self.list_type == "Active"
                else None,
                "conflicting_incompatibilities": (
                    set() if self.list_type == "Active" else None
                ),
                "reverse_incompatibilities": (
                    set() if self.list_type == "Active" else None
                ),
                "load_before_violations": set() if self.list_type == "Active" else None,
                "load_after_violations": set() if self.list_type == "Active" else None,
                "version_mismatch": True,
                "use_this_instead": set()
                if self.settings.external_use_this_instead_metadata_source != "None"
                else None,
            }
            for uuid in mod_uuids
        }

        num_warnings = 0
        total_warning_text = ""
        num_errors = 0
        total_error_text = ""

        # Load latest save package ids once for this run, only if feature enabled
        save_compare_enabled: bool = self.settings.show_save_comparison_indicators
        if save_compare_enabled:
            latest_save_ids = self._get_latest_save_package_ids()
        else:
            latest_save_ids = None

        for uuid, mod_errors in package_id_to_errors.items():
            current_mod_index = self.paths.index(uuid)
            current_item = self.item(current_mod_index)
            if current_item is None:
                continue
            current_item_data = current_item.data(Qt.ItemDataRole.UserRole)
            if getattr(current_item_data, "is_divider", False):
                continue
            current_item_data["mismatch"] = False
            current_item_data["errors"] = ""
            current_item_data["warnings"] = ""
            # Mark active as new if not present in latest save; mark inactive as in_save if present in save
            if save_compare_enabled:
                try:
                    mod_obj = all_mods_metadata.get(uuid)
                    pkg_id = (
                        str(mod_obj.package_id)
                        if isinstance(mod_obj, AboutXmlMod)
                        else ""
                    )
                    is_in_save = (
                        pkg_id in latest_save_ids
                        if latest_save_ids is not None and pkg_id
                        else False
                    )
                    if self.list_type == "Active":
                        current_item_data.__dict__["is_new"] = not is_in_save
                        current_item_data.__dict__["in_save"] = False
                    else:
                        current_item_data.__dict__["is_new"] = False
                        current_item_data.__dict__["in_save"] = is_in_save
                except Exception:
                    current_item_data.__dict__["is_new"] = False
                    current_item_data.__dict__["in_save"] = False
            else:
                current_item_data.__dict__["is_new"] = False
                current_item_data.__dict__["in_save"] = False
            # Mark as recently updated if within threshold
            ts = current_item_data["updated_timestamp"]
            current_item_data["is_recently_updated"] = (
                is_recently_updated(ts, self.settings.mod_list_updated_threshold_days)
                if ts is not None and self.settings.mod_list_updated_indicator
                else False
            )
            mod_data = all_mods_metadata.get(uuid)
            if mod_data is None:
                continue
            pkg_id_str = (
                str(mod_data.package_id) if isinstance(mod_data, AboutXmlMod) else ""
            )
            # Check mod supportedversions against currently loaded version of game
            mod_errors["version_mismatch"] = self._check_version_mismatch(uuid)
            # Set an item's validity dynamically based on the version mismatch value
            if (
                pkg_id_str not in self.ignore_warning_list
                and not current_item_data["warning_toggled"]
            ):
                current_item_data["mismatch"] = mod_errors["version_mismatch"]
            else:
                # If a mod has been moved for eg. inactive -> active. We keep ignoring the warnings.
                # This makes sure to add the mod to the ignore list of the new modlist.
                # TODO: Check if toggle_warning method can add a mod to the ignore list
                # of both ModListWidgets (Active and Inactive) at the same time. Then we can remove some of this confusing code...
                if not current_item_data["warning_toggled"]:
                    if pkg_id_str in self.ignore_warning_list:
                        self.ignore_warning_list.remove(pkg_id_str)
                elif pkg_id_str not in self.ignore_warning_list:
                    self.ignore_warning_list.append(pkg_id_str)
            # Check for "Active" mod list specific errors and warnings
            if (
                self.list_type == "Active"
                and pkg_id_str
                and pkg_id_str not in self.ignore_warning_list
            ):
                # Use helper functions
                (
                    mod_errors["missing_dependencies"],
                    mod_errors["alternative_dependencies"],
                ) = self._check_missing_dependencies(mod_data, package_ids_set)
                (
                    mod_errors["conflicting_incompatibilities"],
                    mod_errors["reverse_incompatibilities"],
                ) = self._check_incompatibilities(mod_data, package_ids_set)
                (
                    mod_errors["load_before_violations"],
                    mod_errors["load_after_violations"],
                ) = self._check_load_order_violations(
                    mod_data, packageid_to_uuid, current_mod_index
                )
            # Calculate any needed string for errors
            tool_tip_text = ""
            # Build tooltip sections, conditionally include alternatives
            tooltip_sections = [
                (
                    "missing_dependencies",
                    QCoreApplication.translate(
                        "ModListWidget", "\nMissing Dependencies:"
                    ),
                ),
                (
                    "conflicting_incompatibilities",
                    QCoreApplication.translate("ModListWidget", "\nIncompatibilities:"),
                ),
                (
                    "reverse_incompatibilities",
                    QCoreApplication.translate(
                        "ModListWidget", "\nIncompatible (per other mod's rules):"
                    ),
                ),
            ]
            if self.metadata_controller.settings.use_alternative_package_ids_as_satisfying_dependencies:
                tooltip_sections.insert(
                    1,
                    (
                        "alternative_dependencies",
                        QCoreApplication.translate(
                            "ModListWidget", "\nAlternative Dependencies:"
                        ),
                    ),
                )

            for error_type, tooltip_header in tooltip_sections:
                if mod_errors[error_type]:
                    tool_tip_text += tooltip_header
                    error_keys = mod_errors[error_type]
                    assert isinstance(error_keys, set)
                    tool_tip_text = self._append_resolved_mod_names(
                        tool_tip_text,
                        error_keys,
                        packageid_to_uuid,
                        all_mods_metadata,
                    )
            # If missing dependency and/or incompatibility, add tooltip to errors
            current_item_data["errors"] = tool_tip_text
            # Calculate any needed string for warnings
            for error_type, tooltip_header in [
                (
                    "load_before_violations",
                    QCoreApplication.translate(
                        "ModListWidget", "\nShould be Loaded After:"
                    ),
                ),
                (
                    "load_after_violations",
                    QCoreApplication.translate(
                        "ModListWidget", "\nShould be Loaded Before:"
                    ),
                ),
            ]:
                if mod_errors[error_type]:
                    tool_tip_text += tooltip_header
                    error_keys = mod_errors[error_type]
                    assert isinstance(error_keys, set)
                    tool_tip_text = self._append_resolved_mod_names(
                        tool_tip_text,
                        error_keys,
                        packageid_to_uuid,
                        all_mods_metadata,
                    )
            # Handle version mismatch behavior
            if (
                mod_errors["version_mismatch"]
                and pkg_id_str not in self.ignore_warning_list
            ):
                # Add tool tip to indicate mod and game version mismatch
                tool_tip_text += QCoreApplication.translate(
                    "ModListWidget", "\nMod and Game Version Mismatch"
                )
            # Handle "use this instead" behavior
            if (
                self._check_use_this_instead(current_item_data)
                and pkg_id_str not in self.ignore_warning_list
            ):
                mod_errors["use_this_instead"] = True
                tool_tip_text += QCoreApplication.translate(
                    "ModListWidget",
                    "\nAn alternative updated mod is recommended:\n{alternative}",
                ).format(alternative=current_item_data["alternative"])
            # Add to error summary if any missing dependencies or incompatibilities
            if self.list_type == "Active" and any(
                [
                    mod_errors[key]
                    for key in [
                        "missing_dependencies",
                        "conflicting_incompatibilities",
                        "reverse_incompatibilities",
                    ]
                ]
            ):
                num_errors += 1
                total_error_text += f"\n\n{mod_data.name}"
                total_error_text += "\n" + "=" * len(mod_data.name)
                total_error_text += tool_tip_text

            # Add to warning summary if any loadBefore or loadAfter violations, or version mismatch
            # Version mismatch is determined earlier without checking if the mod is in ignore_warning_list
            # so we have to check it again here in order to not display a faulty, empty version warning
            if (
                self.list_type == "Active"
                and pkg_id_str not in self.ignore_warning_list
                and any(
                    [
                        mod_errors[key]
                        for key in [
                            "load_before_violations",
                            "load_after_violations",
                            "version_mismatch",
                            "use_this_instead",
                        ]
                    ]
                )
            ):
                num_warnings += 1
                total_warning_text += f"\n\n{mod_data.name}"
                total_warning_text += "\n============================="
                total_warning_text += tool_tip_text
            # Add tooltip to item data and set the data back to the item
            current_item_data["errors_warnings"] = tool_tip_text.strip()
            current_item_data["warnings"] = tool_tip_text[
                len(current_item_data["errors"]) :
            ].strip()
            current_item_data["errors"] = current_item_data["errors"].strip()
            current_item.setData(Qt.ItemDataRole.UserRole, current_item_data)
        logger.info(f"Finished recalculating {self.list_type} list errors and warnings")
        return total_error_text, total_warning_text, num_errors, num_warnings

    def _get_latest_save_package_ids(self) -> set[str] | None:
        """Attempt to find the latest RimWorld save file in the configured instance and extract modIds.

        Returns a set of packageIds in the save, or None on failure. Cached per list instance.
        """
        # Respect setting: fully disable feature to avoid performance impact
        if not self.settings.show_save_comparison_indicators:
            return None
        if self._latest_save_package_ids is not None:
            return self._latest_save_package_ids

        try:
            # Config path typically points to the RimWorld config folder; Saves is sibling folder
            cfg_path = self.settings.instances[
                self.settings.current_instance
            ].config_folder
            if not cfg_path:
                return None
            saves_dir = Path(cfg_path).parent / "Saves"
            if not saves_dir.exists():
                # Try common default path
                pd = PlatformDirs(appname="RimWorld by Ludeon Studios", appauthor=False)
                candidate = Path(pd.user_data_dir).parent / "Saves"
                saves_dir = candidate if candidate.exists() else saves_dir

            if not saves_dir.exists():
                return None

            # Find latest .rws by modified time
            latest: Path | None = None
            latest_mtime = -1.0
            for p in saves_dir.glob("*.rws"):
                m = p.stat().st_mtime
                if m > latest_mtime:
                    latest_mtime = m
                    latest = p
            if latest is None:
                return None

            if fast_rimworld_xml_save_validation(str(latest)):
                ids_set = extract_xml_package_ids(str(latest))
            else:
                ids_set = set("Ludeon.RimWorld")
            # Normalize to lowercase
            self._latest_save_package_ids = {str(i).lower() for i in ids_set}
            return self._latest_save_package_ids
        except Exception:
            return None

    def _has_replacement(
        self, package_id: str, dep: str, package_ids_set: set[str]
    ) -> bool:
        # Get a list of mods that can replace this mod
        replacements = KNOWN_MOD_REPLACEMENTS.get(dep, set())
        # Return true if any of the above mods (replacements) are in the mod list
        # If no replacements exist for dep, returns false
        for replacement in replacements:
            if replacement in package_ids_set:
                logger.debug(
                    f"Missing dependency [{dep}] for [{package_id}] replaced with [{replacement}]"
                )
                return True
        return False
