import asyncio
import os
import random
from datetime import datetime, timezone

from lib import apkmirror
from lib.config import APKMIRROR_APPS, APPS_CONFIG, PATCH_SOURCES, PROCESS_ORDER
from lib.github import download_latest_github_asset
from lib.logging_config import get_logger
from lib.orchestrator import process_app
from lib.release import ensure_release, get_release_by_tag, upload_microg_once, upload_patched_apk

log = get_logger(__name__)


async def main():
    try:
        desktop_obj = await download_latest_github_asset(
            owner="MorpheApp", repo="morphe-desktop",
            prerelease=True,
            match=lambda n: "desktop" in n and n.endswith(".jar"),
        )
        desktop = desktop_obj["name"]

        target_app = os.environ.get("TARGET_APP", "all")
        apps_to_process = PROCESS_ORDER if target_app == "all" else [target_app]

        patches_pool: dict[str, str | None] = {k: None for k in PATCH_SOURCES}
        notes: dict[str, str] = {k: "" for k in PATCH_SOURCES}
        needed: dict[str, bool] = {}

        for key, (owner, repo, label) in PATCH_SOURCES.items():
            needed[key] = any(APPS_CONFIG[k]["patch_source"] == key for k in apps_to_process)
            if needed[key]:
                asset = await download_latest_github_asset(
                    owner=owner, repo=repo, prerelease=True,
                    match=lambda n: n.endswith(".mpp"),
                )
                patches_pool[key] = asset["name"]
                notes[key] = (
                    f"\n<details>\n<summary>{label} Release Notes ({asset['tag']})</summary>\n<br>\n\n"
                    f"{asset['body']}\n\n</details>\n"
                )

        patched_apks_list = []
        failed_apps = []

        for app_key in apps_to_process:
            try:
                result = await process_app(app_key, desktop, patches_pool[APPS_CONFIG[app_key]["patch_source"]])
                if result:
                    patched_apks_list.append(result)
                else:
                    failed_apps.append(app_key)
            except Exception as err:
                log.error("%s failed, skipping: %s", app_key.upper(), err)
                failed_apps.append(app_key)

            if app_key in APKMIRROR_APPS and app_key != apps_to_process[-1]:
                log.info("Closing browser session to get a fresh session for the next app...")
                await apkmirror.close_browser()

                delay = random.uniform(6.0, 14.0)
                log.info("Waiting %.0fs before the next app (to reduce APKMirror request rate)...", delay)
                await asyncio.sleep(delay)

        if patched_apks_list:
            release_tag_env = os.environ.get("RELEASE_TAG")

            if release_tag_env:
                log.info("Using shared release (matrix job): %s", release_tag_env)
                release = await get_release_by_tag(release_tag_env)
            else:
                date = datetime.now(timezone.utc)
                tag_date_str = date.strftime("%Y-%m-%dT%H-%M-%S")
                release_tag = f"build-{tag_date_str}"
                release_name = f"Patched APKs - {date.day} {date.strftime('%B %Y')}"

                body = "### Latest Patched APKs\n\n"
                for apk in patched_apks_list:
                    body += f'* <img src="{apk["icon"]}" width="16" height="16"> **{apk["display_name"]}**\n'
                body += "\n---\n\n"

                for key in PATCH_SOURCES:
                    if needed[key] and notes[key]:
                        body += notes[key]

                log.info("Creating new release: %s", release_tag)
                release = await ensure_release(release_tag, release_name, body)

            microg_uploaded = False
            for apk in patched_apks_list:
                await upload_patched_apk(release, apk["path"])
                if not microg_uploaded and apk["app_name"] in ("youtube", "youtube-music"):
                    await upload_microg_once(release)
                    microg_uploaded = True

            log.info("All apps successfully published under one release!")

        if failed_apps:
            log.error("Failed app(s): %s", ", ".join(failed_apps))
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as err:
        log.error("Fatal error: %s", err)
        raise SystemExit(1)
    finally:
        await apkmirror.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
