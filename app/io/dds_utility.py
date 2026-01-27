from pathlib import Path

from loguru import logger

from app.models.settings import Settings


class DDSUtility:
    """
    Utility class for handling DDS files in the application.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        logger.info("DDSUtility initialized.")

    def delete_dds_files_without_png(self) -> None:
        """Deletes all DDS files that do not have a corresponding PNG file.

        A DDS file is considered "orphaned" when no ``.png`` with the same base
        name exists at the same location. Paths are resolved with ``pathlib``
        (extension-only suffix swap) so a ``.dds`` token anywhere else in the
        directory tree cannot corrupt the resolved PNG path.
        """
        logger.info(
            "Running checks for deleting DDS files without corresponding PNG files..."
        )

        roots = [
            self.settings.instances[self.settings.current_instance].local_folder,
            self.settings.instances[self.settings.current_instance].workshop_folder,
        ]
        # Collapse to existing directories and de-duplicate (local == workshop
        # edge cases), dropping empty/unconfigured folders.
        search_roots: list[Path] = []
        for raw in roots:
            if not raw:
                continue
            root = Path(raw)
            if root.is_dir():
                search_roots.append(root)

        deleted_count = 0
        if not search_roots:
            logger.info("No valid mod folders configured; nothing to clean.")
            return

        # Pre-compute the set of existing PNG base names per root so the orphan
        # check is O(dds_files) instead of O(dds_files * png_files). Using a
        # per-root set also bounds deletions to files inside the scanned roots.
        png_index: dict[Path, set[str]] = {}
        for root in search_roots:
            png_index[root] = {p.stem for p in root.rglob("*.png")}

        for root in search_roots:
            for dds_path in root.rglob("*.dds"):
                if not dds_path.is_file():
                    continue
                try:
                    png_path = dds_path.with_suffix(".png")
                except ValueError:
                    # File has no suffix (e.g. a nameless ".dds" entry) — skip.
                    continue
                if png_path.stem in png_index[root]:
                    continue
                logger.warning(f"Deleting DDS file without PNG: {dds_path}")
                try:
                    dds_path.unlink()
                    deleted_count += 1
                except OSError as e:
                    logger.error(f"Failed to delete {dds_path}: {e}")

        logger.info(
            f"Deleted {deleted_count} DDS files without corresponding PNG files"
        )
