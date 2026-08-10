"""Orchestrates a single app end-to-end: pick a version, download the base
APK, verify its signature, patch it, and stage the final file.

This used to live inline in main.py as `process_app`. Pulled out so
main.py can stay focused on the top-level run (patch source pooling,
release creation/upload) and this piece is independently testable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import apkmirror, github_release_source
from .config import APKMIRROR_APPS, APPS_CONFIG, display_name, icon
from .logging_config import get_logger
from .patcher import patch_apk
from .verify import verify_apk_signature
from .versions import extract_youtube_versions, pick_latest_version

log = get_logger(__name__)


async def process_app(app_key: str, desktop: str, patches: str) -> dict | None:
    config = APPS_CONFIG[app_key]
    log.info("PROCESSING: %s", app_key.upper())

    is_apkmirror_app = app_key in APKMIRROR_APPS

    selected_version = config.get("force_version")

    if not selected_version:
        try:
            result = subprocess.run(
                ["java", "-jar", desktop, "list-versions", "-f", config["pkg"],
                 "--patches", patches, "--include-experimental"],
                capture_output=True, text=True,
            )
            output = (result.stdout or "") + (result.stderr or "")
            versions = extract_youtube_versions(output)
            if versions:
                selected_version = pick_latest_version(versions)
        except Exception as e:
            log.warning("Could not fetch version list: %s", e)

    if not selected_version:
        if not is_apkmirror_app:
            selected_version = "latest"
        else:
            latest = await apkmirror.get_latest_listing(app_key)
            if latest and latest.get("version"):
                selected_version = latest["version"]

    if not selected_version:
        raise RuntimeError("Could not determine a suitable version number.")

    if is_apkmirror_app:
        apk_path = await apkmirror.download_apk(selected_version, app_key, config.get("force_build"))
    else:
        apk_path = await github_release_source.download_apk(selected_version, app_key, config.get("force_build"))

    verify_apk_signature(apk_path, app_key)

    patched_apk = patch_apk(
        desktop, patches, apk_path,
        exclude=config.get("exclude"),
        enable=config.get("enable"),
        arch=config["arch"],
    )

    if not Path(patched_apk).exists():
        return None

    name = display_name(app_key)
    final_name = f"{name}-{selected_version}.apk"
    final_path = Path.cwd() / final_name

    shutil.copyfile(patched_apk, final_path)

    return {
        "app_name": app_key,
        "display_name": name,
        "icon": icon(app_key),
        "patch_source": config["patch_source"],
        "name": final_name,
        "path": str(final_path),
        "version": selected_version,
    }
