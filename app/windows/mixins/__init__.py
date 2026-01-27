"""Mixin package for decomposing the shared BaseModsPanel base class.

Each mixin holds a logically-grouped slice of the former 1191-line
``base_mods_panel.py`` so the ~10 subclasses and ``csv_export_utils``
have a smaller blast radius. Shared types/constants live in
``_shared`` to avoid import cycles with ``base_mods_panel``.
"""
