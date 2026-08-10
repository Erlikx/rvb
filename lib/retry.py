"""Shared retry / backoff helpers.

Both `lib.github` (API calls) and `lib.apkmirror` (browser navigation) used
to implement their own ad-hoc retry-with-jitter loops. This module is the
single place that logic lives now.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Awaitable, Callable, TypeVar

from .logging_config import get_logger

log = get_logger(__name__)

T = TypeVar("T")


def jitter_ms(base_ms: int, spread_ms: int = 300) -> int:
    """Add up to `spread_ms` of random jitter to a base delay (avoids
    thundering-herd retries when several matrix jobs fail at once)."""
    return base_ms + random.randint(0, spread_ms)


async def with_retry(
    fn: Callable[[int], Awaitable[T]],
    retries: int = 5,
    base_delay_ms: int = 1000,
    label: str = "operation",
) -> T:
    """Run `fn(attempt_index)` up to `retries` times with exponential
    backoff + jitter. Re-raises the last error if every attempt fails."""
    last_err: Exception | None = None

    for i in range(retries):
        try:
            return await fn(i)
        except Exception as err:  # noqa: BLE001 - intentionally broad, we retry any failure
            last_err = err
            delay_ms = jitter_ms(base_delay_ms * (2**i))
            log.warning("Retry %d/%d for %s in %dms - %s", i + 1, retries, label, delay_ms, err)
            await asyncio.sleep(delay_ms / 1000)

    assert last_err is not None
    raise last_err


class Cooldown:
    """A simple global cooldown gate, shared across calls.

    Every time `trip()` is called the cooldown window grows exponentially
    (capped at `max_seconds`), and `wait()` will sleep out any remaining
    window before letting the caller proceed. Used to back off globally
    after Cloudflare challenges instead of hammering the same host again
    immediately.
    """

    def __init__(self, base_seconds: float = 15.0, max_seconds: float = 120.0):
        self.base_seconds = base_seconds
        self.max_seconds = max_seconds
        self.hits = 0
        self._until = 0.0

    def trip(self) -> float:
        self.hits += 1
        length = min(self.base_seconds * (2 ** (self.hits - 1)), self.max_seconds)
        self._until = time.monotonic() + length
        return length

    async def wait(self) -> None:
        now = time.monotonic()
        if now < self._until:
            remaining = self._until - now
            log.info("Global cooldown active, waiting %.0fs...", remaining)
            await asyncio.sleep(remaining)

    def reset(self) -> None:
        self.hits = 0
        self._until = 0.0
