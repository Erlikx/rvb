"""Creates the shared draft release that every matrix job in patch.yml
uploads its APK to. Run as: `python -m scripts.create_release`
"""

import asyncio
import os
from datetime import datetime, timezone

from lib.logging_config import get_logger
from lib.release import ensure_release

log = get_logger(__name__)


async def main():
    date = datetime.now(timezone.utc)
    tag = f"build-{date.strftime('%Y-%m-%dT%H-%M-%S')}"
    name = f"Patched APKs - {date.day} {date.strftime('%B %Y')}"
    body = (
        "### Patched APKs\n\n"
        "Each app was patched in its own job on a separate runner/IP to avoid "
        "Cloudflare bot protection, then added to this shared release.\n"
    )

    log.info("Creating shared release: %s", tag)
    release = await ensure_release(tag, name, body)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"tag={release['tag_name']}\n")

    log.info("Release ready: %s (id=%s)", release["tag_name"], release["id"])


if __name__ == "__main__":
    asyncio.run(main())
