"""Public entry points: download a specific version's APK, or find the
latest listed version, from APKMirror."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import APKMIRROR_SITES
from ..logging_config import get_logger
from . import browser as browser_mod
from . import navigation
from .extraction import dump_variant_rows_for_debug, extract_variant_url, version_from_href, wait_for_download

log = get_logger(__name__)


async def download_apk(version: str, app_name: str = "youtube", force_build: str | None = None) -> str:
    app_config = APKMIRROR_SITES.get(app_name)
    if not app_config:
        raise RuntimeError(f'Unknown appName "{app_name}" - not found in APKMIRROR_SITES')

    out_dir = Path(__file__).resolve().parent.parent.parent / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    browser = await browser_mod.get_browser()
    tab = browser.main_tab

    try:
        await browser_mod.enable_downloads(tab, out_dir)

        list_url = await navigation.resolve_list_url(tab, app_config, version)
        log.info("LIST: %s", list_url)

        variant_url = None
        for attempt in range(4):
            await navigation.goto(tab, list_url, wait=1.5 + attempt * 1.0, label="list-page")
            variant_url = await extract_variant_url(tab, force_build, app_name)
            if variant_url:
                break
            log.info("No matching row found on page, retrying (%d/4)...", attempt + 1)

        if not variant_url:
            await dump_variant_rows_for_debug(tab)
            await browser_mod.save_diagnostic_screenshot(tab, f"no-variant-{app_name}")
            raise RuntimeError("No matching variant found on APKMirror")
        if variant_url.startswith("/"):
            variant_url = "https://www.apkmirror.com" + variant_url

        log.info("VARIANT: %s", variant_url)

        await navigation.goto(tab, variant_url, wait=1.2, label="variant-page")

        existing_before = {f.name for f in out_dir.iterdir() if f.is_file()}

        log.info("Clicking main download button...")
        await tab.evaluate("document.querySelector('a.downloadButton')?.click()")

        downloaded = await wait_for_download(out_dir, existing_before, timeout=20)

        if not downloaded:
            log.info("Direct download did not start, waiting for confirm page...")
            await browser_mod.jitter_sleep(1.5)

            final_href = await tab.evaluate(
                "(() => { const el = document.querySelector('#download-link'); return el ? el.getAttribute('href') : null; })()"
            )

            if final_href:
                log.info("Clicking final download link...")
                await tab.evaluate("document.querySelector('#download-link')?.click()")
                downloaded = await wait_for_download(out_dir, existing_before, timeout=60)

        if not downloaded:
            current_url = await tab.evaluate("location.href")
            current_title = await tab.evaluate("document.title")
            log.error("Download did not start. Current page: %r @ %s", current_title, current_url)
            await browser_mod.save_diagnostic_screenshot(tab, f"no-download-{app_name}")
            raise RuntimeError("Download did not start / file not detected (CDP download).")

        size = downloaded.stat().st_size
        if size < 1024:
            raise RuntimeError(f"Downloaded file too small ({size} bytes)")

        log.info("DONE: %s (%.2f MB)", downloaded, size / 1024 / 1024)
        return str(downloaded)

    except Exception:
        await browser_mod.save_diagnostic_screenshot(tab, f"error-{app_name}")
        raise


async def get_latest_listing(app_name: str) -> dict | None:
    app_config = APKMIRROR_SITES.get(app_name)
    if not app_config:
        raise RuntimeError(f'Unknown appName "{app_name}" - not found in APKMIRROR_SITES')

    browser = await browser_mod.get_browser()
    tab = browser.main_tab

    try:
        listing_url = f"https://www.apkmirror.com/apk/{app_config['org']}/{app_config['slug']}/"
        log.info("LISTING: %s", listing_url)

        js = """
        (() => {
            const links = Array.from(document.querySelectorAll("a[href*='-release/']")).slice(0, 15);
            return JSON.stringify(links.map(link => {
                const row = link.closest('div, li, tr') || link.parentElement;
                const text = row ? row.innerText : link.innerText;
                return { href: link.href, text: text || '' };
            }));
        })()
        """

        candidates = []
        for attempt in range(4):
            await navigation.goto(tab, listing_url, wait=2.5 + attempt * 1.2, label="app-listing")
            raw = await tab.evaluate(js)
            try:
                candidates = json.loads(raw) if isinstance(raw, str) else (raw or [])
            except Exception as e:
                log.warning("Could not parse listing data as JSON: %s", e)
                candidates = []
            if candidates:
                break
            log.info("No link found on listing page, retrying (%d/4)...", attempt + 1)

        if not candidates:
            await browser_mod.save_diagnostic_screenshot(tab, f"no-listing-{app_name}")
            return None

        for item in candidates:
            href = item.get("href") if isinstance(item, dict) else None
            text = item.get("text", "") if isinstance(item, dict) else ""

            version = version_from_href(href)
            if not version:
                match = re.search(r"\d+(?:\.\d+)+", text)
                version = match.group(0) if match else None

            if version:
                return {"version": version, "href": href}

        await browser_mod.save_diagnostic_screenshot(tab, f"no-version-{app_name}")
        return None

    except Exception:
        await browser_mod.save_diagnostic_screenshot(tab, f"error-listing-{app_name}")
        raise
