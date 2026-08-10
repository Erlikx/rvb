"""Rewrites the shared release's body with the final list of successfully
published apps + patch-source release notes, then deletes older releases.
Run as: `python -m scripts.finalize_release`
"""

import asyncio
import os
import re

from lib.config import APPS_CONFIG, DISPLAY_NAMES, PATCH_SOURCES, icon
from lib.github import download_latest_github_asset
from lib.logging_config import get_logger
from lib.release import delete_other_releases, get_release_by_tag, update_release_body

log = get_logger(__name__)

NAME_TO_KEY = {v: k for k, v in DISPLAY_NAMES.items()}


def _normalize(text: str) -> str:
    return re.sub(r"[ ._-]+", "", text).lower()


def match_asset(file_name: str):
    if not file_name.lower().endswith(".apk"):
        return None
    if file_name.lower().startswith("microg"):
        return None

    base = file_name[:-4]

    try:
        last_dash = base.rindex("-")
    except ValueError:
        return None

    name_part = base[:last_dash]
    version_part = base[last_dash + 1:]

    normalized_name_part = _normalize(name_part)

    for display_name, app_key in NAME_TO_KEY.items():
        if _normalize(display_name) == normalized_name_part:
            return app_key, display_name, version_part

    return None


async def main():
    release_tag = os.environ["RELEASE_TAG"]
    log.info("Fetching release: %s", release_tag)
    release = await get_release_by_tag(release_tag)
    log.info("Release id=%s", release["id"])

    assets = release.get("assets", [])
    log.info("Found %d asset(s) on the release:", len(assets))
    for asset in assets:
        log.info("  - %s", asset["name"])

    successful = []
    for asset in assets:
        matched = match_asset(asset["name"])
        if matched:
            successful.append(matched)
        else:
            log.warning("Could not match asset to a known app: %s", asset["name"])

    log.info("Matched %d app asset(s).", len(successful))

    if successful:
        body = "### Latest Patched APKs\n\n"
        for app_key, display_name, version in successful:
            body += f'* <img src="{icon(app_key)}" width="16" height="16"> **{display_name}** - `{version}`\n'

        body += "\n---\n\n"

        used_sources = sorted({APPS_CONFIG[app_key]["patch_source"] for app_key, _, _ in successful})

        for key in used_sources:
            if key not in PATCH_SOURCES:
                continue
            owner, repo, label = PATCH_SOURCES[key]
            try:
                asset = await download_latest_github_asset(
                    owner=owner, repo=repo, prerelease=True,
                    match=lambda n: n.endswith(".mpp"),
                )
                body += (
                    f"\n<details>\n<summary>{label} Release Notes ({asset['tag']})</summary>\n<br>\n\n"
                    f"{asset['body']}\n\n</details>\n"
                )
            except Exception as e:
                log.warning("Could not fetch release notes for %s: %s", label, e)

        try:
            await update_release_body(release["id"], body)
            log.info("Release body updated.")
        except Exception as e:
            log.error("Failed to update release body: %s", e)
    else:
        log.info("No published APKs matched, leaving release body as is.")

    try:
        await delete_other_releases(release["id"])
        log.info("Old releases deleted.")
    except Exception as e:
        log.error("Failed to delete old releases: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
