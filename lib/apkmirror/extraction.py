"""Pulling structured data (variant links, versions) out of APKMirror pages,
and watching the download directory for a finished file."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path

from ..logging_config import get_logger

log = get_logger(__name__)


async def extract_variant_url(tab, force_build: str | None, app_name: str) -> str | None:
    js = f"""
    (() => {{
        const rows = document.querySelectorAll('.variants-table .table-row');
        const candidates = [null, null, null, null, null, null];
        const allowedArchs = ['universal', 'evrensel', 'noarch', 'arm64-v8a', 'arm64-v8a + armeabi-v7a', 'arm64-v8a + armeabi'];
        const forceBuild = {json.dumps(force_build)};
        const appName = {json.dumps(app_name)};

        for (const row of rows) {{
            const cells = row.querySelectorAll('.table-cell');
            if (cells.length < 4) continue;

            const link = cells[0].querySelector('a.accent_color');
            if (!link) continue;

            if (forceBuild && !cells[0].innerText.includes(forceBuild)) continue;

            const badge = cells[0].querySelector('.apkm-badge');
            const badgeText = badge ? badge.innerText.toUpperCase() : '';
            const isBundle = badgeText.includes('BUNDLE') || badgeText.includes('PAKET');

            if (appName === 'instagram' && !isBundle) continue;

            const archText = (cells[1].innerText || '').trim().toLowerCase();
            const dpiText = (cells[3].innerText || '').trim().toLowerCase();

            const isTargetArch = archText === '' || allowedArchs.some(a => archText.includes(a));
            if (!isTargetArch) continue;

            const isNodpi = dpiText === '' || dpiText.includes('nodpi');
            const isAnydpi = dpiText.includes('anydpi');

            let slot;
            if (isNodpi) slot = isBundle ? 3 : 0;
            else if (isAnydpi) slot = isBundle ? 4 : 1;
            else slot = isBundle ? 5 : 2;

            if (!candidates[slot]) candidates[slot] = link.href;
        }}

        return candidates.find(c => c) || null;
    }})()
    """
    return await tab.evaluate(js)


async def dump_variant_rows_for_debug(tab) -> None:
    js = """
    (() => {
        const rows = document.querySelectorAll('.table-row');
        const scopedRows = document.querySelectorAll('.variants-table .table-row');
        return JSON.stringify({
            rowCount: rows.length,
            scopedRowCount: scopedRows.length,
            is404: /404/.test(document.title) || /could not be found/i.test(document.body.innerText || ''),
            sample: Array.from(rows).slice(0, 20).map(row => {
                const cells = row.querySelectorAll('.table-cell');
                return {
                    cellCount: cells.length,
                    name: cells[0] ? cells[0].innerText.trim().slice(0, 60) : null,
                    arch: cells[1] ? cells[1].innerText.trim() : null,
                    dpi: cells[3] ? cells[3].innerText.trim() : null,
                };
            }),
        });
    })()
    """
    try:
        raw = await tab.evaluate(js)
        info = json.loads(raw) if isinstance(raw, str) else raw
        log.info(
            "Debug: page has %s .table-row elements (%s of them inside the real .variants-table), is404: %s",
            info.get("rowCount", "?"), info.get("scopedRowCount", "?"), info.get("is404", "?"),
        )
        for i, row in enumerate(info.get("sample", [])):
            log.info("   [%d] cells=%s name=%r arch=%r dpi=%r", i, row.get("cellCount"), row.get("name"), row.get("arch"), row.get("dpi"))
    except Exception as e:
        log.warning("Could not produce debug dump: %s", e)


def version_from_href(href: str) -> str | None:
    if not href:
        return None
    match = re.search(r"-(\d[\d]*(?:-\d+)+)-release", href)
    if not match:
        return None
    return match.group(1).replace("-", ".")


async def wait_for_download(out_dir: Path, existing: set, timeout: float = 60.0):
    deadline = time.monotonic() + timeout
    last_sizes: dict[str, int] = {}

    while time.monotonic() < deadline:
        await asyncio.sleep(1.0)
        try:
            current = {f.name: f for f in out_dir.iterdir() if f.is_file()}
        except FileNotFoundError:
            continue

        new_files = [
            f for name, f in current.items()
            if name not in existing and not name.endswith((".crdownload", ".tmp"))
        ]
        if not new_files:
            continue

        candidate = max(new_files, key=lambda f: f.stat().st_mtime)
        size = candidate.stat().st_size

        if size > 0 and last_sizes.get(candidate.name) == size:
            return candidate

        last_sizes[candidate.name] = size

    return None
