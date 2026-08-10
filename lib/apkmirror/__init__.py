"""Re-exports so `from lib.config import X` / `from ..config import X`
keeps working after the config split into apps.py / display.py / sources.py.
"""

from __future__ import annotations

from .apps import AppPatchConfig, APPS_CONFIG, PROCESS_ORDER
from .display import DISPLAY_NAMES, ICONS, display_name, icon
from .sources import (
    ApkMirrorSite,
    APKMIRROR_APPS,
    APKMIRROR_SITES,
    GITHUB_SOURCE_TAGS,
    PATCH_SOURCES,
)

__all__ = [
    "AppPatchConfig",
    "APPS_CONFIG",
    "PROCESS_ORDER",
    "DISPLAY_NAMES",
    "ICONS",
    "display_name",
    "icon",
    "ApkMirrorSite",
    "APKMIRROR_APPS",
    "APKMIRROR_SITES",
    "GITHUB_SOURCE_TAGS",
    "PATCH_SOURCES",
]
