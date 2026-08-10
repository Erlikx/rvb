"""Shared browser session + Cloudflare challenge handling.

Cloudflare-1020 notes (this is the part that's been flaky in CI):
  1. We used to hard-code a `Chrome/122.0` user-agent string via
     `browser_args`. If the actual installed Chrome build (installed fresh
     in the workflow, so usually much newer) doesn't match that UA, every
     signal Cloudflare can read *other* than the UA header - JS
     `navigator.userAgentData`, TLS/HTTP2 fingerprint, Client Hints -
     still reports the real version. That mismatch alone is enough to
     flag a session as automated. We now let nodriver report Chrome's
     *real* UA and only steer the pieces that legitimately vary
     (language, timezone) instead of masking the browser identity.
  2. Deep-linking straight into `/apk/<org>/<slug>/<version>-release/`
     with no prior visit looks nothing like a human session, who almost
     always lands on the homepage or a search result first. `warm_up()`
     visits the homepage once per browser session before any deep link,
     to pick up normal Cloudflare clearance cookies first.
"""

from __future__ import annotations

import asyncio
import random
import time
from pathlib import Path

import nodriver as uc
from nodriver import cdp

from ..logging_config import get_logger
from ..retry import Cooldown

log = get_logger(__name__)

DIAGNOSTICS_DIR = Path(__file__).resolve().parent.parent.parent / "diagnostics"

_CHALLENGE_MARKERS = [
    "just a moment",
    "checking your browser",
    "attention required! | cloudflare",
    "verify you are human",
    "cf-browser-verification",
    "cf_chl_",
    "ddos protection by cloudflare",
]

_shared_browser = None
_downloads_ready = False
_warmed_up = False

cooldown = Cooldown(base_seconds=15.0, max_seconds=120.0)


async def jitter_sleep(base: float, spread: float = 0.6) -> None:
    await asyncio.sleep(base + random.uniform(0, spread))


async def get_browser():
    global _shared_browser

    if _shared_browser is not None:
        return _shared_browser

    retries = 6
    base_delay = 4.0
    last_err = None

    for attempt in range(retries):
        try:
            _shared_browser = await uc.start(
                headless=True,
                no_sandbox=True,
                browser_args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--lang=en-US,en",
                ],
            )
            return _shared_browser
        except Exception as e:
            last_err = e
            delay = base_delay * (attempt + 1)
            log.warning("Could not start browser (attempt %d/%d): %s - retrying in %.0fs", attempt + 1, retries, e, delay)
            await asyncio.sleep(delay)

    raise last_err


async def close_browser():
    global _shared_browser, _downloads_ready, _warmed_up
    if _shared_browser is not None:
        try:
            _shared_browser.stop()
        except Exception:
            pass
        _shared_browser = None
        _downloads_ready = False
        _warmed_up = False


async def enable_downloads(tab, out_dir: Path):
    global _downloads_ready
    if _downloads_ready:
        return
    try:
        await tab.send(cdp.browser.set_download_behavior(behavior="allow", download_path=str(out_dir)))
        _downloads_ready = True
    except Exception as e:
        log.warning("set_download_behavior failed (will still try to proceed): %s", e)


async def warm_up(tab, home_url: str = "https://www.apkmirror.com/") -> None:
    """Visit the site's homepage once per browser session before any deep
    link, so we pick up Cloudflare clearance cookies the way a real visitor
    would instead of cold-hitting an inner page."""
    global _warmed_up
    if _warmed_up:
        return

    try:
        log.info("Warming up session: %s", home_url)
        await tab.get(home_url)
        await jitter_sleep(2.0, 1.5)
        # A little organic-looking scroll helps some behavioral checks.
        await tab.evaluate("window.scrollBy(0, 400)")
        await jitter_sleep(0.5, 0.5)
        _warmed_up = True
    except Exception as e:
        log.warning("Warm-up visit failed (continuing anyway): %s", e)


async def is_challenge_page(tab) -> bool:
    try:
        content = await tab.evaluate("(document.title + ' ' + document.body.innerText.slice(0, 500)).toLowerCase()")
    except Exception:
        return False
    if not content:
        return False
    return any(marker in content for marker in _CHALLENGE_MARKERS)


async def save_diagnostic_screenshot(tab, label: str):
    try:
        DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        path = DIAGNOSTICS_DIR / f"{label}-{ts}.png"
        await tab.save_screenshot(str(path))
        log.info("Diagnostic screenshot saved: %s", path)
    except Exception as e:
        log.warning("Could not capture screenshot: %s", e)
