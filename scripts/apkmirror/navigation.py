"""Navigating to and resolving APKMirror listing/release pages."""

from __future__ import annotations

import json

from ..config import ApkMirrorSite
from ..logging_config import get_logger
from ..versions import to_apkmirror_version
from . import browser as browser_mod

log = get_logger(__name__)


async def goto(tab, url: str, wait: float = 1.2, challenge_retries: int = 3, label: str = "page") -> None:
    await browser_mod.cooldown.wait()
    await browser_mod.warm_up(tab)

    for attempt in range(challenge_retries + 1):
        await tab.get(url)
        await browser_mod.jitter_sleep(wait)

        if await browser_mod.is_challenge_page(tab):
            cooldown_len = browser_mod.cooldown.trip()

            if attempt < challenge_retries:
                log.warning(
                    "Cloudflare challenge detected (%s), cooling down %.0fs before retrying (challenge #%d this run)...",
                    label, cooldown_len, browser_mod.cooldown.hits,
                )
                await browser_mod.jitter_sleep(cooldown_len, 0)
                continue

            log.warning("Cloudflare challenge still present (%s), proceeding anyway...", label)
            await browser_mod.save_diagnostic_screenshot(tab, f"cloudflare-{label}")

        return


async def row_count(tab) -> int:
    try:
        result = await tab.evaluate("document.querySelectorAll('.variants-table .table-row').length")
        return int(result or 0)
    except Exception:
        return 0


async def is_404_page(tab) -> bool:
    try:
        content = await tab.evaluate("document.title + ' ' + (document.body.innerText || '').slice(0, 300)")
    except Exception:
        return False
    if not content:
        return False
    lowered = content.lower()
    return "404" in lowered and ("whoops" in lowered or "could not be found" in lowered or "not be found" in lowered)


async def page_exists(tab, url: str) -> bool:
    try:
        await goto(tab, url, wait=1.0, label="direct-try")
        if await is_404_page(tab):
            return False
        return (await row_count(tab)) > 0
    except Exception:
        return False


async def resolve_list_url(tab, app_config: ApkMirrorSite, version: str) -> str:
    version_slug = to_apkmirror_version(version)
    name_part = app_config.get("release_slug") or app_config["slug"]
    folder_url = f"https://www.apkmirror.com/apk/{app_config['org']}/{app_config['slug']}"

    candidates = [
        f"{folder_url}/{name_part}-{version_slug}-release/",
        f"{folder_url}/{name_part}-{version_slug}-release-0-release/",
        f"{folder_url}/{name_part}-{version_slug}-beta-0-release/",
        f"{folder_url}/{name_part}-{version_slug}-beta-1-release/",
    ]

    for candidate in candidates:
        log.info("TRY: %s", candidate)
        if await page_exists(tab, candidate):
            return candidate

    log.info("No direct match, scanning app listing page...")
    listing_url = f"{folder_url}/"

    slug_part = f"-{version_slug}-"
    js = f"""
    (() => {{
        const links = Array.from(document.querySelectorAll("a[href*='-release/']"));
        const match = links.find(a => a.getAttribute('href').includes({json.dumps(slug_part)}));
        return match ? match.href : null;
    }})()
    """

    for attempt in range(2):
        await goto(tab, listing_url, wait=1.5 + attempt, label="listing-scan")
        found_url = await tab.evaluate(js)
        if found_url:
            return found_url

    await browser_mod.save_diagnostic_screenshot(tab, f"no-match-{app_config['slug']}")
    raise RuntimeError(f"No APKMirror release page found for version {version}")
